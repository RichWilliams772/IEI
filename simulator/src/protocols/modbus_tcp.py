"""Modbus TCP/IP Protocol Implementation for SCADA Simulator."""
import struct
import socket
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import IntEnum

logger = logging.getLogger(__name__)


class FunctionCode(IntEnum):
    """Modbus TCP function codes."""
    READ_COILS = 1
    READ_DISCRETE_INPUTS = 2
    READ_HOLDING_REGISTERS = 3
    READ_INPUT_REGISTERS = 4
    WRITE_SINGLE_COIL = 5
    WRITE_SINGLE_REGISTER = 6
    READ_EXCEPTION_STATUS = 7
    WRITE_MULTIPLE_REGISTERS = 16


@dataclass
class ModbusDevice:
    """Represents a single Modbus TCP device (slave)."""
    device_id: int
    name: str
    ip_address: str
    port: int = 502
    is_connected: bool = False
    holding_registers: Dict[int, int] = field(default_factory=dict)
    coils: Dict[int, bool] = field(default_factory=dict)
    input_registers: Dict[int, int] = field(default_factory=dict)
    discrete_inputs: Dict[int, bool] = field(default_factory=dict)
    max_registers: int = 125
    response_delay_ms: float = 10.0


class ModbusTCPSimulator:
    """Simulates Modbus TCP/IP protocol stack for SCADA applications."""
    
    def __init__(self):
        self.devices: Dict[int, ModbusDevice] = {}
        self._transaction_ids: Dict[str, int] = {}
        self.logger = logging.getLogger(f"{__name__}.ModbusTCPSimulator")
    
    def add_device(self, device: ModbusDevice) -> bool:
        """Add a Modbus TCP device to the simulator."""
        if device.device_id in self.devices:
            self.logger.warning(f"Device {device.device_id} already exists, updating")
        self.devices[device.device_id] = device
        self.logger.info(f"Added Modbus TCP device: {device.name} ({device.ip_address}:{device.port})")
        return True
    
    def remove_device(self, device_id: int) -> bool:
        """Remove a Modbus TCP device from the simulator."""
        if device_id in self.devices:
            device = self.devices.pop(device_id)
            device.is_connected = False
            self.logger.info(f"Removed Modbus TCP device: {device.name}")
            return True
        return False
    
    def process_request(self, device_id: int, transaction_id: int, 
                        data: bytes) -> Optional[bytes]:
        """Process a Modbus TCP request and return response."""
        if device_id not in self.devices:
            return None
        
        try:
            # Parse request
            if len(data) < 12:  # Minimum MBAP header + function + address + quantity
                return None
            
            device = self.devices[device_id]
            
            func_code = data[7]
            start_address = struct.unpack('>H', data[8:10])[0]
            quantity = struct.unpack('>H', data[10:12])[0]
            
            # Validate parameters
            if quantity <= 0:
                return self._build_exception_response(
                    transaction_id, device_id, func_code, 3)
            
            response_data = b''
            
            # Process based on function code
            if func_code == FunctionCode.READ_HOLDING_REGISTERS.value:
                registers = []
                for addr in range(start_address, start_address + quantity):
                    value = device.holding_registers.get(addr, 0)
                    registers.extend(struct.pack('>H', value))
                
                response_data = struct.pack('B', len(registers)) + b''.join(registers)
                
            elif func_code == FunctionCode.READ_INPUT_REGISTERS.value:
                registers = []
                for addr in range(start_address, start_address + quantity):
                    value = device.input_registers.get(addr, 0)
                    registers.extend(struct.pack('>H', value))
                
                response_data = struct.pack('B', len(registers)) + b''.join(registers)
                
            elif func_code == FunctionCode.READ_COILS.value:
                coil_bits = []
                for addr in range(start_address, start_address + quantity):
                    coil_bits.append(device.coils.get(addr, False))
                
                bytes_needed = (len(coil_bits) + 7) // 8
                bytes_data = bytearray(bytes_needed)
                for i, coil in enumerate(coil_bits):
                    bytes_data[i // 8] |= (1 << (i % 8)) if coil else 0
                
                response_data = struct.pack('B', len(bytes_data)) + bytes(bytes_data)
                
            elif func_code == FunctionCode.WRITE_SINGLE_COIL.value:
                state = struct.unpack('>H', data[12:14])[0]
                device.coils[start_address] = state == 0xFF00
                
                # Echo request back as ACK
                return self._build_modbus_response(transaction_id, device_id, func_code, 
                                                   data[8:12])
                
            elif func_code == FunctionCode.WRITE_SINGLE_REGISTER.value:
                value = struct.unpack('>H', data[12:14])[0]
                device.holding_registers[start_address] = value
                
                return self._build_modbus_response(transaction_id, device_id, func_code, 
                                                   data[8:12])
                
            elif func_code == FunctionCode.WRITE_MULTIPLE_REGISTERS.value:
                byte_count = data[12]
                if len(data) < 13 + byte_count:
                    return None
                
                registers_to_write = []
                for i in range(0, byte_count, 2):
                    if i + 1 < byte_count:
                        val = struct.unpack('>H', data[13+i:13+i+2])[0]
                        registers_to_write.append(val)
                
                for addr in range(start_address, start_address + quantity):
                    idx = addr - start_address
                    if idx < len(registers_to_write):
                        device.holding_registers[addr] = registers_to_write[idx]
                
                response_data = struct.pack('>H', start_address) + struct.pack('>H', quantity)
            
            else:
                # Unsupported function code
                return self._build_exception_response(
                    transaction_id, device_id, func_code, 1)
            
            return self._build_modbus_response(transaction_id, device_id, func_code, response_data)
        
        except Exception as e:
            self.logger.error(f"Error processing Modbus request: {e}")
            return self._build_exception_response(
                transaction_id, device_id, func_code, 4)
    
    def _build_modbus_response(self, transaction_id: int, unit_code: int, 
                                func_code: int, data: bytes = b'') -> bytes:
        """Build a Modbus TCP response ADU."""
        byte_count = len(data)
        
        # Build the response bytes
        resp_bytes = struct.pack('>H', transaction_id)  # Transaction ID
        resp_bytes += struct.pack('>H', 0)  # Protocol ID (always 0 for Modbus)
        resp_bytes += struct.pack('>H', 1 + 1 + byte_count)  # Length: unit + function + data bytes
        
        # Unit Code (slave address)
        resp_bytes += struct.pack('B', unit_code)
        
        # Function code
        resp_bytes += struct.pack('B', func_code)
        
        if func_code == 3 or func_code == 4:
            # Read holding/input registers - response includes byte count and data
            resp_bytes += struct.pack('B', byte_count)
            resp_bytes += data
        elif func_code == 1 or func_code == 2:  
            # Read coils/discrete inputs - response includes byte count and bit data
            resp_bytes += struct.pack('B', byte_count)
            resp_bytes += data
        else:
            # Write functions - echo back the request as confirmation
            pass
        
        return resp_bytes
    
    def _build_exception_response(self, transaction_id: int, unit_code: int, 
                                   func_code: int, exception_code: int) -> bytes:
        """Build a Modbus exception response."""
        exc_resp = struct.pack('>H', transaction_id)
        exc_resp += struct.pack('>H', 0)  # Protocol ID
        exc_resp += struct.pack('>H', 3)  # Length (unit + function + exception)
        exc_resp += struct.pack('B', unit_code)
        exc_resp += struct.pack('B', func_code | 0x80)  # Set MSB to indicate exception
        exc_resp += struct.pack('B', exception_code)
        return exc_resp
    
    def get_device_status(self, device_id: int) -> Optional[dict]:
        """Get status information for a Modbus TCP device."""
        if device_id not in self.devices:
            return None
        
        device = self.devices[device_id]
        return {
            'device_id': device.device_id,
            'name': device.name,
            'ip_address': device.ip_address,
            'port': device.port,
            'is_connected': device.is_connected,
            'holding_registers_count': len(device.holding_registers),
            'coils_count': len(device.coils),
            'input_registers_count': len(device.input_registers)
        }
    
    def get_all_devices_status(self) -> List[dict]:
        """Get status for all connected devices."""
        return [self.get_device_status(did) for did in self.devices.keys()]
