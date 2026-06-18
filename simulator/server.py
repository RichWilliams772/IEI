#!/usr/bin/env python3
"""Simple HTTP server to serve SCADA frontend with mock API endpoints."""
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# Mock device storage
devices = [
    {
        "device_id": 1001,
        "name": "PLC-1",
        "protocol": "modbus_tcp", 
        "ip_address": "192.168.1.10",
        "port": 502,
        "description": "Main process controller",
        "registers": 125,
        "response_delay": 10
    },
    {
        "device_id": 1002,
        "name": "Sensor-2", 
        "protocol": "dnp3",
        "ip_address": "192.168.1.20",
        "port": 20000,
        "description": "Temperature sensor",
        "max_objects": 50,
        "timeout_seconds": 5
    }
]


class SCADAHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            # Serve HTML frontend
            try:
                with open('frontend/index.html', 'r') as f:
                    html = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())
            except Exception as e:
                self.send_error(404, f"File not found: {e}")
                
        elif self.path == '/api/devices':
            # Return list of devices
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(devices).encode())
            
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        if self.path == '/api/devices':
            # Add new device
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Create new device ID
                device_id = max([d['device_id'] for d in devices]) + 1 if devices else 1001
                
                new_device = {
                    "device_id": device_id,
                    "name": data.get("name"),
                    "protocol": data.get("protocol"),
                    "ip_address": data.get("ip_address"),
                    "port": int(data.get("port", 502)),
                    "description": data.get("description", ""),
                    **(data.get("params", {}))
                }
                
                devices.append(new_device)
                
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"id": device_id}).encode())
                
            except Exception as e:
                self.send_error(400, f"Invalid data: {e}")
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        # CORS support
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def start_server(port=8080):
    """Start HTTP server to serve frontend."""
    server = HTTPServer(('', port), SCADAHandler)
    print(f"SCADA Simulator Frontend started on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('frontend', exist_ok=True)
    
    # Start the server in a background thread so this script can exit cleanly
    threading.Thread(target=start_server, daemon=True).start()
    
    print("Frontend server running in background. Access at http://localhost:8080")