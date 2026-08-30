CREATE TABLE nodes (
    node_id         VARCHAR(30) PRIMARY KEY,        -- LG-NODE-PAT-003
    node_type       VARCHAR(20) NOT NULL,            -- FLOOD, AIR_QUALITY, FIRE, MULTI
    gateway_id      VARCHAR(30) REFERENCES gateways(gateway_id),
    latitude        DECIMAL(10, 7) NOT NULL,
    longitude       DECIMAL(10, 7) NOT NULL,
    altitude_m      DECIMAL(7, 2),
    location_name   VARCHAR(200),
    sensors         TEXT[],                          -- Array: {WATER_LEVEL, RAINFALL, ...}
    firmware_ver    VARCHAR(20),
    edge_model_ver  VARCHAR(50),
    power_source    VARCHAR(20) DEFAULT 'SOLAR',     -- SOLAR, BATTERY, MAINS
    communication   VARCHAR(20) DEFAULT 'LORA',      -- LORA, BLE, WIFI, ESPNOW
    status          VARCHAR(20) DEFAULT 'ACTIVE',    -- ACTIVE, INACTIVE, MAINTENANCE
    installed_date  DATE,
    last_seen_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gateways (
    gateway_id      VARCHAR(30) PRIMARY KEY,         -- LG-GW-PAT-01
    latitude        DECIMAL(10, 7) NOT NULL,
    longitude       DECIMAL(10, 7) NOT NULL,
    location_name   VARCHAR(200),
    connectivity    VARCHAR(20) DEFAULT 'WIFI',        -- 4G, WIFI, ETHERNET
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    ml_model_ver    VARCHAR(50),
    total_nodes     INTEGER DEFAULT 0,
    last_heartbeat  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sensor_readings (
    time            TIMESTAMPTZ NOT NULL,
    node_id         VARCHAR(30) NOT NULL,
    gateway_id      VARCHAR(30),
    
    -- Environmental readings (NULL if sensor not present)
    water_level_m       REAL,
    rainfall_mm_hr      REAL,
    temperature_c       REAL,
    humidity_pct        REAL,
    pressure_hpa        REAL,
    pm25_ugm3           REAL,
    pm10_ugm3           REAL,
    smoke_ppm           REAL,
    soil_moisture_pct   REAL,
    tds_ppm             REAL,
    wind_speed_kmh      REAL,
    uv_index            REAL,
    co_ugm3             REAL,
    
    -- Device health
    battery_pct         SMALLINT,
    solar_charging      BOOLEAN,
    signal_strength_dbm SMALLINT,
    uptime_seconds      INTEGER,
    firmware_version    VARCHAR(50),
    
    -- Edge inference results
    model_version       VARCHAR(50),
    anomaly_detected    BOOLEAN DEFAULT FALSE,
    anomaly_score       REAL,
    inference_time_ms   INTEGER,
    edge_label          VARCHAR(50)
);

-- Convert to TimescaleDB hypertable (auto-partitions by time)
SELECT create_hypertable('sensor_readings', 'time');

-- Create indexes for common queries
-- Used by the /data/history?node_id=X endpoint. Queries filter by node_id and order by time descending.
CREATE INDEX idx_readings_node ON sensor_readings (node_id, time DESC);

-- Used by the anomaly detection dashboard. Partial index only on rows where anomaly_detected = TRUE so it's small and fast.
CREATE INDEX idx_readings_anomaly ON sensor_readings (time DESC) 
    WHERE anomaly_detected = TRUE;


CREATE TABLE alerts (
    alert_id        VARCHAR(30) PRIMARY KEY,          -- ALT-20260824-001
    timestamp       TIMESTAMPTZ NOT NULL,
    source          VARCHAR(20) NOT NULL,              -- EDGE, GATEWAY, CLOUD
    gateway_id      VARCHAR(30) REFERENCES gateways(gateway_id),
    primary_node_id VARCHAR(30) REFERENCES nodes(node_id),
    
    alert_level     VARCHAR(10) NOT NULL,              -- GREEN, YELLOW, ORANGE, RED
    alert_type      VARCHAR(30) NOT NULL,              -- FLOOD, AIR_QUALITY, FIRE, etc.
    alert_subtype   VARCHAR(50),                       -- FLASH_FLOOD, PM25_SEVERE, etc.
    
    confidence      REAL NOT NULL,                     -- 0.0 to 1.0
    description     TEXT,
    
    -- Affected area
    affected_lat    DECIMAL(10, 7),
    affected_lng    DECIMAL(10, 7),
    affected_radius_km REAL,                           -- TBD  
    affected_area_name VARCHAR(200),                   -- location name from node conf
    
    -- Model details
    model_name      VARCHAR(50),
    model_layer     VARCHAR(20),                       -- EDGE, GATEWAY, CLOUD
    prediction_data JSONB,                             -- Full model output as JSON
    
    -- Lifecycle
    status          VARCHAR(20) DEFAULT 'ACTIVE',      -- ACTIVE, ACKNOWLEDGED, RESOLVED, FALSE_ALARM
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    
    -- Notifications sent
    notifications_sent JSONB,                          -- [{channel: "SMS", to: "+91...", sent_at: "..."}]
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Used by the /alerts/active endpoint. Partial index only on status = 'ACTIVE' rows.
CREATE INDEX idx_alerts_active ON alerts (timestamp DESC) WHERE status = 'ACTIVE';

-- Used by the /alerts?type=FLOOD filter.
CREATE INDEX idx_alerts_type ON alerts (alert_type, timestamp DESC);


CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(200) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(15),
    role            VARCHAR(30) NOT NULL,               -- ADMIN, AUTHORITY, OPERATOR, CITIZEN
    organization    VARCHAR(200),                       -- "District Administration, Patna"
    alert_preferences JSONB,                           -- {channels: ["SMS", "PUSH"], min_level: "ORANGE"}
    fcm_token       VARCHAR(500),                      -- Firebase Cloud Messaging token
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
