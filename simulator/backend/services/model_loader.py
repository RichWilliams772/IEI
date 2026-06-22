import json
from pathlib import Path
from typing import Dict, Any
from ..models import Model, Component, Source, Bus, Transformer, Load, Breaker, Meter, ConsumerLoad, AsyncGenerator

class ModelLoader:
    COMPONENT_TYPES = {
        'source': Source,
        'bus': Bus,
        'transformer': Transformer,
        'load': Load,
        'breaker': Breaker,
        'meter': Meter,
        'consumer_load': ConsumerLoad,
        'async_generator': AsyncGenerator,
    }

    @staticmethod
    def load_model_from_json(file_path: str) -> Model:
        """Load a model from a JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert the loaded data to our model objects
        components = []
        for comp_data in data.get('components', []):
            comp_type = comp_data.get('type')
            component_cls = ModelLoader.COMPONENT_TYPES.get(comp_type, Component)
            components.append(component_cls(**comp_data))

        return Model(
            components=components,
            sampling_rate_ms=data.get('sampling_rate_ms', 16)
        )
    
    @staticmethod
    def load_example_model() -> Model:
        """Load an example model for testing"""
        example_path = Path(__file__).resolve().parents[2] / "example_model.json"
        return ModelLoader.load_model_from_json(str(example_path))
