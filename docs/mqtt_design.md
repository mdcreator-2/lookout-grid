## MQTT Broker Design

### Topic Hierarchy

```
lookoutgrid/
├── sensors/
│   ├── {gateway_id}/
│   │   ├── data                    # Regular sensor readings (batch)
│   │   ├── anomaly                 # Anomaly-flagged readings (immediate)
│   │   └── {node_id}/
│   │       ├── data                # Individual node reading
│   │       └── status              # Node health/status update
│   │
├── alerts/
│   ├── {gateway_id}/
│   │   ├── new                     # New alert generated
│   │   ├── update                  # Alert status change
│   │   └── resolved               # Alert resolved
│   │
├── gateways/
│   ├── {gateway_id}/
│   │   ├── heartbeat               # Gateway alive signal
│   │   ├── status                  # Gateway status change
│   │   └── log                     # Gateway log messages
│   │
├── commands/
│   ├── {gateway_id}/               # Commands TO gateway
│   │   ├── config                  # Config update
│   │   ├── model-update            # New ML model deployment
│   │   └── {node_id}/              # Commands TO specific node (via gateway)
│   │       ├── config
│   │       ├── model-update
│   │       └── restart
│   │
└── system/
    ├── broadcast                   # System-wide announcements
    └── health                      # System health monitoring
```

### Example MQTT Topic Usage

```
# Gateway publishes sensor data:
TOPIC:   lookoutgrid/sensors/LG-GW-PAT-01/data
PAYLOAD: {"readings": [<sensor_reading_packet>, ...]}  (batch of all node readings)
QoS:     1 (at least once delivery)

# Gateway publishes anomaly alert:
TOPIC:   lookoutgrid/sensors/LG-GW-PAT-01/anomaly
PAYLOAD: <sensor_reading_packet with anomaly_detected=true>
QoS:     2 (exactly once — critical data, must not be lost or duplicated)

# Gateway publishes new alert:
TOPIC:   lookoutgrid/alerts/LG-GW-PAT-01/new
PAYLOAD: <alert_packet>
QoS:     2

# Cloud sends model update command to gateway:
TOPIC:   lookoutgrid/commands/LG-GW-PAT-01/model-update
PAYLOAD: {"model_url": "...", "model_version": "flood-v3-q8"}
QoS:     2

# Gateway publishes heartbeat:
TOPIC:   lookoutgrid/gateways/LG-GW-PAT-01/heartbeat
PAYLOAD: <gateway_heartbeat_packet>
QoS:     0 (best effort — heartbeats are frequent, missing one is fine)
```

### QoS Levels Explained

| QoS | Name | Use For |
|-----|------|---------|
| 0 | At most once (fire and forget) | Heartbeats, routine status updates |
| 1 | At least once (acknowledged) | Regular sensor data |
| 2 | Exactly once (guaranteed) | Alerts, anomaly data, commands |

### Topic Specifications

| Topic | Published By | Subscribed By | QoS | Retained? | Payload Schema | Example Payload Reference |
|---|---|---|---|---|---|---|
| `lookoutgrid/sensors/{gateway_id}/data` | Gateway | Backend's MQTT subscriber | 1 | No | Array of Sensor Reading Packets | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/anomaly` | Gateway | Backend | 2 | No | Single Sensor Reading Packet (`anomaly_detected=true`) | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/{node_id}/data` | Gateway | Backend | 1 | No | Sensor Reading Packet | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/{node_id}/status` | Gateway | Backend | 1 | Yes | Node Status JSON | - |
| `lookoutgrid/alerts/{gateway_id}/new` | Gateway | Backend | 2 | No | Alert Packet | 1.2 Alert Packet |
## MQTT Broker Design

### Topic Hierarchy

```
lookoutgrid/
├── sensors/
│   ├── {gateway_id}/
│   │   ├── data                    # Regular sensor readings (batch)
│   │   ├── anomaly                 # Anomaly-flagged readings (immediate)
│   │   └── {node_id}/
│   │       ├── data                # Individual node reading
│   │       └── status              # Node health/status update
│   │
├── alerts/
│   ├── {gateway_id}/
│   │   ├── new                     # New alert generated
│   │   ├── update                  # Alert status change
│   │   └── resolved               # Alert resolved
│   │
├── gateways/
│   ├── {gateway_id}/
│   │   ├── heartbeat               # Gateway alive signal
│   │   ├── status                  # Gateway status change
│   │   └── log                     # Gateway log messages
│   │
├── commands/
│   ├── {gateway_id}/               # Commands TO gateway
│   │   ├── config                  # Config update
│   │   ├── model-update            # New ML model deployment
│   │   └── {node_id}/              # Commands TO specific node (via gateway)
│   │       ├── config
│   │       ├── model-update
│   │       └── restart
│   │
└── system/
    ├── broadcast                   # System-wide announcements
    └── health                      # System health monitoring
```

### Example MQTT Topic Usage

```
# Gateway publishes sensor data:
TOPIC:   lookoutgrid/sensors/LG-GW-PAT-01/data
PAYLOAD: {"readings": [<sensor_reading_packet>, ...]}  (batch of all node readings)
QoS:     1 (at least once delivery)

# Gateway publishes anomaly alert:
TOPIC:   lookoutgrid/sensors/LG-GW-PAT-01/anomaly
PAYLOAD: <sensor_reading_packet with anomaly_detected=true>
QoS:     2 (exactly once — critical data, must not be lost or duplicated)

# Gateway publishes new alert:
TOPIC:   lookoutgrid/alerts/LG-GW-PAT-01/new
PAYLOAD: <alert_packet>
QoS:     2

# Cloud sends model update command to gateway:
TOPIC:   lookoutgrid/commands/LG-GW-PAT-01/model-update
PAYLOAD: {"model_url": "...", "model_version": "flood-v3-q8"}
QoS:     2

# Gateway publishes heartbeat:
TOPIC:   lookoutgrid/gateways/LG-GW-PAT-01/heartbeat
PAYLOAD: <gateway_heartbeat_packet>
QoS:     0 (best effort — heartbeats are frequent, missing one is fine)
```

### QoS Levels Explained

| QoS | Name | Use For |
|-----|------|---------|
| 0 | At most once (fire and forget) | Heartbeats, routine status updates |
| 1 | At least once (acknowledged) | Regular sensor data |
| 2 | Exactly once (guaranteed) | Alerts, anomaly data, commands |

### Topic Specifications

| Topic | Published By | Subscribed By | QoS | Retained? | Payload Schema | Example Payload Reference |
|---|---|---|---|---|---|---|
| `lookoutgrid/sensors/{gateway_id}/data` | Gateway | Backend's MQTT subscriber | 1 | No | Array of Sensor Reading Packets | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/anomaly` | Gateway | Backend | 2 | No | Single Sensor Reading Packet (`anomaly_detected=true`) | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/{node_id}/data` | Gateway | Backend | 1 | No | Sensor Reading Packet | 1.1 Sensor Reading Packet |
| `lookoutgrid/sensors/{gateway_id}/{node_id}/status` | Gateway | Backend | 1 | Yes | Node Status JSON | - |
| `lookoutgrid/alerts/{gateway_id}/new` | Gateway | Backend | 2 | No | Alert Packet | 1.2 Alert Packet |
| `lookoutgrid/alerts/{gateway_id}/update` | Backend | Gateway | 2 | No | Alert Status Change | - |
| `lookoutgrid/alerts/{gateway_id}/resolved` | Backend | Gateway | 1 | No | Alert Resolved Event | - |
| `lookoutgrid/gateways/{gateway_id}/heartbeat` | Gateway | Backend | 0 | Yes | Gateway Heartbeat Packet | 1.4 Gateway Heartbeat Packet |
| `lookoutgrid/gateways/{gateway_id}/status` | Gateway (or Broker LWT) | Backend | 1 | Yes | Gateway Status (e.g., `{"status": "OFFLINE"}`) | - |
| `lookoutgrid/commands/{gateway_id}/config` | Backend | Gateway | 2 | No | Command Packet | 1.5 Command Packet |
| `lookoutgrid/commands/{gateway_id}/model-update` | Backend | Gateway | 2 | No | Command Packet | 1.5 Command Packet |
| `lookoutgrid/commands/{gateway_id}/{node_id}/config` | Backend | Gateway | 2 | No | Command Packet | 1.5 Command Packet |
| `lookoutgrid/commands/{gateway_id}/{node_id}/restart` | Backend | Gateway | 2 | No | Command Packet | 1.5 Command Packet |
| `lookoutgrid/system/broadcast` | Backend | All Gateways | 1 | No | Broadcast Message | - |

### Mosquitto Configuration

```yaml
# mosquitto.conf
listener 1883                       # Standard MQTT port
listener 8883                       # TLS encrypted (production)
protocol mqtt

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence (store messages for offline devices)
persistence true
persistence_location /var/lib/mosquitto/

# Last Will and Testament (detect gateway disconnect)
# Each gateway sets LWT on connect:
#   Topic: lookoutgrid/gateways/{gateway_id}/status
#   Payload: {"status": "OFFLINE"}
#   QoS: 1, Retain: true

# Retained messages
# Gateway heartbeat is retained so new subscribers
# immediately know gateway status without waiting

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
```

**Implementation Notes:**
- **Port 1883** is for development (no TLS).
- **Port 8883** is for production (TLS — configure later).
- **Persistence** is enabled so messages for offline gateways are stored.
- Each gateway must set an **LWT** (Last Will and Testament) on connect with topic `lookoutgrid/gateways/{gateway_id}/status` and payload `{"status": "OFFLINE"}`.
