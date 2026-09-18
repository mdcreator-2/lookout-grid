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


# ==============================
# CREATE 100 AQI SENSORS
# ==============================

nodes = []

for i in range(1, NUM_NODES + 1):

    nodes.append({
        "node_id": f"LG-NODE-PAT-{i:03d}",
        "lat": 25.6093 + random.uniform(-0.05, 0.05),
        "lng": 85.1376 + random.uniform(-0.05, 0.05)
    })


# ==============================
# CREATE AQI SENSOR PACKET
# ==============================

def create_packet(node, scenario):

    if scenario == "NORMAL":

        pm25 = random.uniform(5, 35)
        pm10 = random.uniform(10, 60)
        smoke = random.uniform(0, 5)
        co = random.uniform(0, 5)

    elif scenario == "POLLUTION":

        pm25 = random.uniform(80, 200)
        pm10 = random.uniform(150, 300)
        smoke = random.uniform(5, 30)
        co = random.uniform(5, 20)

    elif scenario == "SEVERE_POLLUTION":

        pm25 = random.uniform(200, 500)
        pm10 = random.uniform(300, 600)
        smoke = random.uniform(20, 80)
        co = random.uniform(15, 50)

    elif scenario == "RECOVERY":

        pm25 = random.uniform(20, 60)
        pm10 = random.uniform(30, 100)
        smoke = random.uniform(0, 10)
        co = random.uniform(0, 8)

    else:

        pm25 = 20
        pm10 = 40
        smoke = 2
        co = 2


    # Simple simulated AQI value

    aqi = int(pm25 * 2)


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

            "location_name": "Air Quality Monitoring Area"
        },

        "readings": {

            "aqi": aqi,

            "pm25_ugm3": round(pm25, 2),

            "pm10_ugm3": round(pm10, 2),

            "smoke_ppm": round(smoke, 2),

            "co_ppm": round(co, 2),

            "temperature_c": round(
                random.uniform(25, 35), 2
            ),

            "humidity_pct": round(
                random.uniform(40, 90), 2
            ),

            "pressure_hpa": round(
                random.uniform(995, 1015), 2
            ),

            "wind_speed_kmh": round(
                random.uniform(2, 20), 2
            ),

            "water_level_m": None,

            "rainfall_mm_hr": round(
                random.uniform(0, 5), 2
            ),

            "soil_moisture_pct": round(
                random.uniform(30, 70), 2
            ),

            "uv_index": round(
                random.uniform(0, 10), 2
            )
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


# ==============================
# RUN AQI SIMULATION
# ==============================

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
    print("Scenario:", scenario)

    for cycle in range(20):

        print("\n==============================")
        print("SIMULATION CYCLE:", cycle + 1)
        print("SCENARIO:", scenario)
        print("==============================")

        for node in nodes:

            packet = create_packet(
                node,
                scenario
            )

            client.publish(
                MQTT_TOPIC,
                json.dumps(packet)
            )

        print(
            f"Published {len(nodes)} AQI sensor packets to MQTT."
        )

        time.sleep(10)

    client.loop_stop()

    client.disconnect()

    print("\nMQTT disconnected.")