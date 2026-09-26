"""
test_model.py
================
TCP server that receives sensor data from ESP32 over Wi-Fi,
runs the Tier 2 ML model, and prints the prediction in terminal.

The ESP32 opens a new TCP connection each cycle and sends one CSV line:
    T:24.5,H:60.2,P:1001.3,WS:8.4,PM2.5:35.1,PM10:70.2,CO:812.0,PU:0.421,ALERT:1

Usage:
    python3 test_model.py
"""
import socket
import time
import joblib
import pandas as pd

# ── Config ─────────────────────────────────────────────────────────
HOST = "0.0.0.0"     # listen on all interfaces
PORT = 5050           # must match SERVER_PORT in the ESP32 sketch

# ── Load model ─────────────────────────────────────────────────────
model    = joblib.load("aqi_model_pi.joblib")
features = joblib.load("aqi_features_pi.joblib")

print(f"[INFO] Model loaded. Features: {features}")

# ── Key map (ESP32 tag → model feature name) ───────────────────────
KEY_MAP = {
    "T": "temp_c", "H": "humidity", "P": "pressure_mb", "WS": "windspeed_kph",
    "PM2.5": "pm2_5", "PM10": "pm10", "CO": "co",
    "PU": "esp32_probability", "ALERT": "esp32_alert",
}


# ── Parser ─────────────────────────────────────────────────────────
def parse_payload(payload_str: str) -> dict:
    """Parse a comma-separated key:value string into a dict of floats."""
    result = {}
    for field in payload_str.strip().split(","):
        key, sep, value = field.partition(":")
        if not sep:
            continue
        mapped_key = KEY_MAP.get(key.strip())
        if mapped_key is None:
            continue
        result[mapped_key] = float(value)
    return result


# ── TCP helper ─────────────────────────────────────────────────────
def get_esp32_data(conn) -> str | None:
    """
    Read one newline-terminated record from the ESP32 TCP connection.
    Returns the decoded string, or None on failure.
    """
    buffer = b""
    conn.settimeout(5.0)
    try:
        while True:
            chunk = conn.recv(256)
            if not chunk:
                break
            buffer += chunk
            if b"\n" in buffer:
                break
    except socket.timeout:
        pass

    if not buffer:
        return None

    line = buffer.decode("utf-8", errors="ignore").strip()
    return line if line else None


# ── Main ─────────────────────────────────────────────────────── ────
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[SERVER] Listening on {HOST}:{PORT} ...")
    print("Waiting for ESP32 data... (Ctrl+C to stop)\n")

    try:
        while True:
            conn, addr = server.accept()
            with conn:
                print(f"[CONN] Connected by {addr}")
                raw = get_esp32_data(conn)

                if raw is None:
                    print("[WARN] No valid data received.\n")
                    continue

                timestamp = time.strftime("%H:%M:%S")
                print(f"\n[{timestamp}] Received: {raw}")

                try:
                    parsed = parse_payload(raw)

                    # Check all model features are present
                    missing = [f for f in features if f not in parsed]
                    if missing:
                        print(f"  Missing fields for model: {missing}\n")
                        continue

                    # Build input row and predict
                    row = pd.DataFrame([{f: parsed[f] for f in features}])
                    probability = model.predict_proba(row)[0][1]

                    # Determine alert status from ESP32 flag (if present)
                    alert = int(parsed.get("esp32_alert", 0))

                    # ── Display ─────────────────────────────────
                    print("----------------------------------------------------")
                    print(f"  Temp(C)     : {parsed.get('temp_c', 0):.2f}  |  "
                          f"Humidity(%)  : {parsed.get('humidity', 0):.2f}  |  "
                          f"Pressure(mb) : {parsed.get('pressure_mb', 0):.2f}")
                    print(f"  Wind(kph)   : {parsed.get('windspeed_kph', 0):.2f}  |  "
                          f"PM2.5        : {parsed.get('pm2_5', 0):.2f}  |  "
                          f"PM10         : {parsed.get('pm10', 0):.2f}  |  "
                          f"CO           : {parsed.get('co', 0):.2f}")
                    print(f"  ESP32 P(U)  : {parsed.get('esp32_probability', 0):.4f}")
                    print(f"  Pi Model    : {probability:.4f}")
                    print(">>> STATUS: ALERT (HIGH RISK) <<<" if alert
                          else ">>> STATUS: SAFE <<<")
                    print("----------------------------------------------------\n")

                except (ValueError, KeyError) as e:
                    print(f"  Error processing data: {e}\n")

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
