import math
import time
from typing import Any, Dict, List, Optional

from ..models import (
    AsyncGenerator,
    Breaker,
    Bus,
    Component,
    ConsumerLoad,
    Load,
    Meter,
    Model,
    Source,
    SystemState,
    Transformer,
)


class Simulator:
    """A basic single-line steady-state simulator.

    Components are evaluated left-to-right by their diagram x-position. This is
    intentionally simple and matches the educational model in example_model.json.
    """

    def __init__(self, model: Model):
        self.model = model
        self.state = SystemState(components={})
        self.last_simulation_time = time.time()
        self._initialize_state()

    def _initialize_state(self):
        for component in self.model.components:
            self.state.components[component.id] = self._empty_component_state(component)

    def _empty_component_state(self, component: Component) -> Dict[str, Any]:
        return {
            "id": component.id,
            "type": component.type,
            "name": component.name,
            "state": getattr(component, "state", None),
            "voltage": 0.0,
            "current": 0.0,
            "real_power": 0.0,
            "reactive_power": 0.0,
            "apparent_power": 0.0,
            "power_factor": None,
            "frequency": self.state.frequency,
            "energized": False,
        }

    def _ordered_components(self) -> List[Component]:
        return sorted(
            self.model.components,
            key=lambda component: (
                component.position.get("x", 0),
                component.position.get("y", 0),
                component.id,
            ),
        )

    def _find_component(self, component_id: str, component_type=None) -> Optional[Component]:
        for component in self.model.components:
            if component.id == component_id and (component_type is None or isinstance(component, component_type)):
                return component
        return None

    def _reset_dynamic_state(self):
        for component in self.model.components:
            self.state.components[component.id] = self._empty_component_state(component)

    def _voltage_to_kv(self, voltage_level) -> float:
        voltage_key = getattr(voltage_level, "value", voltage_level)
        voltage_map = {
            "13.8 kV": 13.8,
            "12 kV": 12.0,
            "600 V": 0.6,
            "480 V": 0.48,
            "240 V": 0.24,
        }
        return voltage_map.get(str(voltage_key), 0.0)

    def _voltage_to_volts(self, voltage_level) -> float:
        return self._voltage_to_kv(voltage_level) * 1000

    def _calculate_transformer_voltage(self, transformer: Transformer, input_voltage: float) -> float:
        """Calculate transformer output voltage in either direction."""
        if transformer.turns_ratio is not None:
            return input_voltage * transformer.turns_ratio

        primary_v = self._voltage_to_volts(transformer.primary_voltage)
        secondary_v = self._voltage_to_volts(transformer.secondary_voltage)
        if primary_v <= 0 or secondary_v <= 0:
            return 0.0

        if abs(input_voltage - secondary_v) < abs(input_voltage - primary_v):
            return input_voltage * (primary_v / secondary_v)
        return input_voltage * (secondary_v / primary_v)

    def _calculate_current(self, real_power_kw: float, voltage_v: float, power_factor: float) -> float:
        if voltage_v <= 0 or power_factor <= 0:
            return 0.0
        apparent_power_kva = real_power_kw / power_factor
        return (apparent_power_kva * 1000) / voltage_v

    def _calculate_power(self, real_power_kw: float, power_factor: float) -> tuple:
        if power_factor <= 0:
            return 0.0, 0.0, 0.0
        apparent_power_kva = real_power_kw / power_factor
        reactive_power_kvar = math.sqrt(max(apparent_power_kva**2 - real_power_kw**2, 0.0))
        return real_power_kw, reactive_power_kvar, apparent_power_kva

    def _apply_voltage_droop_control(self, source: Source, voltage: float) -> float:
        if source.voltage_db is None or source.voltage_default is None:
            return voltage

        voltage_deviation = voltage - source.voltage_default
        if abs(voltage_deviation) <= source.voltage_db:
            return source.voltage_default
        if voltage_deviation > 0:
            return source.voltage_default + source.voltage_db
        return source.voltage_default - source.voltage_db

    def _apply_frequency_droop_control(self, meter: Meter, frequency: float) -> float:
        if meter.frequency_db is None or meter.frequency_default is None:
            return frequency

        frequency_deviation = frequency - meter.frequency_default
        if abs(frequency_deviation) <= meter.frequency_db:
            return meter.frequency_default
        if frequency_deviation > 0:
            return meter.frequency_default + meter.frequency_db
        return meter.frequency_default - meter.frequency_db

    def _consumer_load_power(self, consumer_load: ConsumerLoad) -> float:
        if consumer_load.is_unexpected_draw_active:
            return consumer_load.power_rating * (consumer_load.unexpected_draw_multiplier or 1.0)
        return consumer_load.power_rating

    def _set_load_state(self, component: Component, real_power_kw: float, power_factor: float, voltage: float):
        current = self._calculate_current(real_power_kw, voltage, power_factor)
        real_power, reactive_power, apparent_power = self._calculate_power(real_power_kw, power_factor)
        state = self.state.components[component.id]
        state.update(
            {
                "voltage": voltage,
                "current": current,
                "real_power": real_power,
                "reactive_power": reactive_power,
                "apparent_power": apparent_power,
                "power_factor": power_factor,
                "frequency": self.state.frequency,
                "energized": True,
            }
        )

    def simulate_step(self) -> SystemState:
        self.last_simulation_time = time.time()
        self._reset_dynamic_state()

        source = next((component for component in self.model.components if isinstance(component, Source)), None)
        if source is None:
            self.state.timestamp = time.time()
            return self.state

        current_voltage = self._apply_voltage_droop_control(source, self._voltage_to_volts(source.voltage_rating))
        path_energized = True

        self.state.components[source.id].update(
            {
                "voltage": current_voltage,
                "frequency": self.state.frequency,
                "energized": True,
            }
        )

        for component in self._ordered_components():
            state = self.state.components[component.id]
            if isinstance(component, Source):
                continue

            if isinstance(component, Bus):
                if path_energized:
                    state.update({"voltage": current_voltage, "frequency": self.state.frequency, "energized": True})

            elif isinstance(component, Transformer):
                if path_energized:
                    current_voltage = self._calculate_transformer_voltage(component, current_voltage)
                    state.update({"voltage": current_voltage, "frequency": self.state.frequency, "energized": True})

            elif isinstance(component, Breaker):
                if path_energized:
                    state.update({"voltage": current_voltage, "frequency": self.state.frequency, "energized": True})
                if not component.state:
                    path_energized = False
                    current_voltage = 0.0

            elif isinstance(component, Load):
                if path_energized:
                    self._set_load_state(component, component.power_rating, component.power_factor, current_voltage)

            elif isinstance(component, ConsumerLoad):
                state.update(
                    {
                        "unexpected_draw_active": component.is_unexpected_draw_active,
                        "unexpected_draw_multiplier": component.unexpected_draw_multiplier,
                        "base_power": component.power_rating,
                        "actual_power": self._consumer_load_power(component),
                    }
                )
                if path_energized:
                    self._set_load_state(
                        component,
                        self._consumer_load_power(component),
                        component.power_factor,
                        current_voltage,
                    )

            elif isinstance(component, AsyncGenerator):
                state["is_operational"] = component.is_operational
                if path_energized and component.is_operational:
                    real_power = component.power_rating
                    power_factor = component.target_power_factor
                    real_power, reactive_power, apparent_power = self._calculate_power(real_power, power_factor)
                    if component.reactive_power_capability is not None:
                        reactive_power = component.reactive_power_capability
                    state.update(
                        {
                            "voltage": current_voltage,
                            "real_power": real_power,
                            "reactive_power": reactive_power,
                            "apparent_power": apparent_power,
                            "power_factor": power_factor,
                            "frequency": self.state.frequency,
                            "energized": True,
                        }
                    )

            elif isinstance(component, Meter):
                if path_energized:
                    frequency = self._apply_frequency_droop_control(component, self.state.frequency)
                    state.update({"voltage": current_voltage, "frequency": frequency, "energized": True})

        self._update_meter_readings()
        self.state.timestamp = time.time()
        return self.state

    def _update_meter_readings(self):
        ordered = self._ordered_components()
        for meter in [component for component in ordered if isinstance(component, Meter)]:
            meter_state = self.state.components[meter.id]
            if not meter_state["energized"]:
                continue

            meter_x = meter.position.get("x", 0)
            real_power = 0.0
            reactive_power = 0.0
            apparent_power = 0.0

            for component in ordered:
                component_state = self.state.components[component.id]
                component_x = component.position.get("x", 0)
                if component_x < meter_x or not component_state.get("energized"):
                    continue
                if isinstance(component, (Load, ConsumerLoad)):
                    if abs(component_state.get("voltage", 0.0) - meter_state["voltage"]) <= 1.0:
                        real_power += component_state.get("real_power", 0.0)
                        reactive_power += component_state.get("reactive_power", 0.0)
                        apparent_power += component_state.get("apparent_power", 0.0)

            meter_state["real_power"] = real_power
            meter_state["reactive_power"] = reactive_power
            meter_state["apparent_power"] = apparent_power
            meter_state["current"] = (apparent_power * 1000) / meter_state["voltage"] if meter_state["voltage"] else 0.0
            meter_state["power_factor"] = real_power / apparent_power if apparent_power else None

    def update_breaker_state(self, breaker_id: str, new_state: bool) -> bool:
        breaker = self._find_component(breaker_id, Breaker)
        if breaker is None:
            return False
        breaker.state = new_state
        self.state.components[breaker_id]["state"] = new_state
        return True

    def update_consumer_load_draw(self, consumer_load_id: str, unexpected_draw_active: bool, multiplier: float = None) -> bool:
        consumer_load = self._find_component(consumer_load_id, ConsumerLoad)
        if consumer_load is None:
            return False
        consumer_load.is_unexpected_draw_active = unexpected_draw_active
        if multiplier is not None:
            consumer_load.unexpected_draw_multiplier = multiplier
        return True

    def update_async_generator_state(self, generator_id: str, operational: bool) -> bool:
        generator = self._find_component(generator_id, AsyncGenerator)
        if generator is None:
            return False
        generator.is_operational = operational
        return True

    def get_component_state(self, component_id: str) -> Dict[str, Any]:
        return self.state.components.get(component_id, {})

    def get_system_state(self) -> SystemState:
        return self.state
