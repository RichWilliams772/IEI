from ..models import Meter, SystemState

class MeterService:
    @staticmethod
    def read_meter(meter: Meter, system_state: SystemState) -> dict:
        """Return the current stored readings for a meter."""
        meter_state = system_state.components.get(meter.id, {})
        return {
            "voltage": meter_state.get("voltage", 0.0),
            "current": meter_state.get("current", 0.0),
            "real_power": meter_state.get("real_power", 0.0),
            "reactive_power": meter_state.get("reactive_power", 0.0),
            "apparent_power": meter_state.get("apparent_power", 0.0),
            "power_factor": meter_state.get("power_factor"),
            "frequency": meter_state.get("frequency", system_state.frequency),
            "energized": meter_state.get("energized", False),
        }
    
    @staticmethod
    def calculate_readings(component_state: dict) -> dict:
        """Return normalized readings from a component state dict."""
        return {
            "voltage": component_state.get("voltage", 0.0),
            "current": component_state.get("current", 0.0),
            "real_power": component_state.get("real_power", 0.0),
            "reactive_power": component_state.get("reactive_power", 0.0),
            "apparent_power": component_state.get("apparent_power", 0.0),
            "power_factor": component_state.get("power_factor"),
            "frequency": component_state.get("frequency", 60.0),
            "energized": component_state.get("energized", False),
        }
