"""
pi_lora_tier2_mqtt.py
========================
Receives ESP32 alerts via LoRa (compact key:value string format, NOT
JSON), re-scores with the full Tier 2 model, publishes to cloud MQTT.

ESP32 sends: "T:22.5,H:55.0,P:1013.0,WS:15.0,PM2.5:25.0,PM10:40.0,CO:0.3,PU:0.123,ALERT:0"
"""
import json
import time
import joblib
import pandas as pd
from collections import deque
import paho.mqtt.client as mqtt
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD

model = joblib.load("aqi_model_pi.joblib")        # full Pipeline: imputer+scaler+classifier
threshold = joblib.load("aqi_threshold_pi.joblib")
features = joblib.load("aqi_features_pi.joblib")   # ['temp_c','humidity','windspeed_kph','pressure_mb','pm2_5','pm10','co']

history = deque(maxlen=6)

# NOTE: the compact payload has no node_id field -- set this to match
# whichever ESP32 node is sending. If you have multiple AQI nodes later,
# each would need its own identifier added to the ESP32's snprintf() call.
NODE_ID = "aqi_node_1"

CLOUD_BROKER = "your-cloud-server-address"  # your FastAPI backend's broker
cloud_client = mqtt.Client()
cloud_client.connect(CLOUD_BROKER, 1883, keepalive=60)
cloud_client.loop_start()


# ---------------------------------------------------------------------
# Parser for the compact key:value payload -- replaces json.loads()
# ---------------------------------------------------------------------
KEY_MAP = {
    "T": "temp_c", "H": "humidity", "P": "pressure_mb", "WS": "windspeed_kph",
    "PM2.5": "pm2_5", "PM10": "pm10", "CO": "co",
    "PU": "esp32_probability", "ALERT": "esp32_alert",
}

def parse_lora_payload(payload_str: str) -> dict:
    result = {}
    for field in payload_str.strip().split(","):
        key, sep, value = field.partition(":")
        if not sep:
            continue  # malformed field (no colon), skip rather than crash
        mapped_key = KEY_MAP.get(key.strip())
        if mapped_key is None:
            continue  # unknown/unexpected field, skip
        result[mapped_key] = float(value)
    return result


class LoRaReceiver(LoRa):
    def on_rx_done(self):
        payload_bytes = self.read_payload(nocheck=True)
        payload_str = bytes(payload_bytes).decode("utf-8", errors="ignore")
        print(f"[LoRa RX] {payload_str}")

        try:
            parsed = parse_lora_payload(payload_str)

            missing = [f for f in features if f not in parsed]
            if missing:
                print(f"[WARN] Payload missing expected fields {missing}, skipping.")
                self.set_mode(1)
                self.clear_irq_flags(RxDone=1)
                return

            row = pd.DataFrame([{f: parsed[f] for f in features}])
            full_prob = model.predict_proba(row)[0][1]  # Pipeline handles imputation+scaling internally
            history.append(full_prob)

            is_alert = full_prob >= threshold
            trend = "rising" if len(history) >= 2 and history[-1] > history[0] else "stable_or_falling"

            result = {
                "node_id": NODE_ID,
                "current_probability": round(float(full_prob), 3),
                "alert": bool(is_alert),
                "trend": trend,
                "threshold_used": float(threshold),
                # Edge (ESP32) vs Tier 2 (Pi) comparison -- useful for judges/debugging,
                # shows the distilled model's estimate alongside the full model's
                "esp32_probability": parsed.get("esp32_probability"),
                "esp32_alert": bool(parsed.get("esp32_alert", 0)),
            }
            cloud_client.publish(f"sensors/{NODE_ID}/tier2_forecast", json.dumps(result))
            print(f"[Published to cloud] {result}")

        except (ValueError, KeyError) as e:
            print(f"[WARN] Bad LoRa payload, could not parse: {e}")

        self.set_mode(1)
        self.clear_irq_flags(RxDone=1)


def main():
    BOARD.setup()
    lora = LoRaReceiver(verbose=False)
    lora.set_mode(1)
    lora.set_freq(433.0)  # match ESP32's LoRa.begin() frequency
    print("Pi LoRa gateway + Tier 2 model online.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        BOARD.teardown()
        cloud_client.loop_stop()


if __name__ == "__main__":
    main()