"""DNP3 (Distributed Network Protocol) Implementation for SCADA Simulator."""
import struct
import time
import logging
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import IntEnum

logger = logging.getLogger(__name__)


class DNP3FunctionCode(IntEnum):
    """DNP3 link-layer function codes."""
    CONFIRM = 0x18
    TEST_FRAME = 0x14
    RESPONSE_TO_UNSOLICITED = 0x2C
    UNSOLICITED_RESPONSE = 0x66
    REQUEST = 0x65
    RESET_LINK_LAYER = 0x29


class DNP3ObjectClass(IntEnum):
    """DNP3 measurement object classes."""
    BITS = 0x00
    UNSIGNED8 = 0x01
    UNSIGNED16 = 0x02
    UNSIGNED32 = 0x03
    FLOAT32 = 0x05
    """DNP3 (Distributed Network Protocol) Implementation for SCADA Simulator."""
    import struct
    import time
    import logging
    from typing import Dict, List, Optional, Tuple
    from dataclasses import dataclass, field
    from enum import IntEnum

    logger = logging.getLogger(__name__)


    class DNP3FunctionCode(IntEnum):
        """DNP3 link-layer function codes."""
        CONFIRM = 0x18
        TEST_FRAME = 0x14
        RESPONSE_TO_UNSOLICITED = 0x2C
        UNSOLICITED_RESPONSE = 0x66
        REQUEST = 0x65
        RESET_LINK_LAYER = 0x29


    class DNP3ObjectClass(IntEnum):
        """DNP3 measurement object classes."""
        BITS = 0x00
        UNSIGNED8 = 0x01
        UNSIGNED16 = 0x02
        UNSIGNED32 = 0x03
        FLOAT32 = 0x05
        BIT_STRING_32 = 0x41


    @dataclass
    class DNP3PointSet:
        """Represents a set of DNP3 points (measurements) for an object prefix."""
        prefix_type: int  # Object type in DNP3 format
        context: bytes = b''
        data: Dict[int, any] = field(default_factory=dict)

        def add_point(self, index: int, value: any) -> None:
            self.data[index] = value

        def get_values(self, indices: List[int] = None) -> List[any]:
            indices = indices or list(self.data.keys())
            return [self.data[i] for i in indices if i in self.data]


    class DNP3Device:
        """Represents a single DNP3 device (station)."""
        def __init__(self, station_addr: int, name: str, ip_address: str = "127.0.0.1", port: int = 20000):
            self.station_addr = station_addr
            self.name = name
            self.ip_address = ip_address
            self.port = port
            self.is_connected = False
            self.objects: Dict[int, DNP3PointSet] = {}
            self.sequence_number: int = 0
            self.last_command_time: float = 0.0
            self.outstation_status = "READY"

        def add_object(self, obj_type: int, points: Dict[int, any]) -> bool:
            if obj_type in self.objects:
                logger.warning(f"Object prefix {obj_type} already exists for station {self.station_addr}")
                return False
            pset = DNP3PointSet(prefix_type=obj_type, data=points)
            self.objects[obj_type] = pset
            logger.info(f"Added object type {obj_type} with {len(points)} points to station {self.name}")
            return True

        def get_object_data(self, obj_type: int) -> Dict[int, any]:
            if obj_type in self.objects:
                return self.objects[obj_type].data
            return {}


    class DNP3Simulator:
        """Handles DNP3 protocol communication and data exchange."""
    
        @staticmethod
        def build_link_header(func_code: int, dest_addr: int, src_addr: int,
                              body_length: int) -> bytes:
            """Build a DNP3 link-layer header.
        
            Format: Flag(1) + Addr_Dest(3B BE) + Addr_Src(3B LE) + Length(1) + Func(1) = 9 bytes
            """
            header = b'\xC0'  # Start flag
            header += dest_addr.to_bytes(length=3, byteorder='big')
            header += src_addr.to_bytes(length=3, byteorder='little')
            header += struct.pack('B', body_length)
            header += struct.pack('B', func_code)
            return header

        @staticmethod
        def build_object_field(prefix_type: int, indices: List[int], 
                               values: Dict[int, float]) -> bytes:
            """Build a DNP3 object field for read requests.
        
            Index type 1 encoding: [count (1B)], [base_index (2B LE)]
            Then pairs of [index (2B LE), value (... )] follow depending on object class.
            """
            obj_type_bytes = struct.pack('B', prefix_type)  # object type byte
        
            num_items = len(indices)
            if num_items <= 254:
                count_byte = struct.pack('B', num_items - 1)  # inclusive range [base, base+count]
            elif num_items <= 65534:
                count_bytes = bytes([0xFE]) + struct.pack('<H', num_items - 1)
            else:  # extended (>65534) -- not common in practice for SCADA
                count_bytes = bytes([0xFF, 0xFF]) + struct.pack('>I', num_items)

            if num_items == 1:
                base_idx = indices[0]
                idx_data = base_idx.to_bytes(length=2, byteorder='little')
            else:
                base_idx = indices[0]
                idx_data = base_idx.to_bytes(length=2, byteorder='little')

            # Value bytes depend on object class (simplified as 64-bit float here)
            value_bytes = b''
            for i in range(num_items):
                val = values.get(indices[i], 0.0)
                value_bytes += struct.pack('<d', val)  # double precision

            return obj_type_bytes + count_bytes + idx_data + value_bytes

        def __init__(self):
            self.devices: Dict[int, DNP3Device] = {}
            self.logger = logging.getLogger(f"{__name__}.DNP3Simulator")

        def add_device(self, device: DNP3Device) -> bool:
            """Register a DNP3 outstation/device."""
            if device.station_addr in self.devices:
                self.logger.warning(f"Station {device.station_addr} already registered")
                return False
        
            self.devices[device.station_addr] = device
            self.logger.info(f"Registered DNP3 station: {device.name} (addr={device.station_addr})")
            return True

        def remove_device(self, station_addr: int) -> bool:
            """Remove a DNP3 outstation."""
            if station_addr in self.devices:
                device = self.devices.pop(station_addr)
                device.is_connected = False
                self.logger.info(f"Removed DNP3 station: {device.name}")
                return True
            return False

        def parse_read_request(self, payload: bytes) -> Optional[Tuple[int, int]]:
            """Parse DNP3 read request from master.
        
            Returns (object_prefix, object_list_bytes).
            """
            if len(payload) < 4:
                self.logger.error("DNP3 read request too short")
                return None
        
            # After link header: bytes_from_object_type | count(1or4) | index_data
            obj_type = payload[0]
            count_byte = payload[1]
        
            if count_byte == 255:  # Extended count (next 4 bytes)
                count = struct.unpack('>I', payload[2:6])[0]
                idx_data_len = count * 2  # Each index is 2 bytes
                indices = {}
                for i in range(count):
                    offset_base = 6 + i * 2
                    if offset_base + 1 < len(payload):
                        idx = struct.unpack('<H', payload[offset_base:offset_base+2])[0]
                        indices[idx] = True
            else:
                count = count_byte + 1  # type-1 range is inclusive [base, base+count]
                base_idx = payload[2] if len(payload) > 2 else 0
                indices = {base_idx + i for i in range(count)}
        
            self.logger.info(f"Read request: obj_type={obj_type}, count={count}")
            return (obj_type, list(indices))

        def process_measurement_request(self, station_addr: int, 
                                         obj_prefix: int) -> Optional[Dict[int, any]]:
            """Get measurement data for the requested object prefix."""
            if station_addr not in self.devices:
                self.logger.error(f"Station {station_addr} not found")
                return None
        
            device = self.devices[station_addr]
            return device.get_object_data(obj_prefix)

        def process_write_command(self, station_addr: int, 
                                   obj_type: int, indices_and_values: Dict[int, float]) -> bool:
            """Process a write command from master to outstation."""
            if station_addr not in self.devices:
                self.logger.error(f"Station {station_addr} not found")
                return False
        
            device = self.devices[station_addr]
            current_time = time.time()
        
            # Validate timestamp freshness (DNP3 window)
            max_window_dnp3_s = 5.0
            if abs(current_time - device.last_command_time) > max_window_dnp3_s:
                self.logger.warning(f"DNP3 command too old for station {station_addr}")
                return False
        
            # Apply write to matching objects
            applied = 0
            for obj_class in device.objects:
                if DNP3ObjectClass(obj_type).value == obj_class:
                    pset = device.objects[obj_class]
                    for idx, val in indices_and_values.items():
                        pset.add_point(idx, val)
                        applied += 1
        
            device.last_command_time = current_time
            self.logger.info(f"Wrote to {applied} DNP3 points at station {station_addr}")
        
            # Generate response
            return True

        def build_response(self, src_station: int, dest_station: int, 
                           function_code: int, body_payload: bytes) -> bytes:
            """Construct the full outbound DNP3 frame."""
            length = len(body_payload) + 1  # +1 for function code byte
        
            frame = b''
            frame += struct.pack('B', 0xC0)
        
            # Addresses (big-endian, truncated to 3 bytes each)
            frame += dest_station.to_bytes(length=3, byteorder='big')
            frame += src_station.to_bytes(length=3, byteorder='little')
        
            frame += struct.pack('B', length)
            frame += struct.pack('B', function_code)
            frame += body_payload
        
            return frame

        def send_command_to_station(self, station_addr: int, command_data: Dict[str, any]) -> bool:
            """Send a command (like Setpoint or Write) to an DNP3 outstation."""
            if station_addr not in self.devices:
                self.logger.error(f"Station {station_addr} not found for command")
                return False
        
            device = self.devices[station_addr]
            success = self.process_write_command(station_addr, **command_data)
        
            if success:
                self.logger.info(f"Command sent to DNP3 station {device.name}: {command_data}")
                device.outstation_status = "RECEIVED_COMMAND"
            
                # Reset status after simulated processing delay
                import threading
                def reset_delay():
                    time.sleep(0.5)  # Simulate outstation processing delay
                    device.outstation_status = "READY"
                threading.Thread(target=reset_delay, daemon=True).start()
        
            return success

        def get_all_stations_status(self) -> List[dict]:
            """Get status dictionary for all known DNP3 stations."""
            results = []
            for addr in self.devices:
                dev = self.devices[addr]
                objects_summary = {}
                for obj_class_id, pset in dev.objects.items():
                    objects_summary[int(obj_class_id)] = len(pset.data)
            
                status = {
                    'station_addr': addr,
                    'name': dev.name,
                    'is_connected': dev.is_connected,
                    'outstation_status': dev.outstation_status,
                    'object_count': len(dev.objects),
                    'object_details': objects_summary,
                    'last_command_time': dev.last_command_time
                }
                results.append(status)
            return results
