import random
import time
import json
from datetime import datetime, timezone

NUM_NODES = 100
GATEWAY_ID = "LG-GW-PAT-01"

# Create 100 fake flood sensors
nodes = []

for i in range(1, NUM_NODES + 1):
    node = {
        "node_id": f"LG-NODE-PAT-{i:03d}",
        "lat": 25.6093 + random.uniform(-0.05, 0.05),
        "lng": 85.1376 + random.uniform(-0.05, 0.05),
        "water_level_m": random.uniform(0.7, 1.0)
    }

    nodes.append(node)


# Create a sensor reading
def create_packet(node, scenario):

    water_level = node["water_level_m"]

    # Normal situation
    if scenario == "NORMAL":
        rainfall = random.uniform(0, 5)
        water_level += random.uniform(-0.02, 0.02)

    # Heavy rain
    elif scenario == "HEAVY_RAIN":
        rainfall = random.uniform(30, 50)
        water_level += random.uniform(0.05, 0.12)

    # Flood
    elif scenario == "FLOOD":
        rainfall = random.uniform(40, 70)
        water_level += random.uniform(0.12, 0.25)

    # Flash flood
    elif scenario == "FLASH_FLOOD":
        rainfall = random.uniform(60, 100)
        water_level += random.uniform(0.5, 1.0)

    # Recovery
    elif scenario == "RECOVERY":
        rainfall = random.uniform(0, 5)
        water_level -= random.uniform(0.05, 0.15)

    water_level = max(0, water_level)

    node["water_level_m"] = water_level

    packet = {
        "schema_version": "1.0",
        "packet_type": "SENSOR_READING",

        "node_id": node["node_id"],
        "gateway_id": GATEWAY_ID,

        "timestamp": datetime.now(timezone.utc).isoformat(),

        "location": {
            "lat": round(node["lat"], 6),
            "lng": round(node["lng"], 6),
            "altitude_m": 52.3,
            "location_name": "Gandak River Monitoring Area"
        },

        "readings": {
            "water_level_m": round(water_level, 2),
            "rainfall_mm_hr": round(rainfall, 2),
            "temperature_c": round(random.uniform(25, 32), 2),
            "humidity_pct": round(random.uniform(70, 95), 2),
            "pressure_hpa": round(random.uniform(995, 1015), 2),

            "pm25_ugm3": None,
            "pm10_ugm3": None,
            "smoke_ppm": None,

            "soil_moisture_pct": round(random.uniform(40, 80), 2),
            "wind_speed_kmh": round(random.uniform(2, 15), 2),
            "uv_index": None
        },

        "device_health": {
            "battery_pct": random.randint(70, 100),
            "solar_charging": random.choice([True, False]),
            "signal_strength_dbm": random.randint(-95, -60),
            "uptime_seconds": random.randint(10000, 500000),
            "firmware_version": "1.2.3"
        }
    }

    return packet


# Run the flood simulation
for cycle in range(20):

    print("\n==============================")
    print("SIMULATION CYCLE:", cycle + 1)
    print("==============================")

   for node_number, node in enumerate(nodes[:1], start=1):

        # First 5 cycles: normal
        if cycle < 5:
            scenario = "NORMAL"

        # Next 5 cycles: heavy rain
        elif cycle < 10:
            scenario = "HEAVY_RAIN"

        # Next 3 cycles: flood
        elif cycle < 13:
            if node_number <= 80:
                scenario = "FLOOD"
            else:
                scenario = "HEAVY_RAIN"

        # Cycle 14: flash flood for first 10 sensors
        elif cycle == 13:
            if node_number <= 10:
                scenario = "FLASH_FLOOD"
            else:
                scenario = "FLOOD"

        # Remaining cycles: recovery
        else:
            scenario = "RECOVERY"

        packet = create_packet(node, scenario)

        print(json.dumps(packet, indent=2))

    time.sleep(1000)