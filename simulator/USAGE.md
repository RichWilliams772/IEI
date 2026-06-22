# Electrical Diagram Simulator Usage Guide

## Overview

This is a basic single-line electrical diagram simulator with a continuously running FastAPI backend. It supports:

- Source (13.8 kV)
- Bus
- Transformer (step-up/down)
- Load (100 kW at 0.9 PF)
- Breaker (open/close)
- Meter (voltage, current, power readings)
- Consumer load
- Asynchronous generator

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. From the repository root, install dependencies:
```bash
pip install -r simulator/requirements.txt
```

### Running the Server

Use the helper script:
```bash
python simulator/run_server.py
```

Or run uvicorn directly from the repository root:
```bash
python -m uvicorn simulator.backend.api:app --host 0.0.0.0 --port 8000
```

On Windows, you can also run:
```bash
simulator/run_server.bat
```

The server starts on `http://localhost:8000`. Open `http://localhost:8000/` for the dashboard, or `http://localhost:8000/docs` for interactive API docs.

The simulation loop starts automatically at server startup and advances at the model sampling rate, which defaults to 16 ms.

## API Endpoints

### Get System Model
```http
GET /api/model
```
Returns the current system model with all components.

### Get System State
```http
GET /api/state
```
Returns the current state of the electrical system.

### Open Breaker
```http
POST /api/breakers/{breaker_id}/open
```
Opens a breaker by ID.

### Close Breaker
```http
POST /api/breakers/{breaker_id}/close
```
Closes a breaker by ID.

### Simulate Step
```http
POST /api/simulate/step
```
Performs one simulation step to update system state.

### Reload Model
```http
POST /api/model/reload
```
Reloads the model from file.

### Simulation Status
```http
GET /api/simulation/status
```
Returns whether the continuous background simulation loop is running.

## Example Usage

1. Get the current system state:
```bash
curl http://localhost:8000/api/state
```

2. Open a breaker:
```bash
curl -X POST http://localhost:8000/api/breakers/breaker-main/open
```

3. Close a breaker:
```bash
curl -X POST http://localhost:8000/api/breakers/breaker-main/close
```

## Model Structure

The system model is defined in JSON format with components including:

- `id`: Unique identifier for the component
- `type`: Component type (source, bus, transformer, load, breaker, meter)
- `name`: Human-readable name
- `position`: X,Y coordinates for visualization
- Type-specific properties like voltage ratings, power ratings, etc.

## Architecture

The simulator is built with a modular architecture:

1. **Model Layer**: Defines components and system structure using Pydantic models
2. **Services Layer**:
   - `model_loader.py`: Handles model loading from JSON files
   - `simulator.py`: Core simulation logic
   - `meters.py`: Meter reading calculations
   - `protection.py`: Protection logic for breakers
3. **API Layer**: FastAPI endpoints exposing the simulator functionality

## Future Enhancements

This basic implementation can be extended with:

- V/f behavior simulation
- Fault current calculations
- Relay protection curves
- More complex network topologies
- Real-time data persistence
