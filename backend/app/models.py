from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(String)

    temperature = Column(Float)
    pressure = Column(Float)
    frequency = Column(Float)

    active_power = Column(Float)
    reactive_power = Column(Float)

    equipment_health = Column(Float)