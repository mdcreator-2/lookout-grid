from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, SmallInteger
from sqlalchemy import PrimaryKeyConstraint
from .base import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        PrimaryKeyConstraint('time', 'node_id'),
    )

    time = Column(DateTime(timezone=True), nullable=False)
    node_id = Column(String(30), nullable=False)
    gateway_id = Column(String(30))
    
    water_level_m = Column(Float)
    rainfall_mm_hr = Column(Float)
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    pressure_hpa = Column(Float)
    pm25_ugm3 = Column(Float)
    pm10_ugm3 = Column(Float)
    smoke_ppm = Column(Float)
    soil_moisture_pct = Column(Float)
    tds_ppm = Column(Float)
    wind_speed_kmh = Column(Float)
    uv_index = Column(Float)
    co_ugm3 = Column(Float)
    
    battery_pct = Column(SmallInteger)
    solar_charging = Column(Boolean)
    signal_strength_dbm = Column(SmallInteger)
    uptime_seconds = Column(Integer)
    firmware_version = Column(String(50))
    
    model_version = Column(String(50))
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Float)
    inference_time_ms = Column(Integer)
    edge_label = Column(String(50))
