from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Gateway(Base):
    __tablename__ = "gateways"

    gateway_id = Column(String(30), primary_key=True)
    latitude = Column(Float(precision=10), nullable=False)
    longitude = Column(Float(precision=10), nullable=False)
    location_name = Column(String(200))
    connectivity = Column(String(20), default='WIFI')
    status = Column(String(20), default='ACTIVE')
    ml_model_ver = Column(String(50))
    total_nodes = Column(Integer, default=0)
    last_heartbeat = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    nodes = relationship("Node", back_populates="gateway")
    alerts = relationship("Alert", back_populates="gateway")
