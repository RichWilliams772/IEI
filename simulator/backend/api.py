import asyncio
from contextlib import suppress
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .models import Model, SystemState
from .services.model_loader import ModelLoader
from .services.simulator import Simulator

# Initialize the FastAPI app
app = FastAPI(title="Electrical Diagram Simulator API", version="1.0.0")

# Global variables to store model and simulator
model: Model = None
simulator: Simulator = None
simulation_task: asyncio.Task = None
state_lock = asyncio.Lock()
FRONTEND_INDEX = Path(__file__).resolve().parents[1] / "frontend" / "index.html"

async def simulation_loop():
    """Continuously advance the simulator at the configured sampling interval."""
    while True:
        if simulator is not None:
            interval = max((simulator.model.sampling_rate_ms or 16) / 1000, 0.001)
            async with state_lock:
                simulator.simulate_step()
            await asyncio.sleep(interval)
        else:
            await asyncio.sleep(0.1)

@app.get("/")
async def root():
    """Serve the simulator frontend."""
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(FRONTEND_INDEX)

@app.get("/api")
async def api_info():
    """Return basic API information."""
    return {
        "name": "Electrical Diagram Simulator API",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/api/model",
            "/api/state",
            "/api/simulate/step",
            "/api/model/reload",
            "/api/simulation/status"
        ]
    }

@app.on_event("startup")
async def load_model():
    """Load the example model at startup"""
    global model, simulator, simulation_task
    try:
        model = ModelLoader.load_example_model()
        simulator = Simulator(model)
        async with state_lock:
            simulator.simulate_step()
        simulation_task = asyncio.create_task(simulation_loop())
    except Exception as e:
        print(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail="Failed to load model")

@app.on_event("shutdown")
async def stop_simulation():
    """Stop the background simulation loop."""
    global simulation_task
    if simulation_task is not None:
        simulation_task.cancel()
        with suppress(asyncio.CancelledError):
            await simulation_task
        simulation_task = None

@app.get("/api/model", response_model=Model)
async def get_model():
    """Get the current system model"""
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    return model

@app.get("/api/state", response_model=SystemState)
async def get_system_state():
    """Get the current system state"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    async with state_lock:
        return simulator.get_system_state()

@app.post("/api/breakers/{breaker_id}/open")
async def open_breaker(breaker_id: str):
    """Open a breaker"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    async with state_lock:
        success = simulator.update_breaker_state(breaker_id, False)
        if success:
            simulator.simulate_step()
    if not success:
        raise HTTPException(status_code=404, detail="Breaker not found")

    return {"status": "success", "breaker_id": breaker_id, "state": "open"}

@app.post("/api/breakers/{breaker_id}/close")
async def close_breaker(breaker_id: str):
    """Close a breaker"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    async with state_lock:
        success = simulator.update_breaker_state(breaker_id, True)
        if success:
            simulator.simulate_step()
    if not success:
        raise HTTPException(status_code=404, detail="Breaker not found")

    return {"status": "success", "breaker_id": breaker_id, "state": "closed"}

@app.post("/api/simulate/step")
async def simulate_step():
    """Perform one simulation step"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    async with state_lock:
        state = simulator.simulate_step()
    return {"status": "success", "state": state}

@app.post("/api/model/reload")
async def reload_model():
    """Reload the model from file"""
    global model, simulator
    try:
        new_model = ModelLoader.load_example_model()
        new_simulator = Simulator(new_model)
        async with state_lock:
            model = new_model
            simulator = new_simulator
            simulator.simulate_step()
        return {"status": "success", "message": "Model reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")

@app.post("/api/consumer_load/{consumer_load_id}/unexpected_draw")
async def set_unexpected_draw(consumer_load_id: str, unexpected_draw_active: bool, multiplier: float = 1.5):
    """Set unexpected draw for a consumer load"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    async with state_lock:
        success = simulator.update_consumer_load_draw(consumer_load_id, unexpected_draw_active, multiplier)
        if success:
            simulator.simulate_step()
    if not success:
        raise HTTPException(status_code=404, detail="Consumer load not found")

    return {"status": "success", "consumer_load_id": consumer_load_id, "unexpected_draw_active": unexpected_draw_active, "multiplier": multiplier}

@app.post("/api/async_generator/{generator_id}/operational")
async def set_generator_operational(generator_id: str, operational: bool):
    """Set operational state for an asynchronous generator"""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    async with state_lock:
        success = simulator.update_async_generator_state(generator_id, operational)
        if success:
            simulator.simulate_step()
    if not success:
        raise HTTPException(status_code=404, detail="Generator not found")

    return {"status": "success", "generator_id": generator_id, "operational": operational}

@app.get("/api/simulation/status")
async def simulation_status():
    """Get background simulation status."""
    if simulator is None:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    return {
        "running": simulation_task is not None and not simulation_task.done(),
        "sampling_rate_ms": simulator.model.sampling_rate_ms,
        "timestamp": simulator.get_system_state().timestamp
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
