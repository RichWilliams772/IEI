import random
from datetime import datetime

temperature = 75
pressure = 110
frequency = 60
active_power = 500
reactive_power = 150
equipment_health = 100


def generate_sensor_data():
    global temperature
    global pressure
    global frequency
    global active_power
    global reactive_power
    global equipment_health

    temperature += random.uniform(-1, 1)
    pressure += random.uniform(-2, 2)
    frequency += random.uniform(-0.05, 0.05)
    active_power += random.uniform(-10, 10)
    reactive_power += random.uniform(-5, 5)

    equipment_health -= random.uniform(0, 0.05)

    return {
        "timestamp": datetime.now().isoformat(),
        "temperature": round(temperature, 2),
        "pressure": round(pressure, 2),
        "frequency": round(frequency, 2),
        "active_power": round(active_power, 2),
        "reactive_power": round(reactive_power, 2),
        "equipment_health": round(equipment_health, 2)
    }