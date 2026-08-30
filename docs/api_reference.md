# Lookout Grid — API Reference

**Base URL:** `https://api.lookoutgrid.com/v1` or `http://localhost:8000/v1`

**Content Type:** All request and response bodies are `application/json`.

**Authentication:** Endpoints marked 🔒 require a valid JWT token in the `Authorization: Bearer <token>` header. Role restrictions are noted per-endpoint.

---

## Table of Contents

1. [Standardized Error Response](#1-standardized-error-response)
2. [Enums & Constants](#2-enums--constants)
3. [Auth & Users](#3-auth--users)
4. [Node Management](#4-node-management)
5. [Gateway Management](#5-gateway-management)
6. [Sensor Data Ingestion & Query](#6-sensor-data-ingestion--query)
7. [Alerts](#7-alerts)
8. [ML Model / Prediction](#8-ml-model--prediction)
9. [GIS & Risk Mapping](#9-gis--risk-mapping)
10. [Analytics & Dashboard](#10-analytics--dashboard)
11. [Real-time (WebSocket)](#11-real-time-websocket)
12. [System / Admin](#12-system--admin)

---

## 1. Standardized Error Response

Every error from every endpoint follows this exact shape:

```json
{
  "detail": "Human-readable error message describing what went wrong",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-08-24T13:00:00.000+05:30"
}
```

**Error Codes:**

| HTTP Status | `error_code` | When It Occurs |
|-------------|-------------|----------------|
| 400 | `BAD_REQUEST` | Malformed JSON, missing required field, value out of valid range |
| 401 | `UNAUTHORIZED` | Missing or expired JWT token |
| 403 | `FORBIDDEN` | Valid token but user's role lacks permission for this endpoint |
| 404 | `NOT_FOUND` | The requested resource (node, gateway, alert, user) does not exist |
| 409 | `CONFLICT` | Trying to register a node_id or email that already exists |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure — field type mismatch, string too long, etc. |
| 429 | `RATE_LIMITED` | Too many requests from this client (when rate limiting is enabled) |
| 500 | `INTERNAL_ERROR` | Unhandled server exception — database down, MQTT publish failed, etc. |
| 503 | `MQTT_PUBLISH_FAILED` | Backend could not forward a command/message to the MQTT broker |

---

## 2. Enums & Constants

These are the allowed string values for enum-like fields across all endpoints. Sending a value outside these sets will return a `422 VALIDATION_ERROR`.

| Field | Allowed Values |
|-------|---------------|
| `node_type` | `FLOOD`, `AIR_QUALITY`, `FIRE`, `MULTI` |
| `alert_level` | `GREEN`, `YELLOW`, `ORANGE`, `RED` |
| `alert_type` | `FLOOD`, `AIR_QUALITY`, `FIRE`, `EXTREME_HEAT`, `LANDSLIDE`, `INDUSTRIAL_LEAK`, `WATER_CONTAMINATION` |
| `alert_status` | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM` |
| `alert_source` | `EDGE`, `GATEWAY`, `CLOUD` |
| `model_layer` | `EDGE`, `GATEWAY`, `CLOUD` |
| `node_status` | `ACTIVE`, `INACTIVE`, `MAINTENANCE` |
| `gateway_connectivity` | `4G`, `WIFI`, `ETHERNET` |
| `power_source` | `SOLAR`, `BATTERY`, `MAINS` |
| `communication` | `LORA`, `BLE`, `WIFI`, `ESPNOW` |
| `user_role` | `ADMIN`, `AUTHORITY`, `OPERATOR`, `CITIZEN` |
| `command_type` | `UPDATE_MODEL`, `UPDATE_CONFIG`, `RESTART`, `CALIBRATE`, `SLEEP`, `WAKE`, `FACTORY_RESET` |
| `notification_channel` | `SMS`, `PUSH`, `EMAIL`, `WHATSAPP` |

---

## 3. Auth & Users

### `POST /auth/register`
**Auth:** None (public)

**Request Body:**
```json
{
  "email": "officer@patna.gov.in",
  "password": "securepassword123",
  "full_name": "Rajesh Kumar",
  "phone": "+919876543210",
  "role": "AUTHORITY",
  "organization": "District Administration, Patna"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | ✅ | Must be a valid email, unique across all users |
| `password` | string | ✅ | Minimum 8 characters |
| `full_name` | string | ✅ | Max 100 characters |
| `phone` | string | ❌ | E.164 format (`+91XXXXXXXXXX`), max 15 chars |
| `role` | string | ✅ | One of: `ADMIN`, `AUTHORITY`, `OPERATOR`, `CITIZEN` |
| `organization` | string | ❌ | Max 200 characters |

**Response `201 Created`:**
```json
{
  "user_id": 1,
  "email": "officer@patna.gov.in",
  "full_name": "Rajesh Kumar",
  "phone": "+919876543210",
  "role": "AUTHORITY",
  "organization": "District Administration, Patna",
  "created_at": "2026-08-24T13:00:00.000+05:30"
}
```

**Errors:** `409 CONFLICT` if email already exists.

---

### `POST /auth/login`
**Auth:** None (public)

**Request Body:**
```json
{
  "email": "officer@patna.gov.in",
  "password": "securepassword123"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in_minutes": 30
}
```

**Errors:** `401 UNAUTHORIZED` if email not found or password incorrect.

---

### `POST /auth/refresh`
**Auth:** None (but requires a valid refresh token in body)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...(new)...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...(new)...",
  "token_type": "bearer",
  "expires_in_minutes": 30
}
```

**Errors:** `401 UNAUTHORIZED` if refresh token is invalid or expired.

---

### `GET /users/me`
**Auth:** 🔒 Any authenticated user

**Response `200 OK`:**
```json
{
  "user_id": 1,
  "email": "officer@patna.gov.in",
  "full_name": "Rajesh Kumar",
  "phone": "+919876543210",
  "role": "AUTHORITY",
  "organization": "District Administration, Patna",
  "alert_preferences": {
    "channels": ["SMS", "PUSH"],
    "min_level": "ORANGE"
  },
  "created_at": "2026-08-24T13:00:00.000+05:30"
}
```

---

### `PATCH /users/me/preferences`
**Auth:** 🔒 Any authenticated user

**Request Body:**
```json
{
  "alert_preferences": {
    "channels": ["SMS", "PUSH", "EMAIL"],
    "min_level": "YELLOW"
  }
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `alert_preferences.channels` | string[] | ✅ | Each item must be one of: `SMS`, `PUSH`, `EMAIL`, `WHATSAPP` |
| `alert_preferences.min_level` | string | ✅ | One of: `GREEN`, `YELLOW`, `ORANGE`, `RED` |

**Response `200 OK`:**
```json
{
  "message": "Preferences updated",
  "alert_preferences": {
    "channels": ["SMS", "PUSH", "EMAIL"],
    "min_level": "YELLOW"
  }
}
```

---

### `POST /users/me/fcm-token`
**Auth:** 🔒 Any authenticated user

**Request Body:**
```json
{
  "fcm_token": "dGhpcyBpcyBhIGZha2UgdG9rZW4..."
}
```

**Response `200 OK`:**
```json
{
  "message": "FCM token registered"
}
```

---

## 4. Node Management

### `POST /nodes`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR`

**Request Body** (matches Node Registration Packet from `data_schema.md` §1.3):
```json
{
  "node_id": "LG-NODE-PAT-003",
  "node_type": "FLOOD",
  "gateway_id": "LG-GW-PAT-01",
  "location": {
    "lat": 25.6093,
    "lng": 85.1376,
    "altitude_m": 52.3,
    "location_name": "Gandak River - Upstream Sector 3"
  },
  "sensors_installed": ["WATER_LEVEL", "RAINFALL", "TEMPERATURE", "HUMIDITY", "PRESSURE"],
  "firmware_version": "1.2.3",
  "edge_model_version": "flood-v2-q8",
  "power_source": "SOLAR",
  "communication": "LORA",
  "installed_date": "2026-08-20",
  "installed_by": "Abhirup"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `node_id` | string | ✅ | Format: `LG-NODE-{CITY_CODE}-{NNN}`. Max 30 chars. Must be unique. |
| `node_type` | string | ✅ | One of: `FLOOD`, `AIR_QUALITY`, `FIRE`, `MULTI` |
| `gateway_id` | string | ✅ | Must reference an existing gateway in the `gateways` table |
| `location.lat` | float | ✅ | Range: -90.0 to 90.0 |
| `location.lng` | float | ✅ | Range: -180.0 to 180.0 |
| `location.altitude_m` | float | ❌ | |
| `location.location_name` | string | ❌ | Max 200 chars |
| `sensors_installed` | string[] | ✅ | Each item one of: `WATER_LEVEL`, `RAINFALL`, `TEMPERATURE`, `HUMIDITY`, `PRESSURE`, `PM25`, `PM10`, `SMOKE`, `SOIL_MOISTURE`, `TDS`, `WIND_SPEED`, `UV_INDEX`, `CO` |
| `firmware_version` | string | ❌ | Max 20 chars |
| `edge_model_version` | string | ❌ | Max 50 chars |
| `power_source` | string | ❌ | Default: `SOLAR`. One of: `SOLAR`, `BATTERY`, `MAINS` |
| `communication` | string | ❌ | Default: `LORA`. One of: `LORA`, `BLE`, `WIFI`, `ESPNOW` |
| `installed_date` | string (date) | ❌ | Format: `YYYY-MM-DD` |
| `installed_by` | string | ❌ | Free text |

**Response `201 Created`:**
```json
{
  "node_id": "LG-NODE-PAT-003",
  "node_type": "FLOOD",
  "gateway_id": "LG-GW-PAT-01",
  "latitude": 25.6093,
  "longitude": 85.1376,
  "altitude_m": 52.3,
  "location_name": "Gandak River - Upstream Sector 3",
  "sensors": ["WATER_LEVEL", "RAINFALL", "TEMPERATURE", "HUMIDITY", "PRESSURE"],
  "firmware_ver": "1.2.3",
  "edge_model_ver": "flood-v2-q8",
  "power_source": "SOLAR",
  "communication": "LORA",
  "status": "ACTIVE",
  "installed_date": "2026-08-20",
  "last_seen_at": null,
  "created_at": "2026-08-24T13:00:00.000+05:30"
}
```

**Errors:** `409 CONFLICT` if `node_id` already exists. `404 NOT_FOUND` if `gateway_id` doesn't exist.

---

### `GET /nodes`
**Auth:** 🔒 Any authenticated user

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ❌ | Filter by node_type. e.g. `?type=FLOOD` |
| `status` | string | ❌ | Filter by status. e.g. `?status=ACTIVE` |
| `gateway_id` | string | ❌ | Filter by parent gateway. e.g. `?gateway_id=LG-GW-PAT-01` |
| `limit` | int | ❌ | Default: 50. Max: 200. |
| `offset` | int | ❌ | Default: 0. For pagination. |

**Response `200 OK`:**
```json
{
  "total": 24,
  "limit": 50,
  "offset": 0,
  "nodes": [
    {
      "node_id": "LG-NODE-PAT-003",
      "node_type": "FLOOD",
      "gateway_id": "LG-GW-PAT-01",
      "latitude": 25.6093,
      "longitude": 85.1376,
      "altitude_m": 52.3,
      "location_name": "Gandak River - Upstream Sector 3",
      "sensors": ["WATER_LEVEL", "RAINFALL", "TEMPERATURE", "HUMIDITY", "PRESSURE"],
      "firmware_ver": "1.2.3",
      "edge_model_ver": "flood-v2-q8",
      "power_source": "SOLAR",
      "communication": "LORA",
      "status": "ACTIVE",
      "installed_date": "2026-08-20",
      "last_seen_at": "2026-08-24T12:55:30.000+05:30",
      "created_at": "2026-08-20T10:00:00.000+05:30"
    }
  ]
}
```

---

### `GET /nodes/{node_id}`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `node_id` — e.g. `LG-NODE-PAT-003`

**Response `200 OK`:**
Returns the full node record PLUS the most recent sensor reading from the `sensor_readings` table (joined by `node_id`, ordered by `time DESC`, limit 1).

```json
{
  "node_id": "LG-NODE-PAT-003",
  "node_type": "FLOOD",
  "gateway_id": "LG-GW-PAT-01",
  "latitude": 25.6093,
  "longitude": 85.1376,
  "altitude_m": 52.3,
  "location_name": "Gandak River - Upstream Sector 3",
  "sensors": ["WATER_LEVEL", "RAINFALL", "TEMPERATURE", "HUMIDITY", "PRESSURE"],
  "firmware_ver": "1.2.3",
  "edge_model_ver": "flood-v2-q8",
  "power_source": "SOLAR",
  "communication": "LORA",
  "status": "ACTIVE",
  "installed_date": "2026-08-20",
  "last_seen_at": "2026-08-24T12:55:30.000+05:30",
  "created_at": "2026-08-20T10:00:00.000+05:30",
  "latest_reading": {
    "time": "2026-08-24T12:55:30.000+05:30",
    "water_level_m": 2.5,
    "rainfall_mm_hr": 12.5,
    "temperature_c": 28.3,
    "humidity_pct": 94.1,
    "pressure_hpa": 1005.2,
    "pm25_ugm3": null,
    "pm10_ugm3": null,
    "smoke_ppm": null,
    "soil_moisture_pct": null,
    "tds_ppm": null,
    "wind_speed_kmh": null,
    "uv_index": null,
    "co_ugm3": null,
    "battery_pct": 78,
    "solar_charging": true,
    "signal_strength_dbm": -87,
    "anomaly_detected": true,
    "anomaly_score": 0.82,
    "edge_label": "RISING_WATER_FAST"
  }
}
```

**Errors:** `404 NOT_FOUND` if `node_id` doesn't exist. The `latest_reading` field is `null` if the node has never sent data.

---

### `PATCH /nodes/{node_id}`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR`

**Path Parameter:** `node_id`

**Request Body** (all fields optional — only provided fields are updated):
```json
{
  "firmware_ver": "1.3.0",
  "edge_model_ver": "flood-v3-q8",
  "status": "MAINTENANCE",
  "location_name": "Gandak River - Upstream Sector 3 (Relocated)"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `firmware_ver` | string | Max 20 chars |
| `edge_model_ver` | string | Max 50 chars |
| `status` | string | One of: `ACTIVE`, `INACTIVE`, `MAINTENANCE` |
| `location_name` | string | Max 200 chars |
| `latitude` | float | -90.0 to 90.0 |
| `longitude` | float | -180.0 to 180.0 |
| `altitude_m` | float | |
| `power_source` | string | One of: `SOLAR`, `BATTERY`, `MAINS` |
| `communication` | string | One of: `LORA`, `BLE`, `WIFI`, `ESPNOW` |
| `gateway_id` | string | Must reference existing gateway |

**Response `200 OK`:** Returns the full updated node object (same shape as `GET /nodes/{node_id}` but without `latest_reading`).

**Errors:** `404 NOT_FOUND` if `node_id` doesn't exist.

---

### `DELETE /nodes/{node_id}`
**Auth:** 🔒 Roles: `ADMIN`

**Path Parameter:** `node_id`

This is a **soft delete** — it sets `status = 'INACTIVE'` and `updated_at = NOW()`. The node's historical data in `sensor_readings` is preserved.

**Response `200 OK`:**
```json
{
  "message": "Node LG-NODE-PAT-003 decommissioned",
  "node_id": "LG-NODE-PAT-003",
  "status": "INACTIVE"
}
```

**Errors:** `404 NOT_FOUND` if `node_id` doesn't exist.

---

### `GET /nodes/{node_id}/readings`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `node_id`

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | datetime (ISO 8601) | ❌ | 24 hours ago | Start of time range. e.g. `?from=2026-08-23T00:00:00+05:30` |
| `to` | datetime (ISO 8601) | ❌ | now | End of time range |
| `limit` | int | ❌ | 100 | Max rows to return. Max: 1000. |
| `offset` | int | ❌ | 0 | For pagination |

**Response `200 OK`:**
```json
{
  "node_id": "LG-NODE-PAT-003",
  "total": 288,
  "limit": 100,
  "offset": 0,
  "from": "2026-08-23T00:00:00.000+05:30",
  "to": "2026-08-24T13:00:00.000+05:30",
  "readings": [
    {
      "time": "2026-08-24T12:55:30.000+05:30",
      "water_level_m": 2.5,
      "rainfall_mm_hr": 12.5,
      "temperature_c": 28.3,
      "humidity_pct": 94.1,
      "pressure_hpa": 1005.2,
      "pm25_ugm3": null,
      "pm10_ugm3": null,
      "smoke_ppm": null,
      "soil_moisture_pct": null,
      "tds_ppm": null,
      "wind_speed_kmh": null,
      "uv_index": null,
      "co_ugm3": null,
      "battery_pct": 78,
      "solar_charging": true,
      "signal_strength_dbm": -87,
      "anomaly_detected": true,
      "anomaly_score": 0.82,
      "edge_label": "RISING_WATER_FAST"
    }
  ]
}
```

**Note:** Readings are ordered by `time DESC` (most recent first).

---

### `GET /nodes/{node_id}/health`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `node_id`

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | datetime | ❌ | 7 days ago | Start of time range |
| `to` | datetime | ❌ | now | End of time range |
| `interval` | string | ❌ | `1h` | Time bucket interval for aggregation. Accepted values: `5m`, `15m`, `30m`, `1h`, `6h`, `1d` |

This endpoint returns time-bucketed device health metrics by querying `battery_pct`, `solar_charging`, `signal_strength_dbm`, `uptime_seconds`, and `firmware_version` from the `sensor_readings` table, aggregated using TimescaleDB's `time_bucket()`.

**Response `200 OK`:**
```json
{
  "node_id": "LG-NODE-PAT-003",
  "from": "2026-08-17T00:00:00.000+05:30",
  "to": "2026-08-24T13:00:00.000+05:30",
  "interval": "1h",
  "health_history": [
    {
      "bucket": "2026-08-24T12:00:00.000+05:30",
      "avg_battery_pct": 78.2,
      "min_battery_pct": 76,
      "avg_signal_strength_dbm": -85.4,
      "min_signal_strength_dbm": -92,
      "solar_charging": true,
      "readings_count": 12
    },
    {
      "bucket": "2026-08-24T11:00:00.000+05:30",
      "avg_battery_pct": 80.1,
      "min_battery_pct": 79,
      "avg_signal_strength_dbm": -83.2,
      "min_signal_strength_dbm": -88,
      "solar_charging": true,
      "readings_count": 12
    }
  ]
}
```

**SQL pattern used internally:**
```sql
SELECT
  time_bucket(:interval, time) AS bucket,
  AVG(battery_pct)::REAL AS avg_battery_pct,
  MIN(battery_pct) AS min_battery_pct,
  AVG(signal_strength_dbm)::REAL AS avg_signal_strength_dbm,
  MIN(signal_strength_dbm) AS min_signal_strength_dbm,
  BOOL_OR(solar_charging) AS solar_charging,
  COUNT(*) AS readings_count
FROM sensor_readings
WHERE node_id = :node_id
  AND time >= :from_time
  AND time <= :to_time
GROUP BY bucket
ORDER BY bucket DESC
```

---

## 5. Gateway Management

### `POST /gateways`
**Auth:** 🔒 Roles: `ADMIN`

**Request Body:**
```json
{
  "gateway_id": "LG-GW-PAT-01",
  "latitude": 25.6100,
  "longitude": 85.1350,
  "location_name": "Patna Flood Control Office",
  "connectivity": "4G",
  "ml_model_ver": "flood-lstm-v3"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `gateway_id` | string | ✅ | Format: `LG-GW-{CITY_CODE}-{NN}`. Max 30 chars. Must be unique. |
| `latitude` | float | ✅ | -90.0 to 90.0 |
| `longitude` | float | ✅ | -180.0 to 180.0 |
| `location_name` | string | ❌ | Max 200 chars |
| `connectivity` | string | ❌ | Default: `4G`. One of: `4G`, `WIFI`, `ETHERNET` |
| `ml_model_ver` | string | ❌ | Max 50 chars |

**Response `201 Created`:**
```json
{
  "gateway_id": "LG-GW-PAT-01",
  "latitude": 25.6100,
  "longitude": 85.1350,
  "location_name": "Patna Flood Control Office",
  "connectivity": "4G",
  "status": "ACTIVE",
  "ml_model_ver": "flood-lstm-v3",
  "total_nodes": 0,
  "last_heartbeat": null,
  "created_at": "2026-08-24T10:00:00.000+05:30"
}
```

**Errors:** `409 CONFLICT` if `gateway_id` already exists.

---

### `GET /gateways`
**Auth:** 🔒 Any authenticated user

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ❌ | Filter by status. e.g. `?status=ACTIVE` |
| `limit` | int | ❌ | Default: 50 |
| `offset` | int | ❌ | Default: 0 |

**Response `200 OK`:**
```json
{
  "total": 3,
  "limit": 50,
  "offset": 0,
  "gateways": [
    {
      "gateway_id": "LG-GW-PAT-01",
      "latitude": 25.6100,
      "longitude": 85.1350,
      "location_name": "Patna Flood Control Office",
      "connectivity": "4G",
      "status": "ACTIVE",
      "ml_model_ver": "flood-lstm-v3",
      "total_nodes": 8,
      "last_heartbeat": "2026-08-24T12:55:00.000+05:30",
      "created_at": "2026-08-20T10:00:00.000+05:30"
    }
  ]
}
```

---

### `GET /gateways/{gateway_id}`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `gateway_id` — e.g. `LG-GW-PAT-01`

**Response `200 OK`:**
Returns the gateway record plus a count of its connected nodes (active and total).

```json
{
  "gateway_id": "LG-GW-PAT-01",
  "latitude": 25.6100,
  "longitude": 85.1350,
  "location_name": "Patna Flood Control Office",
  "connectivity": "4G",
  "status": "ACTIVE",
  "ml_model_ver": "flood-lstm-v3",
  "total_nodes": 8,
  "active_nodes": 7,
  "last_heartbeat": "2026-08-24T12:55:00.000+05:30",
  "created_at": "2026-08-20T10:00:00.000+05:30"
}
```

`active_nodes` is computed as `SELECT COUNT(*) FROM nodes WHERE gateway_id = :gw_id AND status = 'ACTIVE'`.

**Errors:** `404 NOT_FOUND` if `gateway_id` doesn't exist.

---

### `PATCH /gateways/{gateway_id}`
**Auth:** 🔒 Roles: `ADMIN`

**Request Body** (all fields optional):
```json
{
  "location_name": "Patna Flood Control Office (Relocated)",
  "connectivity": "WIFI",
  "ml_model_ver": "flood-lstm-v4",
  "status": "ACTIVE"
}
```

**Response `200 OK`:** Full updated gateway object.

---

### `GET /gateways/{gateway_id}/nodes`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `gateway_id`

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ❌ | Filter nodes by status |

**Response `200 OK`:**
```json
{
  "gateway_id": "LG-GW-PAT-01",
  "total": 8,
  "nodes": [
    {
      "node_id": "LG-NODE-PAT-001",
      "node_type": "FLOOD",
      "status": "ACTIVE",
      "latitude": 25.6050,
      "longitude": 85.1300,
      "location_name": "Gandak River - Upstream Sector 1",
      "last_seen_at": "2026-08-24T12:55:00.000+05:30"
    }
  ]
}
```

This returns a **summarized** node list (not the full node object — omits sensors, firmware, etc. for performance).

---

### `GET /gateways/{gateway_id}/status`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `gateway_id`

**Response `200 OK`:**
Returns the most recent heartbeat data for this gateway. The data comes from the latest row matching this `gateway_id` in the heartbeat tracking (stored when the backend processes a `GATEWAY_HEARTBEAT` packet received via MQTT).

```json
{
  "gateway_id": "LG-GW-PAT-01",
  "status": "ACTIVE",
  "connectivity": "4G",
  "signal_strength_dbm": -72,
  "cpu_usage_pct": 23,
  "ram_usage_pct": 45,
  "disk_usage_pct": 12,
  "connected_nodes": 8,
  "active_nodes": 7,
  "inactive_nodes": ["LG-NODE-PAT-006"],
  "active_alerts": 1,
  "last_heartbeat": "2026-08-24T12:55:00.000+05:30",
  "last_model_update": "2026-08-20T10:00:00.000+05:30",
  "uptime_since": "2026-08-20T10:00:00.000+05:30"
}
```

**Errors:** `404 NOT_FOUND` if `gateway_id` doesn't exist.

---

## 6. Sensor Data Ingestion & Query

### `POST /data/ingest`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR` (or internal — called by the MQTT subscriber)

**Purpose:** Direct HTTP alternative to MQTT ingestion. Gateways that have HTTP connectivity can use this instead of MQTT. The MQTT subscriber also calls the same internal pipeline.

**Request Body** (matches Sensor Reading Packet from `data_schema.md` §1.1):
```json
{
  "packet_type": "SENSOR_READING",
  "node_id": "LG-NODE-PAT-003",
  "timestamp": "2026-08-24T13:00:00.000+05:30",
  "readings": {
    "water_level_m": 2.5,
    "rainfall_mm_hr": 12.5,
    "temperature_c": 28.3,
    "humidity_pct": 94.1,
    "pressure_hpa": 1005.2,
    "pm25_ugm3": null,
    "pm10_ugm3": null,
    "smoke_ppm": null,
    "soil_moisture_pct": null,
    "tds_ppm": null,
    "wind_speed_kmh": null,
    "uv_index": null,
    "co_ugm3": null
  },
  "device_health": {
    "battery_pct": 78,
    "solar_charging": true,
    "signal_strength_dbm": -87,
    "uptime_seconds": 345600,
    "firmware_version": "1.2.3"
  },
  "edge_inference": {
    "model_version": "flood-v2-q8",
    "anomaly_detected": true,
    "anomaly_score": 0.82,
    "inference_time_ms": 47,
    "edge_label": "RISING_WATER_FAST"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `packet_type` | string | ✅ | Must be `"SENSOR_READING"` |
| `node_id` | string | ✅ | Must reference an existing node |
| `timestamp` | string (ISO 8601) | ✅ | Must include timezone |
| `readings` | object | ✅ | All sub-fields are `float \| null`. `null` = sensor not present on this node. |
| `device_health` | object | ✅ | |
| `device_health.battery_pct` | int | ✅ | 0-100 |
| `device_health.solar_charging` | bool | ✅ | |
| `device_health.signal_strength_dbm` | int | ✅ | Typically -120 to 0 |
| `device_health.uptime_seconds` | int | ✅ | ≥ 0 |
| `device_health.firmware_version` | string | ✅ | |
| `edge_inference` | object | ❌ | Only present when the edge model ran. Omit entirely if no inference. |
| `edge_inference.model_version` | string | ✅ (if edge_inference present) | |
| `edge_inference.anomaly_detected` | bool | ✅ (if edge_inference present) | |
| `edge_inference.anomaly_score` | float | ✅ (if edge_inference present) | 0.0 to 1.0 |
| `edge_inference.inference_time_ms` | int | ✅ (if edge_inference present) | |
| `edge_inference.edge_label` | string | ❌ | Human-readable label like `RISING_WATER_FAST`, `NORMAL`, etc. |

**Side Effects:**
1. Inserts a row into `sensor_readings` hypertable
2. Updates `nodes.last_seen_at` for this `node_id`
3. Broadcasts the reading to all WebSocket clients on the `"live"` channel

**Response `201 Created`:**
```json
{
  "status": "ok",
  "message": "Reading ingested",
  "node_id": "LG-NODE-PAT-003",
  "timestamp": "2026-08-24T13:00:00.000+05:30",
  "anomaly_detected": true
}
```

**Errors:** `404 NOT_FOUND` if `node_id` doesn't exist. `422 VALIDATION_ERROR` if required fields missing or types wrong.

---

### `POST /data/batch`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR`

**Purpose:** Accept a batch of readings at once (gateway sends all its nodes' data in one HTTP call).

**Request Body:**
```json
{
  "gateway_id": "LG-GW-PAT-01",
  "readings": [
    { "...same shape as POST /data/ingest body..." },
    { "...another reading..." },
    { "...another reading..." }
  ]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `gateway_id` | string | ✅ | Identifies the gateway sending the batch |
| `readings` | array | ✅ | Each element has the exact same shape as `POST /data/ingest` request body. Max 100 per batch. |

**Response `201 Created`:**
```json
{
  "status": "ok",
  "message": "Batch ingested",
  "gateway_id": "LG-GW-PAT-01",
  "total_received": 8,
  "total_stored": 8,
  "total_failed": 0,
  "failures": []
}
```

If some readings fail validation:
```json
{
  "status": "partial",
  "message": "Batch partially ingested",
  "gateway_id": "LG-GW-PAT-01",
  "total_received": 8,
  "total_stored": 7,
  "total_failed": 1,
  "failures": [
    {
      "index": 3,
      "node_id": "LG-NODE-PAT-999",
      "error": "Node LG-NODE-PAT-999 not found"
    }
  ]
}
```

---

### `GET /data/latest`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get the most recent reading from every node in the system.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ❌ | Filter by node_type. e.g. `?type=FLOOD` |
| `gateway_id` | string | ❌ | Filter by parent gateway |
| `status` | string | ❌ | Filter by node status. Default: `ACTIVE` |

**Response `200 OK`:**
```json
{
  "total": 22,
  "readings": [
    {
      "node_id": "LG-NODE-PAT-003",
      "node_type": "FLOOD",
      "gateway_id": "LG-GW-PAT-01",
      "location_name": "Gandak River - Upstream Sector 3",
      "latitude": 25.6093,
      "longitude": 85.1376,
      "time": "2026-08-24T12:55:30.000+05:30",
      "readings": {
        "water_level_m": 2.5,
        "rainfall_mm_hr": 12.5,
        "temperature_c": 28.3,
        "humidity_pct": 94.1,
        "pressure_hpa": 1005.2
      },
      "battery_pct": 78,
      "anomaly_detected": true,
      "anomaly_score": 0.82
    }
  ]
}
```

**Note:** The `readings` sub-object only includes non-null sensor values (omit null fields for cleaner payloads in this summary endpoint).

**SQL pattern:**
```sql
SELECT DISTINCT ON (sr.node_id)
  sr.*, n.node_type, n.location_name, n.latitude, n.longitude
FROM sensor_readings sr
JOIN nodes n ON sr.node_id = n.node_id
WHERE n.status = 'ACTIVE'
ORDER BY sr.node_id, sr.time DESC
```

---

### `GET /data/latest/{node_id}`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `node_id`

**Response `200 OK`:**
Same shape as a single element of the `GET /data/latest` response array, but returns the full reading (including null sensor values).

---

### `GET /data/history`
**Auth:** 🔒 Any authenticated user

**Purpose:** Query historical sensor data with optional downsampling.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node_id` | string | ❌ | — | Filter by specific node. If omitted, returns data from all nodes (use with caution). |
| `type` | string | ❌ | — | Filter by node_type |
| `from` | datetime | ❌ | 24h ago | Start of time range |
| `to` | datetime | ❌ | now | End of time range |
| `interval` | string | ❌ | `raw` | Downsampling interval. Accepted: `raw` (no downsampling), `1m`, `5m`, `15m`, `30m`, `1h`, `6h`, `1d` |
| `limit` | int | ❌ | 500 | Max rows. Max: 5000. |
| `offset` | int | ❌ | 0 | Pagination offset |

When `interval` is anything other than `raw`, the endpoint uses TimescaleDB `time_bucket()` to aggregate readings. Numeric sensor fields are averaged within each bucket:

**SQL pattern for downsampled query:**
```sql
SELECT
  time_bucket(:interval, time) AS bucket,
  node_id,
  AVG(water_level_m) AS water_level_m,
  AVG(rainfall_mm_hr) AS rainfall_mm_hr,
  AVG(temperature_c) AS temperature_c,
  AVG(humidity_pct) AS humidity_pct,
  AVG(pressure_hpa) AS pressure_hpa,
  AVG(pm25_ugm3) AS pm25_ugm3,
  AVG(pm10_ugm3) AS pm10_ugm3,
  AVG(smoke_ppm) AS smoke_ppm,
  AVG(soil_moisture_pct) AS soil_moisture_pct,
  AVG(tds_ppm) AS tds_ppm,
  AVG(wind_speed_kmh) AS wind_speed_kmh,
  AVG(uv_index) AS uv_index,
  AVG(co_ugm3) AS co_ugm3,
  AVG(battery_pct)::SMALLINT AS battery_pct,
  BOOL_OR(anomaly_detected) AS anomaly_detected,
  MAX(anomaly_score) AS anomaly_score,
  COUNT(*) AS sample_count
FROM sensor_readings
WHERE node_id = :node_id
  AND time >= :from_time
  AND time <= :to_time
GROUP BY bucket, node_id
ORDER BY bucket DESC
LIMIT :limit OFFSET :offset
```

**Response `200 OK`:**
```json
{
  "node_id": "LG-NODE-PAT-003",
  "from": "2026-08-23T00:00:00.000+05:30",
  "to": "2026-08-24T13:00:00.000+05:30",
  "interval": "1h",
  "total_buckets": 37,
  "limit": 500,
  "offset": 0,
  "data": [
    {
      "bucket": "2026-08-24T12:00:00.000+05:30",
      "node_id": "LG-NODE-PAT-003",
      "water_level_m": 2.35,
      "rainfall_mm_hr": 10.8,
      "temperature_c": 28.1,
      "humidity_pct": 93.5,
      "pressure_hpa": 1005.0,
      "pm25_ugm3": null,
      "pm10_ugm3": null,
      "smoke_ppm": null,
      "soil_moisture_pct": null,
      "tds_ppm": null,
      "wind_speed_kmh": null,
      "uv_index": null,
      "co_ugm3": null,
      "battery_pct": 79,
      "anomaly_detected": true,
      "anomaly_score": 0.82,
      "sample_count": 12
    }
  ]
}
```

---

### `GET /data/aggregate`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get a single aggregated statistic for a specific metric across nodes or time.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `metric` | string | ✅ | — | Column name to aggregate. One of: `water_level_m`, `rainfall_mm_hr`, `temperature_c`, `humidity_pct`, `pressure_hpa`, `pm25_ugm3`, `pm10_ugm3`, `smoke_ppm`, `soil_moisture_pct`, `tds_ppm`, `wind_speed_kmh`, `uv_index`, `co_ugm3`, `battery_pct`, `anomaly_score` |
| `agg` | string | ❌ | `avg` | Aggregate function. One of: `avg`, `min`, `max`, `sum`, `count` |
| `interval` | string | ❌ | `1h` | Time bucket. Same values as `/data/history`. |
| `node_id` | string | ❌ | — | Filter to specific node |
| `gateway_id` | string | ❌ | — | Filter to nodes under this gateway |
| `from` | datetime | ❌ | 24h ago | |
| `to` | datetime | ❌ | now | |
| `limit` | int | ❌ | 100 | |

**Response `200 OK`:**
```json
{
  "metric": "water_level_m",
  "aggregation": "avg",
  "interval": "1h",
  "from": "2026-08-23T13:00:00.000+05:30",
  "to": "2026-08-24T13:00:00.000+05:30",
  "data": [
    {"bucket": "2026-08-24T12:00:00.000+05:30", "value": 2.35},
    {"bucket": "2026-08-24T11:00:00.000+05:30", "value": 2.10},
    {"bucket": "2026-08-24T10:00:00.000+05:30", "value": 1.85}
  ]
}
```

---

## 7. Alerts

### `POST /alerts`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR` (or internal — called by MQTT handler)

**Request Body** (matches Alert Packet from `data_schema.md` §1.2):
```json
{
  "schema_version": "1.0",
  "packet_type": "ALERT",
  "alert_id": "ALT-20260824-001",
  "timestamp": "2026-08-24T13:05:00.000+05:30",
  "source": "GATEWAY",
  "gateway_id": "LG-GW-PAT-01",
  "alert_level": "RED",
  "alert_type": "FLOOD",
  "confidence_score": 0.87,
  "hazard": {
    "type": "FLOOD",
    "subtype": "FLASH_FLOOD",
    "description": "Rapid water level rise detected upstream",
    "estimated_impact_time_min": 45,
    "affected_area": {
      "center_lat": 25.6200,
      "center_lng": 85.1400,
      "radius_km": 5,
      "area_name": "Hajipur South Ward"
    }
  },
  "trigger_data": {
    "primary_node": "LG-NODE-PAT-003",
    "water_level_m": 2.5,
    "rate_of_rise_m_per_hr": 1.8,
    "rainfall_mm_hr": 45.2,
    "supporting_nodes": [
      {
        "node_id": "LG-NODE-PAT-001",
        "water_level_m": 1.8,
        "distance_km": 3.2,
        "position": "upstream"
      }
    ]
  },
  "model_prediction": {
    "model_name": "flood-lstm-v3",
    "model_layer": "GATEWAY",
    "flood_probability": 0.87,
    "predicted_peak_level_m": 3.8,
    "predicted_peak_time": "2026-08-24T13:50:00+05:30"
  },
  "recommended_actions": [
    "Evacuate low-lying areas within 5km radius",
    "Alert downstream villages",
    "Notify NDRF team"
  ]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `alert_id` | string | ✅ | Format: `ALT-YYYYMMDD-NNN`. Max 30 chars. Must be unique. |
| `timestamp` | datetime | ✅ | ISO 8601 with timezone |
| `source` | string | ✅ | One of: `EDGE`, `GATEWAY`, `CLOUD` |
| `gateway_id` | string | ✅ | Must reference existing gateway |
| `alert_level` | string | ✅ | One of: `GREEN`, `YELLOW`, `ORANGE`, `RED` |
| `alert_type` | string | ✅ | One of: `FLOOD`, `AIR_QUALITY`, `FIRE`, `EXTREME_HEAT`, `LANDSLIDE`, `INDUSTRIAL_LEAK`, `WATER_CONTAMINATION` |
| `confidence_score` | float | ✅ | 0.0 to 1.0 |
| `hazard` | object | ✅ | Contains `type`, `subtype`, `description`, `estimated_impact_time_min`, `affected_area` |
| `hazard.affected_area.center_lat` | float | ✅ | |
| `hazard.affected_area.center_lng` | float | ✅ | |
| `hazard.affected_area.radius_km` | float | ✅ | |
| `hazard.affected_area.area_name` | string | ✅ | |
| `trigger_data` | object | ✅ | Raw sensor data that caused this alert |
| `trigger_data.primary_node` | string | ✅ | The node_id whose reading was the primary trigger |
| `model_prediction` | object | ❌ | Present when ML model produced the alert |
| `recommended_actions` | string[] | ❌ | Human-readable action items |

**Side Effects:**
1. Inserts into `alerts` table with `status = 'ACTIVE'`
2. **Alert cooldown check**: Before inserting, queries for existing active alert of same `alert_type` + `affected_area_name` within last 15 minutes. If found, the new reading is logged as supporting evidence for the existing alert (no new alert created — returns `200` with existing alert_id instead of `201`).
3. Triggers alert engine → determines recipients → dispatches SMS/push notifications
4. Broadcasts to WebSocket `"alerts"` channel

**Response `201 Created`:**
```json
{
  "status": "ok",
  "message": "Alert created",
  "alert_id": "ALT-20260824-001",
  "alert_level": "RED",
  "alert_type": "FLOOD",
  "notifications_dispatched": 5
}
```

**Response `200 OK` (if cooldown applied):**
```json
{
  "status": "cooldown",
  "message": "Active alert already exists for this area. Data appended as supporting evidence.",
  "existing_alert_id": "ALT-20260824-001"
}
```

---

### `GET /alerts`
**Auth:** 🔒 Any authenticated user

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | ❌ | — | One of: `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_ALARM` |
| `level` | string | ❌ | — | One of: `GREEN`, `YELLOW`, `ORANGE`, `RED` |
| `type` | string | ❌ | — | One of the alert type codes |
| `source` | string | ❌ | — | One of: `EDGE`, `GATEWAY`, `CLOUD` |
| `gateway_id` | string | ❌ | — | Filter by source gateway |
| `from` | datetime | ❌ | 7 days ago | Start of time range |
| `to` | datetime | ❌ | now | End of time range |
| `limit` | int | ❌ | 50 | Max: 200 |
| `offset` | int | ❌ | 0 | |
| `sort` | string | ❌ | `timestamp_desc` | One of: `timestamp_desc`, `timestamp_asc`, `level_desc`, `level_asc` |

**Response `200 OK`:**
```json
{
  "total": 45,
  "limit": 50,
  "offset": 0,
  "alerts": [
    {
      "alert_id": "ALT-20260824-001",
      "timestamp": "2026-08-24T13:05:00.000+05:30",
      "source": "GATEWAY",
      "gateway_id": "LG-GW-PAT-01",
      "primary_node_id": "LG-NODE-PAT-003",
      "alert_level": "RED",
      "alert_type": "FLOOD",
      "alert_subtype": "FLASH_FLOOD",
      "confidence": 0.87,
      "description": "Rapid water level rise detected upstream",
      "affected_area_name": "Hajipur South Ward",
      "affected_lat": 25.6200,
      "affected_lng": 85.1400,
      "affected_radius_km": 5.0,
      "status": "ACTIVE",
      "acknowledged_by": null,
      "acknowledged_at": null,
      "resolved_at": null,
      "created_at": "2026-08-24T13:05:01.000+05:30"
    }
  ]
}
```

**Note:** The list endpoint returns a **summary** shape (no `trigger_data`, `model_prediction`, `recommended_actions`, `notifications_sent`, or `prediction_data`). Use `GET /alerts/{alert_id}` for the full detail.

---

### `GET /alerts/{alert_id}`
**Auth:** 🔒 Any authenticated user

**Path Parameter:** `alert_id` — e.g. `ALT-20260824-001`

**Response `200 OK`:**
Returns the **full** alert record including all nested objects.

```json
{
  "alert_id": "ALT-20260824-001",
  "timestamp": "2026-08-24T13:05:00.000+05:30",
  "source": "GATEWAY",
  "gateway_id": "LG-GW-PAT-01",
  "primary_node_id": "LG-NODE-PAT-003",
  "alert_level": "RED",
  "alert_type": "FLOOD",
  "alert_subtype": "FLASH_FLOOD",
  "confidence": 0.87,
  "description": "Rapid water level rise detected upstream",
  "affected_lat": 25.6200,
  "affected_lng": 85.1400,
  "affected_radius_km": 5.0,
  "affected_area_name": "Hajipur South Ward",
  "model_name": "flood-lstm-v3",
  "model_layer": "GATEWAY",
  "prediction_data": {
    "flood_probability": 0.87,
    "predicted_peak_level_m": 3.8,
    "predicted_peak_time": "2026-08-24T13:50:00+05:30",
    "trigger_data": {
      "primary_node": "LG-NODE-PAT-003",
      "water_level_m": 2.5,
      "rate_of_rise_m_per_hr": 1.8,
      "rainfall_mm_hr": 45.2,
      "supporting_nodes": [
        {
          "node_id": "LG-NODE-PAT-001",
          "water_level_m": 1.8,
          "distance_km": 3.2,
          "position": "upstream"
        }
      ]
    },
    "recommended_actions": [
      "Evacuate low-lying areas within 5km radius",
      "Alert downstream villages",
      "Notify NDRF team"
    ]
  },
  "status": "ACTIVE",
  "acknowledged_by": null,
  "acknowledged_at": null,
  "resolved_at": null,
  "notifications_sent": [
    {
      "channel": "SMS",
      "to": "+919876543210",
      "sent_at": "2026-08-24T13:05:05.000+05:30",
      "status": "delivered"
    },
    {
      "channel": "PUSH",
      "to": "user_id:1",
      "sent_at": "2026-08-24T13:05:03.000+05:30",
      "status": "sent"
    }
  ],
  "created_at": "2026-08-24T13:05:01.000+05:30"
}
```

**Implementation Note:** The `prediction_data` column is `JSONB` in PostgreSQL. When creating an alert, store `trigger_data`, `model_prediction`, and `recommended_actions` from the incoming Alert Packet as a combined JSON object inside `prediction_data`. This avoids needing extra columns for the variable-structure nested data.

---

### `PATCH /alerts/{alert_id}/acknowledge`
**Auth:** 🔒 Roles: `ADMIN`, `AUTHORITY`

**Request Body:**
```json
{
  "acknowledged_by": "officer@patna.gov.in"
}
```

**Side Effects:**
1. Sets `status = 'ACKNOWLEDGED'`
2. Sets `acknowledged_by` and `acknowledged_at = NOW()`
3. Inserts an `audit_log` row: `action = 'ALERT_ACKNOWLEDGED'`, `target_type = 'ALERT'`, `target_id = alert_id`
4. Publishes to MQTT topic `lookoutgrid/alerts/{gateway_id}/update` with `{"alert_id": "...", "status": "ACKNOWLEDGED"}`
5. Broadcasts to WebSocket `"alerts"` channel

**Response `200 OK`:**
```json
{
  "alert_id": "ALT-20260824-001",
  "status": "ACKNOWLEDGED",
  "acknowledged_by": "officer@patna.gov.in",
  "acknowledged_at": "2026-08-24T13:15:00.000+05:30"
}
```

**Errors:** `404 NOT_FOUND` if alert doesn't exist. `409 CONFLICT` if alert is already `RESOLVED` or `FALSE_ALARM`.

---

### `PATCH /alerts/{alert_id}/resolve`
**Auth:** 🔒 Roles: `ADMIN`, `AUTHORITY`

**Request Body:**
```json
{
  "resolution_notes": "Water level receded below danger mark. Situation normalized."
}
```

| Field | Type | Required |
|-------|------|----------|
| `resolution_notes` | string | ❌ |

**Side Effects:**
1. Sets `status = 'RESOLVED'`, `resolved_at = NOW()`
2. Inserts `audit_log` row
3. Publishes to MQTT `lookoutgrid/alerts/{gateway_id}/resolved`
4. Broadcasts to WebSocket

**Response `200 OK`:**
```json
{
  "alert_id": "ALT-20260824-001",
  "status": "RESOLVED",
  "resolved_at": "2026-08-24T14:30:00.000+05:30"
}
```

---

### `PATCH /alerts/{alert_id}/false-alarm`
**Auth:** 🔒 Roles: `ADMIN`

**Request Body:**
```json
{
  "reason": "Sensor malfunction caused false spike in water level readings"
}
```

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | ✅ |

**Side Effects:**
1. Sets `status = 'FALSE_ALARM'`, `resolved_at = NOW()`
2. Inserts `audit_log` row with `details = {"reason": "..."}`
3. The `reason` is stored for ML model improvement — false alarms should be fed back into the training pipeline to reduce future false positives

**Response `200 OK`:**
```json
{
  "alert_id": "ALT-20260824-001",
  "status": "FALSE_ALARM",
  "resolved_at": "2026-08-24T14:30:00.000+05:30",
  "reason": "Sensor malfunction caused false spike in water level readings"
}
```

---

### `GET /alerts/active`
**Auth:** 🔒 Any authenticated user

**Purpose:** Shortcut to get all currently active alerts. Equivalent to `GET /alerts?status=ACTIVE&sort=timestamp_desc`.

**Response `200 OK`:**
Same shape as `GET /alerts` response, pre-filtered to `status = 'ACTIVE'`.

---

### `GET /alerts/statistics`
**Auth:** 🔒 Roles: `ADMIN`, `AUTHORITY`

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | ❌ | `30d` | Time period. One of: `24h`, `7d`, `30d`, `90d`, `1y` |

**Response `200 OK`:**
```json
{
  "period": "30d",
  "from": "2026-07-25T00:00:00.000+05:30",
  "to": "2026-08-24T13:00:00.000+05:30",
  "total_alerts": 127,
  "by_level": {
    "RED": 5,
    "ORANGE": 18,
    "YELLOW": 72,
    "GREEN": 32
  },
  "by_type": {
    "FLOOD": 45,
    "AIR_QUALITY": 62,
    "FIRE": 8,
    "EXTREME_HEAT": 12,
    "LANDSLIDE": 0,
    "INDUSTRIAL_LEAK": 0,
    "WATER_CONTAMINATION": 0
  },
  "by_status": {
    "ACTIVE": 3,
    "ACKNOWLEDGED": 2,
    "RESOLVED": 115,
    "FALSE_ALARM": 7
  },
  "false_alarm_rate": 0.055,
  "avg_acknowledgment_time_minutes": 8.3,
  "avg_resolution_time_minutes": 142.7
}
```

**SQL patterns:**
```sql
-- false_alarm_rate
SELECT
  COUNT(*) FILTER (WHERE status = 'FALSE_ALARM')::REAL /
  NULLIF(COUNT(*), 0) AS false_alarm_rate
FROM alerts
WHERE timestamp >= :from_time;

-- avg_acknowledgment_time
SELECT AVG(EXTRACT(EPOCH FROM (acknowledged_at - timestamp)) / 60)
FROM alerts
WHERE acknowledged_at IS NOT NULL AND timestamp >= :from_time;

-- avg_resolution_time
SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - timestamp)) / 60)
FROM alerts
WHERE resolved_at IS NOT NULL AND timestamp >= :from_time;
```

---

## 8. ML Model / Prediction

### `POST /predict`
**Auth:** 🔒 Roles: `ADMIN`, `OPERATOR` (or internal — called when gateway escalates to cloud)

**Purpose:** Request the cloud ML model to run inference on provided sensor data. The gateway sends data here when its local model flags medium-high risk and wants cloud confirmation.

**Request Body:**
```json
{
  "gateway_id": "LG-GW-PAT-01",
  "hazard_type": "FLOOD",
  "timestamp": "2026-08-24T13:00:00.000+05:30",
  "node_readings": [
    {
      "node_id": "LG-NODE-PAT-003",
      "position": "upstream",
      "water_level_m": 2.5,
      "rainfall_mm_hr": 45.2,
      "temperature_c": 28.3,
      "humidity_pct": 94.1,
      "pressure_hpa": 1005.2
    },
    {
      "node_id": "LG-NODE-PAT-001",
      "position": "upstream",
      "water_level_m": 1.8,
      "rainfall_mm_hr": 38.0,
      "temperature_c": 27.9,
      "humidity_pct": 95.3,
      "pressure_hpa": 1004.8
    },
    {
      "node_id": "LG-NODE-PAT-005",
      "position": "downstream",
      "water_level_m": 0.9,
      "rainfall_mm_hr": 12.0,
      "temperature_c": 29.1,
      "humidity_pct": 88.7,
      "pressure_hpa": 1005.5
    }
  ],
  "gateway_prediction": {
    "flood_probability": 0.72,
    "model_name": "flood-lstm-v3",
    "model_layer": "GATEWAY"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `gateway_id` | string | ✅ | Source gateway |
| `hazard_type` | string | ✅ | Determines which cloud model to use |
| `timestamp` | datetime | ✅ | |
| `node_readings` | array | ✅ | At least 1 reading. Each entry has `node_id` and all relevant sensor fields. |
| `gateway_prediction` | object | ❌ | The gateway's own prediction (for comparison/logging) |

**Response `200 OK`:**
```json
{
  "prediction_id": "PRED-20260824-001",
  "hazard_type": "FLOOD",
  "timestamp": "2026-08-24T13:00:05.000+05:30",
  "model_name": "flood-transformer-v2",
  "model_layer": "CLOUD",
  "inference_time_ms": 320,
  "result": {
    "flood_probability": 0.91,
    "predicted_peak_level_m": 4.2,
    "predicted_peak_time": "2026-08-24T14:15:00+05:30",
    "predicted_duration_hours": 6,
    "confidence_interval": [0.85, 0.96]
  },
  "recommended_alert_level": "RED",
  "agrees_with_gateway": true
}
```

**Side Effects:** If `result.flood_probability >= 0.7`, the server auto-creates an alert via `POST /alerts` with `source = "CLOUD"`.

---

### `GET /models`
**Auth:** 🔒 Roles: `ADMIN`

**Response `200 OK`:**
```json
{
  "models": [
    {
      "model_id": "flood-lstm-v3",
      "model_type": "FLOOD",
      "model_layer": "GATEWAY",
      "format": "tflite",
      "file_size_mb": 4.2,
      "deployed_to": ["LG-GW-PAT-01", "LG-GW-PAT-02"],
      "accuracy": 0.92,
      "f1_score": 0.89,
      "created_at": "2026-08-15T10:00:00.000+05:30"
    },
    {
      "model_id": "flood-v2-q8",
      "model_type": "FLOOD",
      "model_layer": "EDGE",
      "format": "tflite_micro",
      "file_size_mb": 0.087,
      "deployed_to": ["LG-NODE-PAT-001", "LG-NODE-PAT-002", "LG-NODE-PAT-003"],
      "accuracy": 0.85,
      "f1_score": 0.82,
      "created_at": "2026-08-10T10:00:00.000+05:30"
    }
  ]
}
```

---

### `POST /models/deploy`
**Auth:** 🔒 Roles: `ADMIN`

**Purpose:** Trigger OTA deployment of a model to gateways or nodes.

**Request Body:**
```json
{
  "model_id": "flood-lstm-v4",
  "target_type": "GATEWAY",
  "target_ids": ["LG-GW-PAT-01", "LG-GW-PAT-02"],
  "model_url": "https://lookoutgrid.com/models/flood-lstm-v4.tflite",
  "model_hash_sha256": "a1b2c3d4e5f6..."
}
```

**Side Effects:** Publishes a `COMMAND` packet (from `data_schema.md` §1.5) with `command = "UPDATE_MODEL"` to the MQTT topic `lookoutgrid/commands/{gateway_id}/model-update` for each target gateway.

**Response `202 Accepted`:**
```json
{
  "message": "Deployment initiated",
  "model_id": "flood-lstm-v4",
  "targets_notified": 2,
  "command_ids": ["CMD-20260824-001", "CMD-20260824-002"]
}
```

---

## 9. GIS & Risk Mapping

### `GET /map/nodes`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get all node locations with current status, formatted for map markers. Frontend uses this to render marker pins on a Leaflet/Mapbox map.

**Response `200 OK`:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [85.1376, 25.6093]
      },
      "properties": {
        "node_id": "LG-NODE-PAT-003",
        "node_type": "FLOOD",
        "status": "ACTIVE",
        "gateway_id": "LG-GW-PAT-01",
        "location_name": "Gandak River - Upstream Sector 3",
        "battery_pct": 78,
        "last_seen_at": "2026-08-24T12:55:30.000+05:30",
        "anomaly_detected": true,
        "anomaly_score": 0.82,
        "marker_color": "red"
      }
    }
  ]
}
```

**`marker_color` logic:**
- `"red"` — `anomaly_detected = true` AND `anomaly_score >= 0.7`
- `"orange"` — `anomaly_detected = true` AND `anomaly_score < 0.7`
- `"yellow"` — `status = 'ACTIVE'` AND `last_seen_at` is > 10 min ago (stale)
- `"green"` — normal active node
- `"gray"` — `status = 'INACTIVE'` or `'MAINTENANCE'`

**Note:** GeoJSON uses `[longitude, latitude]` order (not `[lat, lng]`).

---

### `GET /map/risk-zones`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get currently active risk zones as GeoJSON, rendered as colored circles/polygons on the map.

**Response `200 OK`:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [85.1400, 25.6200]
      },
      "properties": {
        "alert_id": "ALT-20260824-001",
        "alert_level": "RED",
        "alert_type": "FLOOD",
        "radius_km": 5.0,
        "description": "Rapid water level rise detected upstream",
        "confidence": 0.87,
        "affected_area_name": "Hajipur South Ward",
        "estimated_impact_time_min": 45,
        "fill_color": "#FF0000",
        "fill_opacity": 0.3,
        "stroke_color": "#CC0000"
      }
    }
  ]
}
```

**`fill_color` mapping:**
| Alert Level | `fill_color` | `fill_opacity` |
|-------------|-------------|----------------|
| `RED` | `#FF0000` | 0.3 |
| `ORANGE` | `#FF8C00` | 0.25 |
| `YELLOW` | `#FFD700` | 0.2 |

The frontend renders each point as a circle with the given `radius_km` (converted to meters for Leaflet's `L.circle()`).

**Data source:** Queries `alerts` table where `status = 'ACTIVE'`.

---

### `GET /map/heatmap`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get risk intensity data for rendering a heatmap layer on the map.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | ❌ | `1h` | How far back to look. One of: `15m`, `30m`, `1h`, `6h`, `24h` |
| `grid_size_deg` | float | ❌ | 0.01 | Grid cell size in degrees (~1.1 km at India latitudes) |

**Response `200 OK`:**
```json
{
  "period": "1h",
  "grid_size_deg": 0.01,
  "generated_at": "2026-08-24T13:00:00.000+05:30",
  "points": [
    {"lat": 25.61, "lng": 85.14, "risk_score": 0.82, "dominant_hazard": "FLOOD"},
    {"lat": 25.62, "lng": 85.14, "risk_score": 0.45, "dominant_hazard": "FLOOD"},
    {"lat": 25.60, "lng": 85.13, "risk_score": 0.12, "dominant_hazard": null}
  ]
}
```

**`risk_score` computation:**
For each grid cell (defined by rounding node lat/lng to the nearest `grid_size_deg`), take the MAX `anomaly_score` from all `sensor_readings` within that cell during the specified `period`. If no anomaly was detected, `risk_score = 0`.

```sql
SELECT
  ROUND(n.latitude / :grid_size) * :grid_size AS lat,
  ROUND(n.longitude / :grid_size) * :grid_size AS lng,
  MAX(sr.anomaly_score) AS risk_score
FROM sensor_readings sr
JOIN nodes n ON sr.node_id = n.node_id
WHERE sr.time >= NOW() - :period_interval
  AND sr.anomaly_score IS NOT NULL
  AND sr.anomaly_score > 0
GROUP BY lat, lng
```

---

### `GET /map/alerts`
**Auth:** 🔒 Any authenticated user

**Purpose:** Get active alert locations for map overlay. Lighter version of `/map/risk-zones` — just points, no radius/style info.

**Response `200 OK`:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [85.1400, 25.6200]
      },
      "properties": {
        "alert_id": "ALT-20260824-001",
        "alert_level": "RED",
        "alert_type": "FLOOD",
        "description": "Rapid water level rise detected upstream",
        "timestamp": "2026-08-24T13:05:00.000+05:30"
      }
    }
  ]
}
```

---

## 10. Analytics & Dashboard

### `GET /dashboard/overview`
**Auth:** 🔒 Any authenticated user

**Purpose:** System summary for the dashboard home page.

**Response `200 OK`:**
```json
{
  "total_nodes": 24,
  "active_nodes": 22,
  "inactive_nodes": 2,
  "maintenance_nodes": 0,
  "total_gateways": 3,
  "active_gateways": 3,
  "offline_gateways": 0,
  "active_alerts": {
    "total": 8,
    "RED": 1,
    "ORANGE": 2,
    "YELLOW": 5
  },
  "alerts_last_24h": 12,
  "false_alarm_rate_30d": 0.055,
  "system_health": "OPERATIONAL",
  "last_updated": "2026-08-24T13:00:00.000+05:30"
}
```

**`system_health` logic:**
- `"OPERATIONAL"` — all gateways have heartbeat within last 10 minutes, no RED alerts
- `"WARNING"` — at least one gateway missing heartbeat OR at least one RED alert active
- `"DEGRADED"` — multiple gateways offline OR critical alert unacknowledged for > 30 min
- `"OFFLINE"` — no heartbeats received from any gateway in last 30 minutes

**SQL queries:**
```sql
-- total/active/inactive nodes
SELECT status, COUNT(*) FROM nodes GROUP BY status;

-- active gateways (heartbeat within 10 min)
SELECT COUNT(*) FROM gateways
WHERE last_heartbeat >= NOW() - INTERVAL '10 minutes';

-- active alerts by level
SELECT alert_level, COUNT(*) FROM alerts
WHERE status = 'ACTIVE' GROUP BY alert_level;

-- alerts in last 24h
SELECT COUNT(*) FROM alerts
WHERE timestamp >= NOW() - INTERVAL '24 hours';
```

---

### `GET /dashboard/trends`
**Auth:** 🔒 Any authenticated user

**Purpose:** Trend data for dashboard charts. Returns time-bucketed averages for a specific metric.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `metric` | string | ✅ | — | Same as `/data/aggregate` metric param |
| `period` | string | ❌ | `7d` | One of: `24h`, `7d`, `30d`, `90d` |
| `interval` | string | ❌ | Auto | Downsampling interval. If omitted, auto-selects: `24h→5m`, `7d→1h`, `30d→6h`, `90d→1d` |
| `node_id` | string | ❌ | — | Specific node (if omitted, averages across all nodes) |
| `gateway_id` | string | ❌ | — | Filter to gateway's nodes |

**Response `200 OK`:**
```json
{
  "metric": "water_level_m",
  "period": "7d",
  "interval": "1h",
  "data": [
    {"time": "2026-08-24T12:00:00.000+05:30", "value": 2.35, "min": 2.10, "max": 2.55},
    {"time": "2026-08-24T11:00:00.000+05:30", "value": 2.10, "min": 1.95, "max": 2.28},
    {"time": "2026-08-24T10:00:00.000+05:30", "value": 1.85, "min": 1.72, "max": 1.99}
  ]
}
```

---

### `GET /dashboard/risk-summary`
**Auth:** 🔒 Any authenticated user

**Purpose:** Current risk levels grouped by region/gateway.

**Response `200 OK`:**
```json
{
  "regions": [
    {
      "gateway_id": "LG-GW-PAT-01",
      "location_name": "Patna Flood Control Office",
      "overall_risk_level": "RED",
      "active_alerts": 1,
      "hazards": {
        "FLOOD": "RED",
        "AIR_QUALITY": "YELLOW"
      },
      "active_nodes": 7,
      "total_nodes": 8,
      "last_heartbeat": "2026-08-24T12:55:00.000+05:30"
    },
    {
      "gateway_id": "LG-GW-DEL-01",
      "location_name": "Delhi AQI Monitoring Center",
      "overall_risk_level": "ORANGE",
      "active_alerts": 2,
      "hazards": {
        "AIR_QUALITY": "ORANGE"
      },
      "active_nodes": 10,
      "total_nodes": 10,
      "last_heartbeat": "2026-08-24T12:57:00.000+05:30"
    }
  ]
}
```

`overall_risk_level` is the highest alert level among all active alerts for that gateway's area.

---

### `GET /analytics/correlation`
**Auth:** 🔒 Roles: `ADMIN`, `AUTHORITY`

**Purpose:** Cross-node correlation data. Shows how readings from multiple nodes relate to each other.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `node_ids` | string | ✅ | Comma-separated list of node_ids. e.g. `?node_ids=LG-NODE-PAT-001,LG-NODE-PAT-003,LG-NODE-PAT-005` |
| `metric` | string | ✅ | Column to correlate |
| `period` | string | ❌ | Default: `7d` |

**Response `200 OK`:**
```json
{
  "metric": "water_level_m",
  "period": "7d",
  "correlation_matrix": {
    "LG-NODE-PAT-001": {"LG-NODE-PAT-001": 1.0, "LG-NODE-PAT-003": 0.87, "LG-NODE-PAT-005": 0.42},
    "LG-NODE-PAT-003": {"LG-NODE-PAT-001": 0.87, "LG-NODE-PAT-003": 1.0, "LG-NODE-PAT-005": 0.65},
    "LG-NODE-PAT-005": {"LG-NODE-PAT-001": 0.42, "LG-NODE-PAT-003": 0.65, "LG-NODE-PAT-005": 1.0}
  },
  "time_series": {
    "LG-NODE-PAT-001": [{"time": "...", "value": 1.8}, "..."],
    "LG-NODE-PAT-003": [{"time": "...", "value": 2.5}, "..."],
    "LG-NODE-PAT-005": [{"time": "...", "value": 0.9}, "..."]
  }
}
```

---

### `GET /analytics/predictions`
**Auth:** 🔒 Roles: `ADMIN`, `AUTHORITY`

**Purpose:** Forecast data for the next 24h or 7d (from the cloud model).

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `hazard_type` | string | ❌ | — | Filter by hazard |
| `gateway_id` | string | ❌ | — | Filter by gateway region |
| `horizon` | string | ❌ | `24h` | One of: `6h`, `24h`, `7d` |

**Response `200 OK`:**
```json
{
  "hazard_type": "FLOOD",
  "horizon": "24h",
  "generated_at": "2026-08-24T13:00:00.000+05:30",
  "predictions": [
    {
      "time": "2026-08-24T14:00:00.000+05:30",
      "predicted_water_level_m": 2.8,
      "confidence_low": 2.5,
      "confidence_high": 3.2,
      "risk_level": "RED"
    },
    {
      "time": "2026-08-24T15:00:00.000+05:30",
      "predicted_water_level_m": 3.2,
      "confidence_low": 2.8,
      "confidence_high": 3.8,
      "risk_level": "RED"
    }
  ]
}
```

---

## 11. Real-time (WebSocket)

### `WS /ws/live`
**Protocol:** WebSocket

**Purpose:** Live sensor data stream. The dashboard connects here to receive real-time readings without polling.

**Connection:** `ws://localhost:8000/v1/ws/live` or `wss://api.lookoutgrid.com/v1/ws/live`

**Server → Client Messages:**
Every time a new sensor reading is ingested (via MQTT or HTTP), the server pushes:
```json
{
  "event": "new_reading",
  "data": {
    "node_id": "LG-NODE-PAT-003",
    "node_type": "FLOOD",
    "gateway_id": "LG-GW-PAT-01",
    "time": "2026-08-24T12:55:30.000+05:30",
    "readings": {
      "water_level_m": 2.5,
      "rainfall_mm_hr": 12.5,
      "temperature_c": 28.3,
      "humidity_pct": 94.1,
      "pressure_hpa": 1005.2
    },
    "battery_pct": 78,
    "anomaly_detected": true,
    "anomaly_score": 0.82,
    "edge_label": "RISING_WATER_FAST"
  }
}
```

**Client → Server Messages (optional):**
The client can send a subscription filter to reduce noise:
```json
{
  "action": "subscribe",
  "filters": {
    "node_ids": ["LG-NODE-PAT-003", "LG-NODE-PAT-001"],
    "node_types": ["FLOOD"],
    "gateway_id": "LG-GW-PAT-01",
    "anomaly_only": false
  }
}
```

If `anomaly_only = true`, only readings with `anomaly_detected = true` are sent.

---

### `WS /ws/alerts`
**Protocol:** WebSocket

**Purpose:** Live alert stream. Pushes all alert lifecycle events to connected clients.

**Connection:** `ws://localhost:8000/v1/ws/alerts` or `wss://api.lookoutgrid.com/v1/ws/alerts`

**Server → Client Messages:**

New alert created:
```json
{
  "event": "new_alert",
  "data": {
    "alert_id": "ALT-20260824-001",
    "alert_level": "RED",
    "alert_type": "FLOOD",
    "description": "Rapid water level rise detected upstream",
    "affected_area_name": "Hajipur South Ward",
    "affected_lat": 25.6200,
    "affected_lng": 85.1400,
    "affected_radius_km": 5.0,
    "confidence": 0.87,
    "timestamp": "2026-08-24T13:05:00.000+05:30"
  }
}
```

Alert acknowledged:
```json
{
  "event": "alert_updated",
  "data": {
    "alert_id": "ALT-20260824-001",
    "status": "ACKNOWLEDGED",
    "acknowledged_by": "officer@patna.gov.in",
    "acknowledged_at": "2026-08-24T13:15:00.000+05:30"
  }
}
```

Alert resolved:
```json
{
  "event": "alert_resolved",
  "data": {
    "alert_id": "ALT-20260824-001",
    "status": "RESOLVED",
    "resolved_at": "2026-08-24T14:30:00.000+05:30"
  }
}
```

---

## 12. System / Admin

### `GET /health`
**Auth:** None (public)

**Purpose:** API health check. Used by monitoring tools, load balancers, and Docker health checks.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "timestamp": "2026-08-24T13:00:00.000+05:30",
  "version": "1.0.0",
  "database": "connected",
  "mqtt_broker": "connected",
  "uptime_seconds": 86400
}
```

**`database`:** `"connected"` if a simple `SELECT 1` succeeds against PostgreSQL, `"disconnected"` otherwise.
**`mqtt_broker`:** `"connected"` if the MQTT subscriber has an active connection, `"disconnected"` otherwise.

If any component is `"disconnected"`, the response `status` changes to `"degraded"` (but still returns HTTP 200 — the health endpoint itself is working).

---

### `GET /system/status`
**Auth:** 🔒 Roles: `ADMIN`

**Response `200 OK`:**
```json
{
  "timestamp": "2026-08-24T13:00:00.000+05:30",
  "api_version": "1.0.0",
  "database": {
    "status": "connected",
    "total_sensor_readings": 1250000,
    "total_alerts": 450,
    "db_size_mb": 128.5
  },
  "mqtt": {
    "status": "connected",
    "broker_host": "localhost:1883",
    "messages_received_last_hour": 720
  },
  "nodes": {
    "total": 24,
    "active": 22,
    "inactive": 2
  },
  "gateways": {
    "total": 3,
    "online": 3,
    "offline": 0
  },
  "alerts": {
    "active": 3,
    "unacknowledged": 1
  }
}
```

---

### `GET /system/audit-log`
**Auth:** 🔒 Roles: `ADMIN`

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `actor` | string | ❌ | — | Filter by actor (email or `"SYSTEM"`) |
| `action` | string | ❌ | — | Filter by action type |
| `target_type` | string | ❌ | — | One of: `NODE`, `GATEWAY`, `ALERT`, `USER` |
| `from` | datetime | ❌ | 7d ago | |
| `to` | datetime | ❌ | now | |
| `limit` | int | ❌ | 50 | Max: 200 |
| `offset` | int | ❌ | 0 | |

**Response `200 OK`:**
```json
{
  "total": 234,
  "limit": 50,
  "offset": 0,
  "entries": [
    {
      "id": 234,
      "timestamp": "2026-08-24T13:15:00.000+05:30",
      "actor": "officer@patna.gov.in",
      "action": "ALERT_ACKNOWLEDGED",
      "target_type": "ALERT",
      "target_id": "ALT-20260824-001",
      "details": {
        "previous_status": "ACTIVE",
        "new_status": "ACKNOWLEDGED"
      }
    }
  ]
}
```

**Audit log actions recorded by the system:**
| Action | When Logged |
|--------|------------|
| `NODE_REGISTERED` | `POST /nodes` |
| `NODE_UPDATED` | `PATCH /nodes/{id}` |
| `NODE_DECOMMISSIONED` | `DELETE /nodes/{id}` |
| `GATEWAY_REGISTERED` | `POST /gateways` |
| `GATEWAY_UPDATED` | `PATCH /gateways/{id}` |
| `ALERT_CREATED` | `POST /alerts` |
| `ALERT_ACKNOWLEDGED` | `PATCH /alerts/{id}/acknowledge` |
| `ALERT_RESOLVED` | `PATCH /alerts/{id}/resolve` |
| `ALERT_FALSE_ALARM` | `PATCH /alerts/{id}/false-alarm` |
| `MODEL_DEPLOYED` | `POST /models/deploy` |
| `COMMAND_SENT` | `POST /system/command` |
| `USER_REGISTERED` | `POST /auth/register` |
| `USER_LOGIN` | `POST /auth/login` |

---

### `POST /system/command`
**Auth:** 🔒 Roles: `ADMIN`

**Purpose:** Send a command to a gateway or node (restart, update config, calibrate sensor, etc.).

**Request Body** (matches Command Packet from `data_schema.md` §1.5):
```json
{
  "target_type": "NODE",
  "target_id": "LG-NODE-PAT-003",
  "via_gateway": "LG-GW-PAT-01",
  "command": "RESTART",
  "payload": {}
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `target_type` | string | ✅ | One of: `GATEWAY`, `NODE` |
| `target_id` | string | ✅ | The `gateway_id` or `node_id` to target |
| `via_gateway` | string | ✅ (when target is NODE) | Which gateway should relay the command |
| `command` | string | ✅ | One of: `UPDATE_MODEL`, `UPDATE_CONFIG`, `RESTART`, `CALIBRATE`, `SLEEP`, `WAKE`, `FACTORY_RESET` |
| `payload` | object | ❌ | Command-specific payload. For `UPDATE_MODEL`: `{"model_url": "...", "model_version": "...", "model_hash_sha256": "..."}`. For `UPDATE_CONFIG`: `{"key": "value", ...}`. For others: empty `{}`. |

**Side Effects:**
1. Generates a `command_id` in format `CMD-YYYYMMDD-NNN`
2. Constructs a full Command Packet
3. Publishes to the appropriate MQTT topic:
   - If `target_type = "GATEWAY"`: `lookoutgrid/commands/{target_id}/{command_topic}`
   - If `target_type = "NODE"`: `lookoutgrid/commands/{via_gateway}/{target_id}/{command_topic}`
   - Where `command_topic` is `restart`, `config`, `model-update` etc. based on the `command` field
4. Inserts `audit_log` row: `action = 'COMMAND_SENT'`

**Command → MQTT topic mapping:**
| Command | MQTT Sub-topic |
|---------|---------------|
| `UPDATE_MODEL` | `model-update` |
| `UPDATE_CONFIG` | `config` |
| `RESTART` | `restart` |
| `CALIBRATE` | `config` (with calibration payload) |
| `SLEEP` | `config` (with sleep payload) |
| `WAKE` | `config` (with wake payload) |
| `FACTORY_RESET` | `config` (with factory_reset payload) |

**Response `202 Accepted`:**
```json
{
  "status": "ok",
  "message": "Command published to MQTT",
  "command_id": "CMD-20260824-001",
  "target_type": "NODE",
  "target_id": "LG-NODE-PAT-003",
  "via_gateway": "LG-GW-PAT-01",
  "command": "RESTART",
  "issued_at": "2026-08-24T13:00:00.000+05:30"
}
```

**Errors:** `404 NOT_FOUND` if `target_id` or `via_gateway` don't exist. `503 MQTT_PUBLISH_FAILED` if the MQTT broker is unreachable.

---

## Appendix: Pagination Convention

All list endpoints follow the same pagination pattern:

**Request query params:**
- `limit` — max items per page (each endpoint has its own default and max)
- `offset` — number of items to skip

**Response envelope:**
```json
{
  "total": 127,
  "limit": 50,
  "offset": 0,
  "items": [ ... ]
}
```

Where `items` is the specific array name for that resource (`nodes`, `gateways`, `alerts`, `readings`, `entries`, etc.).

To get the next page: `?offset=50&limit=50`
To check if more pages exist: `offset + len(items) < total`
