from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class LocationSchema(BaseModel):
    lat: float
    lng: float
    altitude_m: Optional[float] = None
    location_name: Optional[str] = None

class ReadingsSchema(BaseModel):
    water_level_m: Optional[float] = None
    rainfall_mm_hr: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    pm25_ugm3: Optional[float] = None
    pm10_ugm3: Optional[float] = None
    smoke_ppm: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    tds_ppm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    uv_index: Optional[float] = None
    co_ugm3: Optional[float] = None

class DeviceHealthSchema(BaseModel):
    battery_pct: Optional[int] = None
    solar_charging: Optional[bool] = None
    signal_strength_dbm: Optional[int] = None
    uptime_seconds: Optional[int] = None
    firmware_version: Optional[str] = None

class EdgeInferenceSchema(BaseModel):
    model_version: Optional[str] = None
    anomaly_detected: Optional[bool] = False
    anomaly_score: Optional[float] = None
    inference_time_ms: Optional[int] = None
    label: Optional[str] = None

class SensorReadingCreate(BaseModel):
    schema_version: str = "1.0"
    packet_type: str = "DATA"
    node_id: str
    gateway_id: str
    timestamp: datetime
    location: LocationSchema
    readings: ReadingsSchema
    device_health: DeviceHealthSchema
    edge_inference: Optional[EdgeInferenceSchema] = None

class SensorReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    time: datetime
    node_id: str
    readings: Optional[ReadingsSchema] = None
    anomaly_detected: Optional[bool] = None
    anomaly_score: Optional[float] = None

class SensorReadingBatch(BaseModel):
    readings: List[SensorReadingCreate]
