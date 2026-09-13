import random
import time
import json
from datetime import datetime, timezone
import paho.mqtt.client as mqtt


NUM_NODES = 100

GATEWAY_ID = "LG-GW-PAT-01"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lookout-grid/sensors"


# ==========================================
# CREATE 100 FOREST FIRE SENSOR NODES
# ==========================================

nodes = []

for i in range(1, NUM_NODES + 1):
    nodes.append({
        "node_id": f"LG-NODE-FIRE-{i:03d}",
        "lat": 25.6093 + random.uniform(-0.05, 0.05),
        "lng": 85.1376 + random.uniform(-0.05, 0.05)
    })


# ==========================================
# CREATE FIRE SENSOR PACKET
# ==========================================

def create_packet(node, scenario):

    if scenario == "NORMAL":

        temperature = random.uniform(25, 35)
        humidity = random.uniform(50, 85)
        co = random.uniform(0, 5)
        air_quality = random.uniform(10, 50)
        soil_moisture = random.uniform(40, 70)

    elif scenario == "FIRE":

        temperature = random.uniform(40, 65)
        humidity = random.uniform(20, 50)
        co = random.uniform(10, 30)
        air_quality = random.uniform(80, 200)
        soil_moisture = random.uniform(20, 45)

    elif scenario == "SEVERE_FIRE":

        temperature = random.uniform(65, 100)
        humidity = random.uniform(10, 30)
        co = random.uniform(30, 80)
        air_quality = random.uniform(200, 500)
        soil_moisture = random.uniform(5, 25)

    elif scenario == "RECOVERY":

        temperature = random.uniform(30, 40)
        humidity = random.uniform(40, 70)
        co = random.uniform(2, 10)
        air_quality = random.uniform(30, 100)
        soil_moisture = random.uniform(25, 50)

    else:

        temperature = 30
        humidity = 60
        co = 2
        air_quality = 30
        soil_moisture = 50


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
            "location_name": "Forest Fire Monitoring Area"
        },

        "readings": {

            # BME280
            "temperature_c": round(temperature, 2),
            "humidity_pct": round(humidity, 2),
            "pressure_hpa": round(
                random.uniform(995, 1015), 2
            ),

            # MQ-7
            "co_ppm": round(co, 2),

            # MQ-135
            "air_quality": round(air_quality, 2),

            # Soil moisture sensor
            "soil_moisture_pct": round(
                soil_moisture, 2
            ),

            # Not available from the listed hardware
            "pm25_ugm3": None,
            "pm10_ugm3": None,
            "smoke_ppm": None,

            # Not relevant to fire node
            "water_level_m": None,
            "rainfall_mm_hr": None,
            "uv_index": None
        },

        "device_health": {

            "battery_pct": random.randint(70, 100),

            "solar_charging": random.choice(
                [True, False]
            ),

            "signal_strength_dbm": random.randint(
                -95, -60
            ),

            "uptime_seconds": random.randint(
                10000, 500000
            ),

            "firmware_version": "1.2.3"
        }
    }

    return packet


# ==========================================
# RUN FIRE SIMULATION
# ==========================================

def run_simulation(scenario):

    print("\nConnecting to MQTT broker...")

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
    print("🔥 Scenario:", scenario)

    for cycle in range(20):

        print("\n==============================")
        print("FIRE SIMULATION CYCLE:", cycle + 1)
        print("SCENARIO:", scenario)
        print("==============================")

        for node in nodes:

            packet = create_packet(
                node,
                scenario
            )

            client.publish(
                MQTT_TOPIC,
                json.dumps(packet),
                qos=1
            )

        print(
            f"Published {NUM_NODES} fire sensor packets."
        )

        time.sleep(10)

    client.loop_stop()
    client.disconnect()

    print("\nMQTT disconnected.")