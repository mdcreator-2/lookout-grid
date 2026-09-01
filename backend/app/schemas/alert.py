from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class AlertCreate(BaseModel):
    alert_id: str
    timestamp: datetime
    source: str
    gateway_id: Optional[str] = None
    primary_node_id: Optional[str] = None
    alert_level: str
    alert_type: str
    alert_subtype: Optional[str] = None
    confidence: float
    description: Optional[str] = None
    affected_lat: Optional[float] = None
    affected_lng: Optional[float] = None
    affected_radius_km: Optional[float] = None
    affected_area_name: Optional[str] = None
    model_name: Optional[str] = None
    model_layer: Optional[str] = None
    prediction_data: Optional[Dict[str, Any]] = None

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    alert_id: str
    timestamp: datetime
    source: str
    gateway_id: Optional[str] = None
    primary_node_id: Optional[str] = None
    alert_level: str
    alert_type: str
    alert_subtype: Optional[str] = None
    confidence: float
    description: Optional[str] = None
    affected_lat: Optional[float] = None
    affected_lng: Optional[float] = None
    affected_radius_km: Optional[float] = None
    affected_area_name: Optional[str] = None
    model_name: Optional[str] = None
    model_layer: Optional[str] = None
    prediction_data: Optional[Dict[str, Any]] = None
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    notifications_sent: Optional[Dict[str, Any]] = None
    created_at: datetime

class AlertAcknowledge(BaseModel):
    acknowledged_by: str

class AlertListFilter(BaseModel):
    status: Optional[str] = None
    level: Optional[str] = None
    type: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
