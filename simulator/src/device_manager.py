"""SCADA Device Configuration Management System."""
import os
import sys
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class DeviceConfig:
    """Device configuration model for SCADA system."""
    
    device_id: int
    name: str
    ip_address: str 
    protocol: str  # "modbus_tcp", "dnp3", "iccp"
    port: int = 502
    description: str = ""
    created_at: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceConfig':
        return cls(**data)


@dataclass 
class TagMapping:
    """Tag mapping configuration."""
    
    tag_id: str
    device_id: int
    address: int
    value_type: str  # "int", "float", etc.
    description: str = ""
    unit: str = ""
    is_analog: bool = True


@dataclass
class Configuration:
    """Top-level configuration data store."""
    
    devices: Dict[int, DeviceConfig] = None
    tag_mappings: List[TagMapping] = None
    
    def __init__(self):
        self.devices = {}
        self.tag_mappings = []

    def add_device(self, device: DeviceConfig) -> bool:
        if device.device_id in self.devices:
            return False
        self.devices[device.device_id] = device    
        return True

    def remove_device(self, device_id: int) -> bool:
        if device_id not in self.devices:
            return False
        del self.devices[device_id]
        return True

    def get_device(self, device_id: int) -> Optional[DeviceConfig]:
        return self.devices.get(device_id)

    def list_devices(self) -> List[DeviceConfig]:
        return list(self.devices.values())

    def add_tag_mapping(self, mapping: TagMapping) -> None:
        self.tag_mappings.append(mapping)
        
    def get_tag_mappings_for_device(self, device_id: int) -> List[TagMapping]:
        return [t for t in self.tag_mappings if t.device_id == device_id]


class DeviceManager:
    """Manages SCADA devices and configurations."""
    
    def __init__(self, data_dir: str = "~/.scada"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_file = self.data_dir / "config.json"
        self.logger = logging.getLogger(f"{__name__}.DeviceManager")
        
        # Initialize storage
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
        self.config = self._load_config()
        
    def _load_config(self) -> Configuration:
        """Load configuration from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    
                config = Configuration()
                
                # Restore devices
                for dev_data in data.get('devices', []):
                    device = DeviceConfig.from_dict(dev_data)
                    config.devices[device.device_id] = device
                
                # Restore tag mappings
                config.tag_mappings = [
                    TagMapping(**mapping) 
                    for mapping in data.get('tag_mappings', [])
                ]
                
                return config
            else:
                return Configuration()
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return Configuration()

    def _save_config(self):
        """Save configuration to file."""
        try:
            data = {
                'devices': [d.to_dict() for d in self.config.devices.values()],
                'tag_mappings': [asdict(t) for t in self.config.tag_mappings]
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def add_device(self, device: DeviceConfig) -> bool:
        """Add a new device."""
        if self.config.add_device(device):
            self._save_config()
            self.logger.info(f"Added device: {device.name}")
            return True
        return False

    def remove_device(self, device_id: int) -> bool:
        """Remove a device."""
        if self.config.remove_device(device_id):
            # Remove tag mappings for that device
            self.config.tag_mappings = [
                t for t in self.config.tag_mappings 
                if t.device_id != device_id
            ]
            self._save_config()
            self.logger.info(f"Removed device: {device_id}")
            return True
        return False

    def list_devices(self) -> List[DeviceConfig]:
        """List all devices."""
        return self.config.list_devices()

    def get_device(self, device_id: int) -> Optional[DeviceConfig]:
        """Get specific device."""
        return self.config.get_device(device_id)
        
    def add_tag_mapping(self, mapping: TagMapping) -> None:
        """Add a tag mapping."""
        self.config.add_tag_mapping(mapping)
        self._save_config()
        self.logger.info(f"Added tag mapping: {mapping.tag_id}")

    def get_tag_mappings_for_device(self, device_id: int) -> List[TagMapping]:
        """Get all tag mappings for a device."""
        return self.config.get_tag_mappings_for_device(device_id)

    def get_all_tag_mappings(self) -> List[TagMapping]:
        """Get all tag mappings."""
        return self.config.tag_mappings

    def search_devices(self, query: str) -> List[DeviceConfig]:
        """Search devices by name or IP."""
        results = []
        query = query.lower()
        for device in self.config.devices.values():
            if (query in device.name.lower() or 
                query in device.ip_address.lower()):
                results.append(device)
        return results


class SCADASimulator:
    """Main entry point - orchestrates protocols and device registry."""
    
    def __init__(self, data_dir: str = "~/.scada"):
        self.device_manager = DeviceManager(data_dir)
        self.logger = logging.getLogger(f"{__name__}.SCADASimulator")
        
        # Load protocol simulators
        from src.protocols.modbus_tcp import ModbusTCPSimulator
        from src.protocols.dnp3 import DNP3Simulator
        from src.protocols.iccp import ICCPSimulator
        
        self.modbus_sim = ModbusTCPSimulator()
        self.dnp3_sim = DNP3Simulator()  
        self.iccp_sim = ICCPSimulator()

    def create_device(self, name: str, protocol: str, ip_address: str, 
                      port: int = 502, description: str = "") -> Optional[int]:
        """Create a new device."""
        device_id = hash(name + ip_address) % (2**31 - 1)
        
        device = DeviceConfig(
            device_id=device_id,
            name=name,
            ip_address=ip_address,
            protocol=protocol,
            port=port,
            description=description,
            created_at=time.time()
        )

        if self.device_manager.add_device(device):
            self.logger.info(f"Created device: {name} ({protocol})")
            return device_id
        else:
            self.logger.error(f"Failed to create device {name}")
            return None

    def get_device_status(self, device_id: int) -> Optional[dict]:
        """Get status of single device."""
        device = self.device_manager.get_device(device_id)
        if not device:
            return None
            
        status = {
            "device": device,
            "protocol_specific": {}
        }
        
        # Get protocol-specific info
        if device.protocol == "modbus_tcp":
            dev_status = self.modbus_sim.get_device_status(device_id)
            status["protocol_specific"] = dev_status or {}
        elif device.protocol == "dnp3":
            stations = self.dnp3_sim.get_all_stations_status()
            for s in stations:
                if s['station_addr'] == device_id: 
                    status["protocol_specific"] = s
                    break
                    
        return status

    def get_all_devices_status(self) -> List[dict]:
        """Get all devices' statuses."""
        devices = self.device_manager.list_devices()
        statuses = []
        
        for dev in devices:
            status = self.get_device_status(dev.device_id)
            if status:
                statuses.append(status)
                
        return statuses

    def add_tag_mapping(self, tag_id: str, device_id: int, address: int,
                        value_type: str = "int", description: str = "", unit: str = "") -> bool:
        """Add a new tag mapping."""
        mapping = TagMapping(
            tag_id=tag_id,
            device_id=device_id,
            address=address,
            value_type=value_type,
            description=description,
            unit=unit
        )
        
        self.device_manager.add_tag_mapping(mapping)
        self.logger.info(f"Added tag mapping: {tag_id} -> {device_id}:{address}")
        return True

    def get_device_tags(self, device_id: int) -> List[TagMapping]:
        """Get all tag mappings for a device."""
        return self.device_manager.get_tag_mappings_for_device(device_id)

    def get_all_mappings(self) -> List[TagMapping]:
        """Get all tag mappings."""
        return self.device_manager.get_all_tag_mappings()

    def run_simulation(self) -> None:
        """Run the simulator in background (demo only)."""
        self.logger.info("SCADA simulator running...")
