# AI-Integrated Real-Time Environmental Hazard Prediction

## Low-Cost Sensor Selection, AI-Processable Outputs and ESP32 Architecture

---

## 1. Design Constraint

The complete sensor network is designed around a strict hardware cost target:

> **Individual sensor/module cost: preferably below ₹800, with an absolute target of approximately ₹1,000 per sensor.**

All selected sensors must provide an electrically processable output such as:

- I²C
- SPI
- UART
- GPIO/Pulse
- PWM
- Analog voltage

The ESP32 will acquire the data, perform filtering and feature extraction locally, and transmit the resulting data to the backend AI system.

### Important limitation

At this price range, some measurements cannot be performed accurately using professional environmental sensors.

Therefore, the prototype will use:

**Low-cost sensor → ESP32 → calibration/filtering → derived feature → AI model**

rather than assuming that every inexpensive sensor provides laboratory-grade measurements.

---

# 2. Rising Water Level and Flash Flooding

### Required sensors

| Parameter            | Low-Cost Sensor                 | Interface        | AI-Processable Output       | Approx. Robu Price |
| -------------------- | ------------------------------- | ---------------- | --------------------------- | -----------------: |
| Water level          | Waterproof ultrasonic sensor    | GPIO/Pulse       | Distance → water level (cm) |           **₹350** |
| Rain detection       | Rain sensor module              | Analog + Digital | Rain intensity indicator    |            **₹50** |
| Soil moisture        | Capacitive/soil moisture module | Analog           | Soil moisture index (%)     |            **₹50** |
| Temperature          | SHT31                           | I²C              | Temperature °C              |           **₹220** |
| Humidity             | SHT31                           | I²C              | Relative humidity %         |           **₹220** |
| Atmospheric pressure | BME280                          | I²C/SPI          | Pressure hPa                |          **₹1000** |
| Water flow           | YF-S201 Water Flow Sensor       | Pulse            | Flow rate L/min             |           **₹200** |

### AI inputs

The ESP32 should not simply send:

```text
water_level = 120 cm
```

It should calculate:

```text
water_level
water_level_rate
water_level_acceleration
rain_detected
rain_intensity
soil_moisture
flow_rate
temperature
humidity
pressure
```

### Example

```text
Water level:
100 cm → 103 cm → 108 cm → 116 cm → 128 cm

ESP32 calculates:

Level = 128 cm
Rate = increasing
Acceleration = increasing
```

This is much more useful to the AI model.

### Sensor-to-ESP32 architecture

```text
                 FLOOD NODE
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ↓             ↓             ↓
Water Level      Rain Sensor   Flow Sensor
Ultrasonic          ADC/GPIO       Pulse
       │             │             │
       └─────────────┼─────────────┘
                     ↓
                   ESP32
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
     Soil Moisture  SHT31     BME280
         ADC         I²C        I²C
          │          │          │
          └──────────┼──────────┘
                     ↓
              Data Filtering
                     ↓
            Rate-of-Change Analysis
                     ↓
              Flood-Risk Features
                     ↓
                AI Backend
```

### Recommended low-cost implementation

**Water level + rain + soil moisture + temperature/humidity + pressure**

This is the best balance between cost and useful AI data.

---

# 3. Forest Fire and Smoke Events

A strict ₹1,000 limit means that a thermal camera such as MLX90640 must be removed from the first prototype.

Instead, use multiple inexpensive sensors and allow the AI model to perform sensor fusion.

### Required sensors

| Parameter               | Low-Cost Sensor      | Interface        | AI-Processable Output    | Approx. Price |
| ----------------------- | -------------------- | ---------------- | ------------------------ | ------------: |
| Temperature             | SHT31                | I²C              | °C                       |      **₹220** |
| Humidity                | SHT31                | I²C              | %RH                      |      **₹220** |
| Smoke / combustible gas | MQ-2                 | Analog + Digital | Gas/smoke response       |      **₹100** |
| General air pollution   | MQ-135               | Analog + Digital | Air-quality response     |      **₹150** |
| Flame                   | IR flame sensor      | Digital/Analog   | Flame intensity/presence |       **₹50** |
| Light intensity         | LDR module           | Analog           | Light intensity index    |       **₹50** |
| Soil moisture           | Soil moisture sensor | Analog           | Moisture %/index         |       **₹50** |

### AI inputs

```text
temperature
humidity
MQ2_raw
MQ135_raw
flame_intensity
light_intensity
soil_moisture
```

Derived features:

```text
temperature_rise_rate
humidity_drop_rate
smoke_rise_rate
gas_anomaly
flame_probability
dryness_index
fire_risk_score
```

### Why multiple cheap sensors?

A single MQ-2 sensor can easily produce false positives.

For example:

```text
MQ-2 high
      +
temperature normal
      +
humidity normal
      +
flame = 0
      +
soil moisture high
      ↓
probably NOT fire
```

But:

```text
MQ-2 increasing
      +
MQ-135 increasing
      +
temperature increasing
      +
humidity decreasing
      +
flame signal detected
      ↓
HIGH FIRE PROBABILITY
```

This is exactly where your AI/sensor-fusion approach becomes useful.

### Sensor-to-ESP32 architecture

```text
                  FIRE NODE
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
      SHT31         MQ-2         MQ-135
     Temp/RH       Smoke/Gas     Air Quality
       I²C           ADC            ADC
       │             │              │
       └─────────────┼──────────────┘
                     ↓
                   ESP32
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
      Flame Sensor   LDR    Soil Moisture
        ADC/GPIO      ADC        ADC
          │           │           │
          └───────────┼───────────┘
                      ↓
              Sensor Fusion
                      ↓
             Fire-Risk Features
                      ↓
                 AI Model
```

### Important limitation

**MQ sensors should be treated as relative/anomaly sensors, not accurate ppm instruments.**

Their raw analog response can still be very useful for AI if the system is calibrated against known environmental conditions.

---

# 4. Extreme Heat Conditions

This category is comparatively easy to implement cheaply.

### Required sensors

| Parameter             | Sensor     | Interface | AI Output             | Approx. Price |
| --------------------- | ---------- | --------- | --------------------- | ------------: |
| Temperature           | SHT31      | I²C       | °C                    |      **₹220** |
| Humidity              | SHT31      | I²C       | %RH                   |      **₹220** |
| Atmospheric pressure  | BME280     | I²C/SPI   | hPa                   |     **₹1000** |
| Light/solar intensity | LDR module | Analog    | Light intensity index |       **₹50** |
| UV intensity          | GUVA-S12SD | Analog    | UV intensity          |      **₹300** |

Robu currently lists the DFRobot GUVA-S12SD analog UV sensor at ₹619.

### AI inputs

```text
temperature
humidity
pressure
light_intensity
UV_index
wind_speed
```

The software can calculate:

```text
heat_index
dew_point
wet_bulb_temperature
temperature_rise_rate
humidity_drop_rate
heat_stress_score
```

### Sensor-to-ESP32 architecture

```text
                HEAT NODE
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
      SHT31       BME280       LDR
     Temp/RH     Pressure      Light
        I²C        I²C          ADC
        │           │            │
        └───────────┼────────────┘
                    ↓
                  ESP32
                    │
             ┌──────┴──────┐
             ↓             ↓
          GUVA-S12SD    Anemometer
             UV         Wind Speed
             │             │
             └──────┬──────┘
                    ↓
             Feature Extraction
                    ↓
       Heat Index / Wet Bulb / UV
                    ↓
                AI Model
```

---

# 5. Landslide Prediction

This category requires special treatment.

Professional pore-pressure and displacement sensors are far above the ₹1,000 limit. Therefore, the low-cost prototype will monitor **precursor variables** rather than directly measuring every geotechnical parameter.

### Required sensors

| Parameter            | Low-Cost Sensor                  | Interface | AI Output                | Approx. Price |
| -------------------- | -------------------------------- | --------- | ------------------------ | ------------: |
| Rainfall             | Rain sensor / DIY tipping bucket | GPIO/ADC  | Rain intensity/index     |       **₹50** |
| Soil moisture        | Capacitive soil moisture sensor  | ADC       | Moisture index           |       **₹50** |
| Soil temperature     | DS18B20                          | 1-Wire    | °C                       |   **₹57–₹83** |
| Ground tilt          | ADXL345                          | I²C/SPI   | X/Y/Z acceleration, tilt |      **₹300** |
| Ground vibration     | ADXL345                          | I²C/SPI   | vibration/acceleration   |      **₹300** |
| Atmospheric pressure | BME280                           | I²C/SPI   | hPa                      |     **₹1000** |
| Water level          | Waterproof ultrasonic sensor     | GPIO      | Water level              |      **₹350** |

Robu currently lists the DFRobot ADXL345 at ₹689, the waterproof DS18B20 around ₹779, and BME280 variants around ₹459–₹539.

### AI inputs

```text
rainfall
soil_moisture
soil_temperature
tilt_x
tilt_y
tilt_z
vibration
water_level
pressure
```

Derived features:

```text
soil_moisture_rate
rainfall_accumulation
tilt_rate
tilt_acceleration
vibration_energy
water_level_rate
slope_instability_score
```

### Very important

For landslides, **tilt rate is more valuable than simply knowing the current tilt**.

Example:

```text
Day 1:  0.5°
Day 2:  0.6°
Day 3:  0.8°
Day 4:  1.2°
Day 5:  2.1°
```

The AI should recognize the increasing deformation trend.

### Sensor-to-ESP32 architecture

```text
               LANDSLIDE NODE
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   Rain Sensor   Soil Moisture   DS18B20
      ADC/GPIO        ADC         1-Wire
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                    ESP32
                      │
              ┌───────┴───────┐
              ↓               ↓
           ADXL345          BME280
        Tilt/Vibration     Pressure
           I²C/SPI           I²C
              │               │
              └───────┬───────┘
                      ↓
              Trend Analysis
                      ↓
             Ground Movement
                Features
                      ↓
            Landslide AI Model
```

### Limitation

This low-cost system **cannot replace a professional geotechnical monitoring system**. It is suitable for research/prototype AI development and early-warning experimentation.

---

# 6. Industrial Emissions / Chemical Leaks

With the ₹1,000 limit, the practical approach is to use **MQ-series gas sensors**.

These should be treated as **gas-response/anomaly sensors**, not industrial-grade ppm instruments.

### Required sensors

| Gas / Parameter                | Sensor | Interface | AI Output            | Approx. Price |
| ------------------------------ | ------ | --------- | -------------------- | ------------: |
| Smoke / LPG / methane response | MQ-2   | ADC       | Raw gas response     |      **₹100** |
| CO / combustible gases         | MQ-7   | ADC       | CO-related response  |      **₹500** |
| General air quality            | MQ-135 | ADC       | Air-quality response |      **₹150** |
| H₂S                            | MQ-136 | ADC       | H₂S-related response |     **₹1050** |
| NH₃                            | MQ-137 | ADC       | NH₃-related response |     **₹1200** |
| Temperature                    | SHT31  | I²C       | °C                   |      **₹220** |
| Humidity                       | SHT31  | I²C       | %RH                  |      **₹220** |
| Pressure                       | BME280 | I²C       | hPa                  |     **₹1000** |

### AI inputs

```text
MQ2
MQ7
MQ135
MQ136
MQ137
temperature
humidity
pressure
```

The AI can derive:

```text
gas_anomaly
gas_rise_rate
multi_gas_anomaly
baseline_deviation
environmental_compensation
chemical_leak_probability
```

### Sensor-to-ESP32 architecture

```text
              INDUSTRIAL NODE
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
      MQ-2          MQ-7         MQ-135
    Gas/Smoke         CO        Air Quality
       ADC            ADC           ADC
       │              │             │
       └──────────────┼─────────────┘
                      ↓
                  ESP32-S3
                      │
              ┌───────┼───────┐
              ↓       ↓       ↓
           MQ-136   MQ-137   SHT31
            H2S       NH3    Temp/RH
              │       │       │
              └───────┼───────┘
                      ↓
              Gas Sensor Fusion
                      ↓
              Anomaly Detection
                      ↓
          Chemical Leak Probability
                      ↓
                  AI Backend
```

### Important limitation

Do **not** label an MQ sensor's raw ADC value directly as an accurate ppm value.

Instead use:

```text
MQ2_raw
MQ7_raw
MQ135_raw
...
```

and let calibration + machine learning map these measurements to:

```text
normal
abnormal
possible leak
high-risk leak
```

This is much more defensible for a student/research prototype.

---

# 7. Water Quality Degradation

This category also needs to be simplified because professional dissolved-oxygen, nitrate and ammonia sensors exceed the budget.

### Low-cost sensor set

| Parameter           | Sensor                       | Interface      | AI Output                               |   Approx. Price |
| ------------------- | ---------------------------- | -------------- | --------------------------------------- | --------------: |
| TDS                 | Low-cost TDS sensor          | Analog         | TDS ppm                                 |        **₹500** |
| Water temperature   | DS18B20 waterproof           | 1-Wire         | °C                                      |         **₹60** |
| Water level         | Waterproof ultrasonic sensor | GPIO           | cm/m                                    |        **₹350** |
| Water presence/leak | Water detection sensor       | Digital/Analog | Water presence/index                    |         **₹50** |

### AI inputs

```text
pH
turbidity
TDS
water_temperature
water_level
```

Derived features:

```text
pH_change_rate
turbidity_change_rate
TDS_change_rate
temperature_change
water_level_change
water_quality_anomaly
```

### Sensor-to-ESP32 architecture

```text
              WATER QUALITY NODE
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
       pH          Turbidity          TDS
      ADC             ADC             ADC
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                     ESP32
                       │
              ┌────────┴────────┐
              ↓                 ↓
           DS18B20        Water Level
          Temperature       Ultrasonic
              │                 │
              └────────┬────────┘
                       ↓
                Data Filtering
                       ↓
              Feature Extraction
                       ↓
            Water Quality Index
                       ↓
                  AI Model
```


---

# 9. Sensor Sharing Between Nodes

A major cost-saving strategy is to **reuse sensors that measure common environmental parameters**.

For example:

```text
                 SHT31
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
      FLOOD       FIRE       HEAT
        │          │          │
        └──────────┼──────────┘
                   ↓
              Temp + RH
```

Similarly:

```text
BME280
  │
  ├── Flood
  ├── Fire
  ├── Heat
  ├── Landslide
  └── Industrial
```

This avoids buying a separate temperature/humidity/pressure sensor for every node if the nodes are physically close enough.

---

# 10. Recommended ESP32 Nodes

## Node 1 — Flood

```text
ESP32
 │
 ├── Waterproof Ultrasonic
 ├── Rain Sensor
 ├── Soil Moisture
 ├── Flow Sensor
 ├── SHT31
 └── BME280
```

## Node 2 — Forest Fire

```text
ESP32
 │
 ├── SHT31
 ├── MQ-2
 ├── MQ-135
 ├── Flame Sensor
 ├── LDR
 └── Soil Moisture
```

## Node 3 — Extreme Heat

```text
ESP32
 │
 ├── SHT31
 ├── BME280
 ├── GUVA-S12SD
 ├── LDR
 └── Anemometer
```

## Node 4 — Landslide

```text
ESP32
 │
 ├── Rain Sensor
 ├── Soil Moisture
 ├── DS18B20
 ├── ADXL345
 ├── BME280
 └── Water Level Sensor
```

## Node 5 — Industrial Emission

```text
ESP32-S3
 │
 ├── MQ-2
 ├── MQ-7
 ├── MQ-135
 ├── MQ-136
 ├── MQ-137
 └── SHT31
```

## Node 6 — Water Quality

```text
ESP32
 │
 ├── pH Sensor
 ├── Turbidity Sensor
 ├── TDS Sensor
 ├── DS18B20
 └── Water Level Sensor
```

---

# 11. Overall System

```text
                         ENVIRONMENT
                              │
       ┌──────────────┬───────┴────────┬──────────────┐
       ↓              ↓                ↓              ↓
     FLOOD           FIRE             HEAT         LANDSLIDE
     ESP32          ESP32            ESP32           ESP32
       │              │                │               │
       └──────────────┴────────────────┴───────────────┘
                              │
                              ↓
                       LOCAL NETWORK
                     Wi-Fi / ESP-NOW /
                         LoRa later
                              │
                              ↓
                         EDGE GATEWAY
                     Raspberry Pi / PC
                              │
                ┌─────────────┴─────────────┐
                ↓                           ↓
          Raw Data Storage             Edge Processing
                │                           │
                ↓                           ↓
          Time-Series DB             Feature Extraction
                                            │
                                            ↓
                                     Local Anomaly Model
                                            │
                ┌───────────────────────────┘
                ↓
             AI SERVER
                │
      ┌─────────┼──────────┬──────────┐
      ↓         ↓          ↓          ↓
    Flood      Fire      Landslide   Heat
    Model      Model       Model     Model
      │         │          │          │
      └─────────┼──────────┴──────────┘
                ↓
          Risk Prediction
                │
                ↓
           Alert System
                │
                ↓
        Web / Mobile Dashboard
```

---

# 12. Recommended AI Dataset Structure

Each ESP32 should generate timestamped records.

Example:

```text
timestamp
node_id

temperature
humidity
pressure

rainfall
soil_moisture
water_level
flow_rate

MQ2
MQ7
MQ135
MQ136
MQ137

tilt_x
tilt_y
tilt_z
vibration

pH
turbidity
TDS
water_temperature

battery_voltage
RSSI
sensor_status
```

Then calculate additional features:

```text
temperature_rate
humidity_rate
water_level_rate
rainfall_accumulation
soil_moisture_rate
gas_rate
tilt_rate
vibration_level
pH_rate
TDS_rate
turbidity_rate
```

These become the input features for the AI model.

---

# 13. What the AI Should Predict

The system should preferably predict **risk probabilities**, not simply sensor thresholds.

### Flood

```text
Flood probability in next 30 min = 82%
```

### Fire

```text
Fire probability in next 15 min = 74%
```

### Heat

```text
Extreme heat probability = 91%
```

### Landslide

```text
Landslide probability in next 2 hours = 63%
```

### Industrial leak

```text
Gas anomaly probability = 87%
```

### Water quality

```text
Water degradation probability = 78%
```

---