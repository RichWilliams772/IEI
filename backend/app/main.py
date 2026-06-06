from fastapi import FastAPI
from simulator.telemetry_generator import generate_sensor_data
from backend.app.models import Base, Telemetry
from backend.app.database import engine, SessionLocal

app = FastAPI(
    title="Intelligent Energy Monitoring Platform"
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Energy Monitoring API Running"}

@app.get("/telemetry")
def telemetry():
    data = generate_sensor_data()

    db = SessionLocal()

    telemetry_record = Telemetry(
        timestamp=data["timestamp"],
        temperature=data["temperature"],
        pressure=data["pressure"],
        frequency=data["frequency"],
        active_power=data["active_power"],
        reactive_power=data["reactive_power"],
        equipment_health=data["equipment_health"]
    )

    db.add(telemetry_record)
    db.commit()
    db.refresh(telemetry_record)
    db.close()

    return data