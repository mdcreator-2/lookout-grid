import random
import time
import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


# ==============================
# SETTINGS
# ==============================

NUM_NODES = 100

GATEWAY_ID = "LG-GW-PAT-01"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lookout-grid/sensors"


# ==============================
# CREATE 100 FLOOD SENSOR NODES
# ==============================

nodes = []

for i in range(1, NUM_NODES + 1):
    nodes.append({
        "node_id": f"LG-NODE-PAT-{i:03d}",
        "lat": 25.6116 + random.uniform(-0.05, 0.05),
        "lng": 85.116477 + random.uniform(-0.05, 0.05)
    })


# ==============================
# CREATE SENSOR PACKET
# ==============================

def create_packet(node, scenario):

    # --------------------------
    # NORMAL
    # --------------------------

    if scenario == "NORMAL":

        water_level = random.uniform(0.5, 1.0)
        rainfall = random.uniform(0, 5)

    # --------------------------
    # HEAVY RAIN
    # --------------------------

    elif scenario == "HEAVY_RAIN":

        water_level = random.uniform(1.0, 2.0)
        rainfall = random.uniform(20, 60)

    # --------------------------
    # FLOOD
    # --------------------------

    elif scenario == "FLOOD":

        water_level = random.uniform(2.0, 4.0)
        rainfall = random.uniform(60, 120)

    # --------------------------
    # FLASH FLOOD
    # --------------------------

    elif scenario == "FLASH_FLOOD":

        water_level = random.uniform(4.0, 6.0)
        rainfall = random.uniform(120, 200)

    # --------------------------
    # RECOVERY
    # --------------------------

    elif scenario == "RECOVERY":

        water_level = random.uniform(0.8, 1.8)
        rainfall = random.uniform(0, 15)

    else:

        water_level = 0.7
        rainfall = 2.0


    # ==========================
    # OTHER ENVIRONMENT VALUES
    # ==========================

    temperature = random.uniform(25, 35)
    humidity = random.uniform(60, 95)
    pressure = random.uniform(990, 1015)
    soil_moisture = random.uniform(50, 90)
    wind_speed = random.uniform(2, 20)


    # ==========================
    # SENSOR PACKET
    # ==========================

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

            "temperature_c": round(temperature, 2),

            "humidity_pct": round(humidity, 2),

            "pressure_hpa": round(pressure, 2),

            "pm25_ugm3": None,

            "pm10_ugm3": None,

            "smoke_ppm": None,

            "soil_moisture_pct": round(soil_moisture, 2),

            "wind_speed_kmh": round(wind_speed, 2),

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


# ==============================
# RUN FLOOD SIMULATION
# ==============================

def run_simulation(scenario):

    print()
    print("🌊 FLOOD SIMULATION STARTED")
    print("Scenario:", scenario)
    print("Connecting to MQTT broker...")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    client.loop_start()

    print("MQTT connected successfully!")
    print(f"Simulating {NUM_NODES} flood sensor nodes.")

    # --------------------------
    # 20 SIMULATION CYCLES
    # --------------------------

    for cycle in range(20):

        print()
        print("==============================")
        print(f"FLOOD SIMULATION CYCLE: {cycle + 1}")
        print(f"SCENARIO: {scenario}")
        print("==============================")

        published = 0

        # ----------------------
        # SEND 100 SENSOR PACKETS
        # ----------------------

        for node in nodes:

            packet = create_packet(
                node,
                scenario
            )

            result = client.publish(
                MQTT_TOPIC,
                json.dumps(packet)
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                published += 1

        print(
            f"Published {published}/{NUM_NODES} flood sensor packets to MQTT."
        )

        # Wait before next cycle
        time.sleep(10)

    # ==========================
    # DISCONNECT
    # ==========================

    client.loop_stop()

    client.disconnect()

    print()
    print("🌊 Flood simulation completed.")
    print("MQTT disconnected.")