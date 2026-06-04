import random
from datetime import datetime

def generate_sensor_data():
    return {
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(60, 95), 2),
        "pressure": round(random.uniform(90, 130), 2),
        "frequency": round(random.uniform(59.8, 60.2), 2),
        "active_power": round(random.uniform(400, 1000), 2),
        "reactive_power": round(random.uniform(100, 300), 2),
        "equipment_health": round(random.uniform(80, 100), 2)
    }