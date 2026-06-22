#!/usr/bin/env python3
"""
Simple script to run the electrical diagram simulator server.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    simulator_dir = Path(__file__).resolve().parent
    repo_root = simulator_dir.parent
    requirements_file = simulator_dir / "requirements.txt"
    
    print("Starting Electrical Diagram Simulator...")
    print("Installing dependencies...")
    
    # Install requirements
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return
    
    # Run the server
    try:
        print("Starting server...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "uvicorn",
            "simulator.backend.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")

if __name__ == "__main__":
    main()
