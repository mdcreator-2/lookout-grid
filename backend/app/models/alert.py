from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import Base

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(30), primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(20), nullable=False)
    gateway_id = Column(String(30), ForeignKey("gateways.gateway_id"))
    primary_node_id = Column(String(30), ForeignKey("nodes.node_id"))
    
    alert_level = Column(String(10), nullable=False)
    alert_type = Column(String(30), nullable=False)
    alert_subtype = Column(String(50))
    
    confidence = Column(Float, nullable=False)
    description = Column(String)
    
    affected_lat = Column(Float)
    affected_lng = Column(Float)
    affected_radius_km = Column(Float)
    affected_area_name = Column(String(200))
    
    model_name = Column(String(50))
    model_layer = Column(String(20))
    prediction_data = Column(JSONB)
    
    status = Column(String(20), default='ACTIVE')
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    notifications_sent = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gateway = relationship("Gateway", back_populates="alerts")
    primary_node = relationship("Node", back_populates="alerts")
