from fastapi import FastAPI
from sqlalchemy.orm import Session
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

@app.get("/history")
def history():

    db = SessionLocal()

    records = db.query(Telemetry).all()

    results = []

    for record in records:
        results.append({
            "id": record.id,
            "timestamp": record.timestamp,
            "temperature": record.temperature,
            "pressure": record.pressure,
            "frequency": record.frequency,
            "active_power": record.active_power,
            "reactive_power": record.reactive_power,
            "equipment_health": record.equipment_health
        })

    db.close()

    return results


@app.get("/health")
def health():

    db = SessionLocal()

    latest_record = (
        db.query(Telemetry)
        .order_by(Telemetry.id.desc())
        .first()
    )

    db.close()

    if latest_record is None:
        return {
            "status": "No data available"
        }

    if latest_record.equipment_health < 95:
        status = "warning"
    else:
        status = "healthy"

    return {
        "status": status,
        "equipment_health": latest_record.equipment_health
    }
@app.get("/alerts")
def alerts():

    db = SessionLocal()

    latest_record = (
        db.query(Telemetry)
        .order_by(Telemetry.id.desc())
        .first()
    )

    db.close()

    if latest_record is None:
        return {
            "alert": "No telemetry available"
        }

    alerts = []

    if latest_record.temperature > 80:
        alerts.append("High temperature detected")

    if latest_record.pressure > 120:
        alerts.append("High pressure detected")

    if latest_record.equipment_health < 95:
        alerts.append("Equipment health warning")

    if len(alerts) == 0:
        alerts.append("No active alerts")

    return {
        "alerts": alerts
    }
@app.get("/dashboard")
def dashboard():

    db = SessionLocal()

    latest = db.query(Telemetry).order_by(Telemetry.id.desc()).first()

    if latest is None:
        db.close()
        return {"message": "No telemetry data available"}

    alerts = []

    if latest.temperature > 80:
        alerts.append("High temperature detected")

    if latest.pressure > 120:
        alerts.append("High pressure detected")

    if latest.equipment_health < 90:
        alerts.append("Equipment health warning")

    status = "healthy"

    if latest.equipment_health < 90:
        status = "warning"

    result = {
        "temperature": latest.temperature,
        "pressure": latest.pressure,
        "frequency": latest.frequency,
        "active_power": latest.active_power,
        "reactive_power": latest.reactive_power,
        "equipment_health": latest.equipment_health,
        "status": status,
        "alerts": alerts
    }

    db.close()

    return result