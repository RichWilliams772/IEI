"""ICCP (Inter-Control Center Communications Protocol) Implementation for SCADA Simulator."""
import struct
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)

DEFAULT_ICCP_PORT = 1603


@dataclass
class DNP3Event:
    """A single DNP3 event encapsulated in an ICCP frame."""
    priority: int
    object_prefix: int
    index_type: int
    indices_and_values: Dict[int, tuple]  # idx -> (value, type_tag)


@dataclass
class ICCPDevice:
    """A remote control centre / station reachable via ICCP."""
    device_id: int
    name: str
    ip_address: str = "127.0.0.1"
    port: int = DEFAULT_ICCP_PORT
    is_connected: bool = False


class ICCPSimulator:
    """ICCP protocol handler simulating inter-control center communications."""

    def __init__(self):
        self.devices: Dict[int, ICCPDevice] = {}
        self.logger = logging.getLogger(f"{__name__}.ICCPSimulator")

    # Configuration & status queries

    def add_device(self, device: ICCPDevice) -> bool:
        if device.device_id in self.devices:
            return False
        self.devices[device.device_id] = device
        return True

    def remove_device(self, device_id: int) -> bool:
        if device_id not in self.devices: 
            return False
        dev = self.devices.pop(device_id)
        dev.is_connected = False
        return True

    def get_all_devices_status(self) -> List[dict]:
        out = []
        for did, dev in self.devices.items():
            out.append({
                "device_id": did, 
                "name": dev.name,
                "is_connected": dev.is_connected
            })
        return out

    # ICCP framing helpers

    @staticmethod
    def _build_iccp_header(func_code: int, src_id: int, dest_id: int,
                           sequence: int) -> bytes:
        """Build the mandatory 14-octet ICCP header.
        
        Format:
          Byte 0: Function Code (4 bit) + Direction (4 bit)
          Bytes 1-3: Source ID
          Bytes 4-6: Destination ID  
          Bytes 7-13: Sequence Number (48 bits)
        """
        # Function code byte is split between function & direction
        direction_b = func_code >> 4
        fc_byte = func_code & 0x0F
        
        hdr = b''
        hdr += struct.pack('B', fc_byte)           # Function Code
        hdr += struct.pack('B', direction_b)       # Direction
        hdr += src_id.to_bytes(3, 'big')           # Source ID
        hdr += dest_id.to_bytes(3, 'big')          # Destination ID
        hdr += sequence.to_bytes(6, 'big')         # 48-bit sequence number
        
        return hdr

    @staticmethod
    def _build_iccp_body(events: List[DNP3Event]) -> bytes:
        """Pack the variable length application-body of an ICCP frame."""
        body = b""
        for ev in events:
            # Build tag from object prefix + index type  
            tag = struct.pack('<I', ev.object_prefix)[:3]  # 3-byte little-endian object prefix
            tag += struct.pack('B', ev.index_type)        # 1-byte index type
            
            # Pack event values (simplified to 4 byte float)
            vals_b = b""
            for idx, val in sorted(ev.indices_and_values.items()):
                value, _ = val  # Extract just the value part
                vals_b += struct.pack('<f', float(value))  # 32-bit little-endian float
            
            body += struct.pack('B', len(tag)) + tag  
            body += struct.pack('>H', len(vals_b)) + vals_b
        
        return body

    def build_iccp_frame(self, src_id: int, dest_id: int, func_code: int,
                         events: List[DNP3Event] = None, sequence: int = 1) -> bytes:
        """Return a fully-formed ICCP frame as bytes."""
        if events is None: 
            events = []
        
        hdr = self._build_iccp_header(func_code, src_id, dest_id, sequence)
        body = self._build_iccp_body(events)
        return hdr + body

    def parse_iccp_frame(self, raw: bytes) -> dict:
        """Return a dictionary with header fields and decoded application-body."""
        if len(raw) < 14:
            raise ValueError(f"ICC frame too short ({len(raw)} bytes); need ≥ 14")

        # Decode header 
        func_code = raw[0]
        direction = raw[1]
        src_id = int.from_bytes(raw[2:5], 'big')
        dest_id = int.from_bytes(raw[5:8], 'big')
        sequence = int.from_bytes(raw[8:14], 'big')  # 6-byte sequence (in big-endian)

        # Extract body if any
        if len(raw) <= 14:
            return {
                "func_code": func_code,
                "direction": direction,
                "src_id": src_id,
                "dest_id": dest_id,
                "sequence": sequence,
                "event_count": 0
            }

        # Decode body (simplified version for demo)
        event_list = []
        offset = 14
        while offset < len(raw):
            if offset + 2 > len(raw): 
                break
            
            tag_len = struct.unpack('B', raw[offset:offset+1])[0]
            offset += 1
            if offset + tag_len > len(raw):
                break
            
            tag = raw[offset:offset+tag_len]
            offset += tag_len
            
            if offset + 2 > len(raw):
                break
            
            val_len = int.from_bytes(raw[offset:offset+2], 'big')
            offset += 2
            
            if offset + val_len > len(raw):
                break
                
            # For demo, assume all values are floats
            vals = []
            pos = 0
            while pos < val_len:
                if offset + pos + 4 > len(raw):
                    break
                val = struct.unpack('<f', raw[offset+pos:offset+pos+4])[0]
                vals.append(val)
                pos += 4
            
            event_list.append({
                'object_prefix': int.from_bytes(tag[:3], 'little'),  
                'index_type': tag[3],
                'values': vals
            })
            
            offset += val_len
            
        return {
            "func_code": func_code,
            "direction": direction,
            "src_id": src_id,
            "dest_id": dest_id,
            "sequence": sequence,
            "events": event_list
        }

    def send_to_device(self, dev_id: int, events: List[DNP3Event], 
                       priority: int = 0) -> bool:
        """Send a batch of DNP3-events to device via ICCP."""
        if dev_id not in self.devices: 
            return False
            
        dev = self.devices[dev_id]
        
        # Apply global priority
        for ev in events: 
            ev.priority = max(ev.priority, priority)
            
        # Build & log frame (in real system, we'd send via socket)
        frame = self.build_iccp_frame(src_id=0, dest_id=dev_id,
                                        func_code=0x65,  # DNP3 Request
                                        events=events)
        
        self.logger.info(f"Sent ICCP frame → {dev.name} ({len(events)} events)")
        return True
