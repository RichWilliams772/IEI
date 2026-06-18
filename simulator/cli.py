#!/usr/bin/env python3
"""SCADA Simulator CLI Interface."""
import sys
import argparse
import json
import logging
from pathlib import Path


# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_parser():
    """Create argument parser for the CLI."""
    parser = argparse.ArgumentParser(description="SCADA Simulator Command Line Interface")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Device management
    device_parser = subparsers.add_parser('device', help='Manage devices')
    device_subparsers = device_parser.add_subparsers(dest='device_cmd', help='Device commands')

    add_device = device_subparsers.add_parser('add', help='Add a new device')
    add_device.add_argument('--name', required=True, help='Device name')
    add_device.add_argument('--protocol', required=True, choices=['modbus_tcp', 'dnp3', 'iccp'], 
                           help='Protocol type')
    add_device.add_argument('--ip', required=True, help='Device IP address')
    add_device.add_argument('--port', default=502, type=int, help='Device port (default: 502)')
    add_device.add_argument('--description', default='', help='Device description')

    list_devices = device_subparsers.add_parser('list', help='List all devices')
    
    remove_device = device_subparsers.add_parser('remove', help='Remove a device')
    remove_device.add_argument('--id', required=True, type=int, help='Device ID to remove')

    # Tag management  
    tag_parser = subparsers.add_parser('tag', help='Manage tags')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_cmd', help='Tag commands')

    add_tag = tag_subparsers.add_parser('add', help='Add a new tag mapping')
    add_tag.add_argument('--id', required=True, help='Tag ID')
    add_tag.add_argument('--device-id', required=True, type=int, help='Device ID')
    add_tag.add_argument('--address', required=True, type=int, help='Address')
    add_tag.add_argument('--type', default='int', help='Value type (default: int)')
    add_tag.add_argument('--description', default='', help='Tag description')
    add_tag.add_argument('--unit', default='', help='Unit of measurement')

    list_tags = tag_subparsers.add_parser('list', help='List all tags')
    
    # Simulation control
    sim_parser = subparsers.add_parser('simulate', help='Start simulation')
    sim_parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')

    return parser


def main():
    """Main CLI entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return
        
    try:
        # Import the core simulator here to avoid circular imports
        from src.device_manager import SCADASimulator
        
        simulator = SCADASimulator()
        
        if args.command == 'device':
            if args.device_cmd == 'add':
                device_id = simulator.create_device(
                    name=args.name,
                    protocol=args.protocol,
                    ip_address=args.ip,
                    port=args.port,
                    description=args.description
                )
                if device_id is not None:
                    logger.info(f"Device added with ID: {device_id}")
                else:
                    logger.error("Failed to add device")
                    
            elif args.device_cmd == 'list':
                devices = simulator.device_manager.list_devices()
                print("Devices:")
                for dev in devices:
                    print(f"  - ID: {dev.device_id}, Name: {dev.name}, Protocol: {dev.protocol}")
                    
            elif args.device_cmd == 'remove':
                success = simulator.device_manager.remove_device(args.id)
                if success:
                    logger.info(f"Device {args.id} removed")
                else:
                    logger.error(f"Failed to remove device {args.id}")
                    
        elif args.command == 'tag':
            if args.tag_cmd == 'add':
                success = simulator.add_tag_mapping(
                    tag_id=args.id,
                    device_id=args.device_id,
                    address=args.address,
                    value_type=args.type,
                    description=args.description,
                    unit=args.unit
                )
                if success:
                    logger.info(f"Tag mapping added")
                else:
                    logger.error("Failed to add tag mapping")
                    
            elif args.tag_cmd == 'list':
                tags = simulator.get_all_mappings()
                print("Tag Mappings:")
                for t in tags:
                    print(f"  - {t.tag_id} -> Device:{t.device_id} Address:{t.address}")
                    
        elif args.command == 'simulate':
            logger.info("Starting SCADA simulation...")
            simulator.run_simulation()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
