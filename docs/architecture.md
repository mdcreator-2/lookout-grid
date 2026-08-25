## Where Does the Edge ML Model Sit? (Layer 1 AND Layer 2)

**Short answer: BOTH layers have ML models, but different kinds.**

This is the most important architectural distinction in your project:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML MODEL DISTRIBUTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1 — ESP32 (Edge Node)                                   │
│  ┌─────────────────────────────────────┐                       │
│  │ What runs here:                     │                       │
│  │  • TFLite Micro model (<100KB)      │                       │
│  │  • Simple anomaly detection         │                       │
│  │  • Threshold-based rules            │                       │
│  │                                     │                       │
│  │ Example models:                     │                       │
│  │  • "Is this sensor reading normal   │                       │
│  │    or abnormal?" (binary classifier)│                       │
│  │  • "Has water level crossed danger  │                       │
│  │    threshold?" (rule-based + tiny   │                       │
│  │    decision tree)                   │                       │
│  │                                     │                       │
│  │ WHY so small?                       │                       │
│  │  ESP32 has only 520KB RAM and       │                       │
│  │  4MB flash. A full neural network   │                       │
│  │  simply won't fit.                  │                       │
│  └─────────────────────────────────────┘                       │
│           │                                                     │
│           │ Sends anomaly flag + raw data                       │
│           ▼                                                     │
│  LAYER 2 — Raspberry Pi (Gateway)                              │
│  ┌─────────────────────────────────────┐                       │
│  │ What runs here:                     │                       │
│  │  • TFLite model (1-10MB)            │                       │
│  │  • Real ML inference (LSTM, CNN,    │                       │
│  │    Random Forest, XGBoost)          │                       │
│  │  • Multi-sensor correlation         │                       │
│  │                                     │                       │
│  │ Example models:                     │                       │
│  │  • "Based on water level + rainfall │                       │
│  │    + humidity from 5 nearby nodes,  │                       │
│  │    what is the flood probability    │                       │
│  │    in the next 2 hours?"            │                       │
│  │  • "Based on PM2.5 + wind speed +   │                       │
│  │    temperature, will AQI cross 300  │                       │
│  │    in the next 6 hours?"            │                       │
│  │                                     │                       │
│  │ WHY here?                           │                       │
│  │  Raspberry Pi has 4GB RAM and a     │                       │
│  │  full Linux OS. It can run real     │                       │
│  │  Python ML models.                  │                       │
│  └─────────────────────────────────────┘                       │
│           │                                                     │
│           │ Sends risk assessment + summarized data             │
│           ▼                                                     │
│  LAYER 3 — Cloud Server                                        │
│  ┌─────────────────────────────────────┐                       │
│  │ What runs here:                     │                       │
│  │  • Full TensorFlow/PyTorch models   │                       │
│  │    (50-500MB)                       │                       │
│  │  • Deep neural networks, ensemble   │                       │
│  │    models                           │                       │
│  │  • Historical trend analysis        │                       │
│  │  • Model retraining pipeline        │                       │
│  │                                     │                       │
│  │ Example:                            │                       │
│  │  • "Based on 5 years of historical  │                       │
│  │    data + current sensor readings   │                       │
│  │    from 500 nodes + IMD weather     │                       │
│  │    forecast, what is the flood      │                       │
│  │    risk for the next 7 days across  │                       │
│  │    the entire state?"               │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```





## Complete Architecture Walkthrough — Every Layer Explained

### LAYER 1: Edge Sensor Nodes (The Field Soldiers)

```
┌──────────────────────────────────────────────────┐
│              EDGE SENSOR NODE                     │
│         (deployed in field/river/forest)          │
│                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │Water Level│   │ BME280   │   │ PMS5003  │     │
│  │ Sensor   │   │Temp/Hum/ │   │ PM2.5/   │     │
│  │(Ultrasonic)│  │Pressure  │   │ PM10     │     │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘     │
│       │              │              │             │
│       └──────────┬───┘──────────────┘             │
│                  │                                │
│           ┌──────▼──────┐                         │
│           │   ESP32-S3  │                         │
│           │             │                         │
│           │ • Reads sensor data every 30 sec      │
│           │ • Runs TFLite Micro model             │
│           │ • If NORMAL: stores locally, sends    │
│           │   summary every 5 min via LoRa        │
│           │ • If ANOMALY: immediately sends       │
│           │   alert + raw data via LoRa           │
│           │ • Deep sleeps between readings to     │
│           │   save battery                        │
│           └──────┬──────┘                         │
│                  │                                │
│           ┌──────▼──────┐                         │
│           │ LoRa Module │ ──── radio waves ───►   │
│           │  (SX1278)   │      to Gateway         │
│           └─────────────┘      (up to 10 km)      │
│                                                   │
│  ┌─────────────┐  ┌─────────────┐                │
│  │ Solar Panel  │  │  Battery    │                │
│  │  (6V 2W)    │──│ (18650 ×2)  │                │
│  └─────────────┘  └─────────────┘                │
│                                                   │
│  All inside a weatherproof enclosure box          │
└──────────────────────────────────────────────────┘
```

**What happens here step-by-step:**

1. **Sensors read** the environment every 30 seconds (water level, temperature, humidity, air quality, etc.)
2. **ESP32 wakes up** from deep sleep, reads sensor values
3. **ESP32 runs the tiny ML model** (a decision tree or tiny autoencoder, <100KB):
   - The model asks: *"Are these readings normal or abnormal?"*
   - Example: Water level suddenly rose 50cm in 10 minutes → **ABNORMAL**
   - Example: Temperature is 32°C, normal for this season → **NORMAL**
4. **If NORMAL**: ESP32 saves the reading locally and goes back to sleep. Every 5 minutes, it sends a summary packet via LoRa.
5. **If ABNORMAL**: ESP32 immediately sends a high-priority alert packet via LoRa to the gateway with all raw sensor data.
6. **ESP32 goes back to deep sleep** to conserve battery.

---

### LAYER 2: Gateway / Fog Layer (The Regional Commander)

```
┌──────────────────────────────────────────────────┐
│              GATEWAY NODE                         │
│     (placed in village/ward office/tower)         │
│                                                   │
│  ┌─────────────┐                                 │
│  │ LoRa Module │ ◄── receives data from          │
│  │  (SX1278)   │     5-15 edge nodes              │
│  └──────┬──────┘     within 10 km radius          │
│         │                                         │
│  ┌──────▼──────────────────────────────────┐     │
│  │        RASPBERRY PI 4 (4GB RAM)         │     │
│  │                                         │     │
│  │  Software running:                      │     │
│  │  ┌─────────────────────────────────┐   │     │
│  │  │ 1. LoRa Receiver Service        │   │     │
│  │  │    • Receives packets from all   │   │     │
│  │  │      connected edge nodes        │   │     │
│  │  │    • Parses sensor data          │   │     │
│  │  └─────────────┬───────────────────┘   │     │
│  │                │                        │     │
│  │  ┌─────────────▼───────────────────┐   │     │
│  │  │ 2. Data Aggregation Engine      │   │     │
│  │  │    • Combines data from multiple │   │     │
│  │  │      nodes                       │   │     │
│  │  │    • Time-aligns readings        │   │     │
│  │  │    • Computes regional averages  │   │     │
│  │  └─────────────┬───────────────────┘   │     │
│  │                │                        │     │
│  │  ┌─────────────▼───────────────────┐   │     │
│  │  │ 3. ML Inference Engine          │   │     │
│  │  │    • Runs LSTM/RF/XGBoost model │   │     │
│  │  │    • Multi-node correlation:     │   │     │
│  │  │      "Node 3 upstream shows     │   │     │
│  │  │       rising water + Node 7     │   │     │
│  │  │       shows heavy rain →        │   │     │
│  │  │       Flood risk for downstream │   │     │
│  │  │       area = HIGH (0.87)"       │   │     │
│  │  └─────────────┬───────────────────┘   │     │
│  │                │                        │     │
│  │  ┌─────────────▼───────────────────┐   │     │
│  │  │ 4. Decision Engine              │   │     │
│  │  │    • Risk < 0.3 → NORMAL        │   │     │
│  │  │      (send summary to cloud     │   │     │
│  │  │       every 15 min)             │   │     │
│  │  │    • Risk 0.3-0.7 → WARNING     │   │     │
│  │  │      (send to cloud immediately │   │     │
│  │  │       for deep analysis)        │   │     │
│  │  │    • Risk > 0.7 → CRITICAL      │   │     │
│  │  │      (send to cloud + trigger   │   │     │
│  │  │       LOCAL alerts: siren,      │   │     │
│  │  │       SMS, LED warning)         │   │     │
│  │  └─────────────┬───────────────────┘   │     │
│  │                │                        │     │
│  │  ┌─────────────▼───────────────────┐   │     │
│  │  │ 5. MQTT Client                  │   │     │
│  │  │    • Publishes data/alerts to   │   │     │
│  │  │      cloud MQTT broker          │   │     │
│  │  │    • Uses 4G modem for internet │   │     │
│  │  └─────────────────────────────────┘   │     │
│  └─────────────────────────────────────────┘     │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 4G Modem │  │  Power   │  │ Local    │       │
│  │(SIM7600) │  │ Supply   │  │ Siren/LED│       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                   │
└──────────────────────────────────────────────────┘
```

**What happens here step-by-step:**

1. **Receives data** from all connected edge nodes (5-15 nodes) via LoRa radio
2. **Aggregates data** — combines readings from multiple sensors in the region
3. **Runs real ML models** — an LSTM or Random Forest that takes multi-node data as input and outputs a risk probability (e.g., flood probability = 0.87)
4. **Correlates across nodes** — this is the KEY intelligence:
   - Node 3 (upstream on river) shows water level rising
   - Node 5 (nearby) shows heavy rainfall
   - Node 8 (downstream) shows normal water level **but** the gateway predicts it will flood in ~45 minutes based on upstream patterns
5. **Makes a decision**:
   - Low risk → send summary to cloud every 15 minutes
   - Medium risk → send to cloud immediately for deep analysis
   - High risk → send to cloud AND trigger local alerts (siren, SMS to village head)
6. **Sends to cloud** via 4G modem using MQTT protocol

> [!TIP]
> **The gateway is the brain of your system.** The ESP32 is the eyes (sensing), the gateway is the brain (thinking), and the cloud is the memory + big brain (long-term analysis, heavy models).

---

### LAYER 3: Cloud Backend (The Command Center)

```
┌──────────────────────────────────────────────────────────────┐
│                    CLOUD BACKEND                              │
│          (runs on AWS/GCP or your college server)             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              MQTT BROKER (Mosquitto)                    │  │
│  │  • Receives messages from all gateways                 │  │
│  │  • Organizes by "topics":                              │  │
│  │    - sensors/flood/gateway-01/data                     │  │
│  │    - sensors/flood/gateway-01/alert                    │  │
│  │    - sensors/airquality/gateway-02/data                │  │
│  └──────────────────┬─────────────────────────────────────┘  │
│                     │                                         │
│      ┌──────────────┼──────────────┐                         │
│      │              │              │                          │
│      ▼              ▼              ▼                          │
│  ┌────────┐   ┌──────────┐   ┌──────────┐                   │
│  │FastAPI │   │  Heavy   │   │PostgreSQL│                    │
│  │Backend │   │ ML Model │   │+Timescale│                    │
│  │  API   │   │ Server   │   │   DB     │                    │
│  │        │   │          │   │          │                     │
│  │• REST  │   │• Full    │   │• Stores  │                    │
│  │  APIs  │   │  LSTM/   │   │  ALL     │                    │
│  │• WebSoc│   │  Trans-  │   │  sensor  │                    │
│  │  ket   │   │  former  │   │  data    │                    │
│  │  for   │   │• 7-day   │   │• Time-   │                    │
│  │  real- │   │  fore-   │   │  series  │                    │
│  │  time  │   │  cast    │   │  queries │                    │
│  │  dash  │   │• Model   │   │• Histori-│                    │
│  │        │   │  retrain │   │  cal     │                    │
│  └───┬────┘   └──────────┘   │  trends  │                    │
│      │                        └──────────┘                    │
│      │                                                        │
│      ├────────────────────────────┐                           │
│      │                            │                           │
│      ▼                            ▼                           │
│  ┌──────────┐            ┌──────────────┐                    │
│  │React.js  │            │ Alert Engine │                     │
│  │Dashboard │            │              │                     │
│  │          │            │• Firebase    │                     │
│  │• GIS Map │            │  Push Notif  │                     │
│  │• Live    │            │• SMS (Twilio)│                     │
│  │  graphs  │            │• Email       │                     │
│  │• Alert   │            │• WhatsApp    │                     │
│  │  feed    │            │  Business API│                     │
│  │• Risk    │            └──────────────┘                     │
│  │  heatmap │                                                 │
│  └──────────┘                                                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**What happens here:**

1. **MQTT Broker** receives messages from all gateways across the region
2. **FastAPI Backend** processes the data — stores to database, serves to dashboard
3. **Heavy ML Model** runs deep analysis when gateway escalates (flood probability with 7-day forecast)
4. **Database** stores all historical data for trend analysis
5. **Dashboard** shows real-time maps, graphs, alerts to authorities
6. **Alert Engine** sends notifications to citizens and officials

---





## Testing & Simulation

| # | Task | Priority |
|---|------|----------|
| 1 | Build flood event simulator (Python script that generates realistic time-series) | HIGH |
| 2 | Build AQI spike simulator | HIGH |
| 3 | Build fire event simulator | MEDIUM |
| 4 | Build MQTT fake publisher (simulates gateway sending data — for testing backend without hardware) | HIGH |
| 5 | Write unit tests for backend API endpoints | MEDIUM |
| 6 | Write unit tests for ML model inference pipeline | MEDIUM |
| 7 | Integration test: simulator → MQTT → backend → database → dashboard | HIGH |
| 8 | Test LoRa communication reliability (packet loss rate) | MEDIUM |
| 9 | Test edge inference accuracy on ESP32 (compare with cloud model output) | HIGH |
| 10 | Test alert delivery (does SMS/push actually arrive?) | MEDIUM |
| 11 | Load test: simulate 50 nodes sending data simultaneously | LOW |
| 12 | Test offline mode: disconnect gateway internet, verify local alerts still work | MEDIUM |
| 13 | Demo dry run — full end-to-end test mimicking SIH demo | HIGH |

