from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class ComponentType(str, Enum):
    SOURCE = "source"
    BUS = "bus"
    TRANSFORMER = "transformer"
    LOAD = "load"
    BREAKER = "breaker"
    METER = "meter"
    CONSUMER_LOAD = "consumer_load"
    ASYNC_GENERATOR = "async_generator"

class VoltageLevel(str, Enum):
    KV_138 = "13.8 kV"
    KV_480 = "480 V"
    KV_240 = "240 V"
    KV_600 = "600 V"
    KV_12 = "12 kV"

class Component(BaseModel):
    id: str
    type: ComponentType
    name: str
    position: Dict[str, int]
    # Common attributes for all components
    voltage_rating: Optional[VoltageLevel] = None
    power_rating: Optional[float] = None  # in kW or kVA
    
class Source(Component):
    type: ComponentType = ComponentType.SOURCE
    voltage_rating: VoltageLevel = VoltageLevel.KV_138
    # Droop control parameters for voltage
    voltage_db: Optional[float] = None  # Deadband for voltage
    voltage_upper_limit: Optional[float] = None  # Upper voltage limit
    voltage_lower_limit: Optional[float] = None  # Lower voltage limit
    voltage_default: Optional[float] = None  # Default voltage
    
class Bus(Component):
    type: ComponentType = ComponentType.BUS
    voltage_rating: VoltageLevel = VoltageLevel.KV_138

class Transformer(Component):
    type: ComponentType = ComponentType.TRANSFORMER
    primary_voltage: VoltageLevel
    secondary_voltage: VoltageLevel
    turns_ratio: Optional[float] = None  # If not provided, calculated from voltage ratings
    
class Load(Component):
    type: ComponentType = ComponentType.LOAD
    power_rating: float  # in kW
    power_factor: float  # between 0 and 1
    voltage_rating: VoltageLevel = VoltageLevel.KV_480

class ConsumerLoad(Component):
    type: ComponentType = ComponentType.CONSUMER_LOAD
    power_rating: float  # in kW
    power_factor: float  # between 0 and 1
    voltage_rating: VoltageLevel = VoltageLevel.KV_480
    # Configuration for unexpected power draw
    expected_power: Optional[float] = None  # Expected power rating
    unexpected_draw_multiplier: Optional[float] = 1.0  # Multiplier for unexpected draw (e.g., 1.5 for 50% increase)
    is_unexpected_draw_active: bool = False  # Flag to indicate if unexpected draw is active

class AsyncGenerator(Component):
    type: ComponentType = ComponentType.ASYNC_GENERATOR
    power_rating: float  # in kW
    voltage_rating: VoltageLevel = VoltageLevel.KV_480
    # Generator parameters
    speed_rpm: Optional[float] = 1800  # Standard synchronous speed for 60Hz
    poles: int = 4  # Number of poles
    excitation_voltage: Optional[float] = None  # Excitation voltage
    reactive_power_support: bool = True  # Whether it can provide reactive power support
    is_operational: bool = False  # Whether the generator is ready to turn on
    # Power factor control parameters
    target_power_factor: float = 0.95  # Target power factor (leading or lagging)
    reactive_power_capability: Optional[float] = None  # Maximum reactive power capability in kVAR

class Breaker(Component):
    type: ComponentType = ComponentType.BREAKER
    state: bool = True  # True = closed, False = open
    
class Meter(Component):
    type: ComponentType = ComponentType.METER
    voltage_rating: VoltageLevel = VoltageLevel.KV_138
    # Droop control parameters for frequency
    frequency_db: Optional[float] = None  # Deadband for frequency
    frequency_upper_limit: Optional[float] = None  # Upper frequency limit
    frequency_lower_limit: Optional[float] = None  # Lower frequency limit
    frequency_default: Optional[float] = None  # Default frequency

ComponentUnion = Union[
    Source,
    Bus,
    Transformer,
    Load,
    Breaker,
    Meter,
    ConsumerLoad,
    AsyncGenerator,
    Component,
]

class Model(BaseModel):
    components: List[ComponentUnion]
    # Sampling rate configuration
    sampling_rate_ms: Optional[int] = 16  # Minimum sampling rate in milliseconds
    
class SystemState(BaseModel):
    components: Dict[str, Any]  # Store component states
    frequency: float = 60.0  # in Hz
    timestamp: Optional[float] = None  # Unix timestamp for state

class BreakerAction(BaseModel):
    breaker_id: str
    action: str  # "open" or "close"
