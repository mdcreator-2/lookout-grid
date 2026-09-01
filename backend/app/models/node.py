from sqlalchemy import Column, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from .base import Base

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String(30), primary_key=True)
    node_type = Column(String(20), nullable=False)
    gateway_id = Column(String(30), ForeignKey("gateways.gateway_id"))
    latitude = Column(Float(precision=10), nullable=False)
    longitude = Column(Float(precision=10), nullable=False)
    altitude_m = Column(Float)
    location_name = Column(String(200))
    sensors = Column(ARRAY(String))
    firmware_ver = Column(String(20))
    edge_model_ver = Column(String(50))
    power_source = Column(String(20), default='SOLAR')
    communication = Column(String(20), default='LORA')
    status = Column(String(20), default='ACTIVE')
    installed_date = Column(Date)
    last_seen_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    gateway = relationship("Gateway", back_populates="nodes")
    alerts = relationship("Alert", back_populates="primary_node")
