from fastapi import FastAPI
from simulator.telemetry_generator import generate_sensor_data

app = FastAPI(
    title="Intelligent Energy Monitoring Platform"
)

@app.get("/")
def root():
    return {"message": "Energy Monitoring API Running"}

@app.get("/telemetry")
def telemetry():
    return generate_sensor_data()