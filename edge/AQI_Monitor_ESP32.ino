/*
  ================================================================
  ESP32 AQI MONITORING NODE
  Sensors : SHT31 (Temp/Hum) + BME280 (Pressure) + MQ-7 (CO)
  Simulated (random, safe-range): Windspeed, PM2.5, PM10
  Inference: On-device TFLite model (AQI_predict_model_final.tflite)
  Comms   : LoRa SX1278 (raw data + alert flag)
  ================================================================

  REQUIRED LIBRARIES (Arduino Library Manager):
    1. Adafruit SHT31 Library      (Adafruit)
    2. Adafruit BME280 Library     (Adafruit)  + Adafruit Unified Sensor
    3. LoRa                        (Sandeep Mistry)
    4. ArduTFLite                  -- TensorFlow Lite Micro for Arduino

  FILE STRUCTURE (place both files in the same sketch folder):
    AQI_Monitor_ESP32.ino
    model_data.h
  ================================================================
*/

#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_SHT31.h>
#include <Adafruit_BME280.h>
#include <LoRa.h>
#include <esp_system.h>

#include <ArduTFLite.h>
#include "model_data.h"

/* ================= PIN DEFINITIONS ================= */
// I2C (SHT31 + BME280)
#define I2C_SDA         21
#define I2C_SCL         22

// MQ-7 analog output
#define MQ7_PIN         34      // ADC1_CH6, input-only pin

// LoRa SX1278 (SPI - VSPI default pins)
#define LORA_SCK        18
#define LORA_MISO       19
#define LORA_MOSI       23
#define LORA_NSS        5
#define LORA_RST        14
#define LORA_DIO0       26
#define LORA_BAND       433E6  // change to 868E6 / 915E6 as per your module region

/* ================= SENSOR I2C ADDRESSES ================= */
#define SHT31_ADDR      0x44
#define BME280_ADDR     0x76    // use 0x77 if your module uses that address

/* ================= DATASET MIN/MAX (from AQI_Predict.ipynb df.describe()) =================
   Used to clamp/map every raw sensor reading into the range the model was trained on.        */
const float TEMP_MIN   = 5.7,    TEMP_MAX   = 43.8;    // deg C
const float HUM_MIN    = 5.0,    HUM_MAX    = 100.0;   // %
const float PRES_MIN   = 966.1,  PRES_MAX   = 998.8;   // mb (hPa)
const float WIND_MIN   = 0.0,    WIND_MAX   = 27.1;    // kph
const float PM25_MIN   = 6.0,    PM25_MAX   = 443.3;   // ug/m3
const float PM10_MIN   = 6.1,    PM10_MAX   = 3263.4;  // ug/m3
const float CO_MIN     = 146.0,  CO_MAX     = 7432.0;  // (dataset "co" units)

/* ================= SAFE-RANGE SIMULATION BOUNDS =================
   Adjustable "safe" sub-ranges used ONLY for the parameters with no
   physical sensor (windspeed, PM2.5, PM10) - random values are drawn
   from within these bounds and are additionally clamped to the
   dataset min/max above before being fed to the model.             */
const float SIM_WIND_MIN = 0.0,   SIM_WIND_MAX = 15.0;   // calm - breezy
const float SIM_PM25_MIN = 10.0,  SIM_PM25_MAX = 60.0;   // Good - Satisfactory
const float SIM_PM10_MIN = 20.0,  SIM_PM10_MAX = 100.0;  // Good - Satisfactory

/* ================= MQ-7 CALIBRATION (simplified linear map) =================
   Replace with a proper Rs/Ro MQ-7 curve calibration for production use.     */
const int   MQ7_ADC_MIN = 0;
const int   MQ7_ADC_MAX = 4095;   // ESP32 ADC resolution (12-bit)

/* ================= AQI MODEL / DECISION THRESHOLD ================= */
#define AQI_THRESHOLD   0.159f    // output[1] (P(unsafe)) >= threshold -> ALERT

/* ================= TIMING ================= */
const unsigned long SENSOR_READ_INTERVAL = 2000UL;     // read + infer + print every 2 s
const unsigned long LORA_NORMAL_INTERVAL = 1UL * 60UL * 1000UL; // 1 min (no alert)
const unsigned long LORA_ALERT_INTERVAL  = 30UL * 1000UL;       // 30 s (alert active)

/* ================= TFLITE MODEL CONFIG ================= */
#define N_INPUTS        7
#define N_OUTPUTS       2
#define TENSOR_ARENA_SIZE  8 * 1024

uint8_t tensorArena[TENSOR_ARENA_SIZE] __attribute__((aligned(16)));

/* ================= SENSOR OBJECTS ================= */
Adafruit_SHT31   sht31   = Adafruit_SHT31();
Adafruit_BME280  bme280;

/* ================= GLOBALS ================= */
unsigned long lastSensorRead = 0;
unsigned long lastLoRaSend   = 0;
bool alertActive = false;

/* ================================================================
   HELPER FUNCTIONS
   ================================================================ */

float clampf(float value, float minVal, float maxVal) {
  if (value < minVal) return minVal;
  if (value > maxVal) return maxVal;
  return value;
}

// Uniform random float in [minVal, maxVal] using ESP32 hardware RNG
float randomFloatInRange(float minVal, float maxVal) {
  uint32_t r = esp_random();
  float frac = (float)r / (float)UINT32_MAX;
  return minVal + frac * (maxVal - minVal);
}

// Arduino map() equivalent for floats
float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Reads MQ-7 analog pin and maps raw ADC counts to dataset CO range
float readMQ7_CO() {
  int raw = analogRead(MQ7_PIN);
  float co = mapFloat((float)raw, (float)MQ7_ADC_MIN, (float)MQ7_ADC_MAX, CO_MIN, CO_MAX);
  return clampf(co, CO_MIN, CO_MAX);
}

/* ================================================================
   SETUP
   ================================================================ */
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n===== ESP32 AQI MONITORING NODE BOOTING ====="));

  analogReadResolution(12);      // 0-4095
  analogSetAttenuation(ADC_11db); // full 0-3.3V range

  /* ---- I2C SENSORS ---- */
  Wire.begin(I2C_SDA, I2C_SCL);

  if (!sht31.begin(SHT31_ADDR)) {
    Serial.println(F("[ERROR] SHT31 not found. Check wiring."));
  } else {
    Serial.println(F("[OK] SHT31 initialized."));
  }

  if (!bme280.begin(BME280_ADDR, &Wire)) {
    Serial.println(F("[ERROR] BME280 not found. Check wiring/address."));
  } else {
    Serial.println(F("[OK] BME280 initialized."));
  }

  /* ---- LoRa SX1278 ---- */
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  LoRa.setPins(LORA_NSS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_BAND)) {
    Serial.println(F("[ERROR] LoRa init failed. Check wiring/band."));
    while (1) delay(1000);
  }
  Serial.println(F("[OK] LoRa initialized."));

  /* ---- TFLite model ---- */
  if (!modelInit(aqi_model_data, tensorArena, TENSOR_ARENA_SIZE)) {
    Serial.println(F("[ERROR] TFLite init failed."));
    while (1) delay(1000);
  }

  Serial.println(F("[OK] TFLite AQI model loaded."));

  randomSeed(esp_random());
  Serial.println(F("===== SETUP COMPLETE =====\n"));
}

/* ================================================================
   LOOP
   ================================================================ */
void loop() {
  unsigned long now = millis();

  if (now - lastSensorRead >= SENSOR_READ_INTERVAL) {
    lastSensorRead = now;

    /* ---------- 1. READ / GENERATE RAW VALUES ---------- */
    float temp_c   = sht31.readTemperature();
    float humidity = sht31.readHumidity();
    float pressure_mb = bme280.readPressure() / 100.0F;   // Pa -> mb(hPa)

    float windspeed_kph = randomFloatInRange(SIM_WIND_MIN, SIM_WIND_MAX);
    float pm2_5          = randomFloatInRange(SIM_PM25_MIN, SIM_PM25_MAX);
    float pm10            = randomFloatInRange(SIM_PM10_MIN, SIM_PM10_MAX);
    float co               = readMQ7_CO();

    // Handle NaN from sensor read failures
    if (isnan(temp_c))   temp_c   = TEMP_MIN;
    if (isnan(humidity)) humidity = HUM_MIN;
    if (isnan(pressure_mb)) pressure_mb = PRES_MIN;

    /* ---------- 2. MAP / CLAMP TO DATASET MIN-MAX (from .ipynb) ---------- */
    temp_c        = clampf(temp_c,        TEMP_MIN, TEMP_MAX);
    humidity      = clampf(humidity,      HUM_MIN,  HUM_MAX);
    pressure_mb   = clampf(pressure_mb,   PRES_MIN, PRES_MAX);
    windspeed_kph = clampf(windspeed_kph, WIND_MIN, WIND_MAX);
    pm2_5         = clampf(pm2_5,         PM25_MIN, PM25_MAX);
    pm10          = clampf(pm10,          PM10_MIN, PM10_MAX);
    co            = clampf(co,            CO_MIN,   CO_MAX);

    /* ---------- 3. RUN TFLITE INFERENCE ---------- */
    float input[N_INPUTS] = { temp_c, humidity, pressure_mb, windspeed_kph, pm2_5, pm10, co };
    float output[N_OUTPUTS] = { 0 };

    bool inputOK = true;
    for (int i = 0; i < N_INPUTS; i++) {
      if (!modelSetInput(input[i], i)) {
        inputOK = false;
        break;
      }
    }

    if (!inputOK) {
      Serial.println(F("[ERROR] Failed to set TFLite input."));
      return;
    }

    if (!modelRunInference()) {
      Serial.println(F("[ERROR] TFLite inference failed."));
      return;
    }

    float probSafe   = modelGetOutput(0);
    float probUnsafe = modelGetOutput(1);
    alertActive = (probUnsafe >= AQI_THRESHOLD);

    /* ---------- 4. SERIAL MONITOR OUTPUT ---------- */
    Serial.println(F("----------------------------------------------------"));
    Serial.printf("Temp(C): %.2f | Humidity(%%): %.2f | Pressure(mb): %.2f\n",
                  temp_c, humidity, pressure_mb);
    Serial.printf("Windspeed(kph): %.2f | PM2.5: %.2f | PM10: %.2f | CO: %.2f\n",
                  windspeed_kph, pm2_5, pm10, co);
    Serial.printf("Model -> P(Safe): %.4f | P(Unsafe): %.4f | Threshold: %.3f\n",
                  probSafe, probUnsafe, AQI_THRESHOLD);
    Serial.println(alertActive ? F(">>> STATUS: ALERT (UNSAFE AIR QUALITY) <<<")
                                : F(">>> STATUS: SAFE <<<"));

    /* ---------- 5. LoRa TRANSMISSION (interval depends on alert state) ---------- */
    unsigned long loraInterval = alertActive ? LORA_ALERT_INTERVAL : LORA_NORMAL_INTERVAL;

    if (now - lastLoRaSend >= loraInterval) {
      lastLoRaSend = now;

      char packet[160];
      snprintf(packet, sizeof(packet),
               "T:%.1f,H:%.1f,P:%.1f,WS:%.1f,PM2.5:%.1f,PM10:%.1f,CO:%.1f,PU:%.3f,ALERT:%d",
               temp_c, humidity, pressure_mb, windspeed_kph, pm2_5, pm10, co,
               probUnsafe, alertActive ? 1 : 0);

      LoRa.beginPacket();
      LoRa.print(packet);
      LoRa.endPacket();

      Serial.print(F("[LoRa TX] "));
      Serial.println(packet);
    }
    Serial.println(F("----------------------------------------------------\n"));
  }
}
