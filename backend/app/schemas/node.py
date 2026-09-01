from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class NodeCreate(BaseModel):
    node_id: str
    node_type: str
    gateway_id: Optional[str] = None
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    location_name: Optional[str] = None
    sensors: Optional[List[str]] = None
    firmware_ver: Optional[str] = None
    edge_model_ver: Optional[str] = None
    power_source: Optional[str] = "SOLAR"
    communication: Optional[str] = "LORA"
    status: Optional[str] = "ACTIVE"
    installed_date: Optional[date] = None

class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    node_id: str
    node_type: str
    gateway_id: Optional[str] = None
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    location_name: Optional[str] = None
    sensors: Optional[List[str]] = None
    firmware_ver: Optional[str] = None
    edge_model_ver: Optional[str] = None
    power_source: Optional[str] = None
    communication: Optional[str] = None
    status: Optional[str] = None
    installed_date: Optional[date] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    latest_reading: Optional[Dict[str, Any]] = None

class NodeUpdate(BaseModel):
    firmware_ver: Optional[str] = None
    edge_model_ver: Optional[str] = None
    status: Optional[str] = None
