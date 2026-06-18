#!/usr/bin/env python3
"""Simple HTTP server to serve SCADA frontend."""
import http.server
import socketserver
import os
import sys

PORT = 8000
FRONTEND_DIR = "frontend"

# Change to project directory
os.chdir(r"C:\Users\user\Documents\Github\IEI\simulator")

class SCADAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

def start_server():
    """Start HTTP server to serve frontend."""
    try:
        with socketserver.TCPServer(("", PORT), SCADAHandler) as httpd:
            print(f"SCADA Simulator Frontend started on http://localhost:{PORT}")
            print("Press Ctrl+C to stop")
            print("=" * 50)
            print("Instructions:")
            print("- Add devices via web UI")
            print("- Edit existing devices")
            print("- Map tags/addresses per protocol")
            print("- Use CLI for terminal operations:")
            print("    python cli.py device add --name \"PLC-1\" --protocol modbus_tcp --ip 192.168.1.10")
            print("=" * 50)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(FRONTEND_DIR, exist_ok=True)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        start_server()
    else:
        # Just show usage
        print("Usage:")
        print(f"  {sys.argv[0]} start   # Start web server")
        print(f"  python3 cli.py        # Use CLI for device management")