from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15))
    role = Column(String(30), nullable=False)
    organization = Column(String(200))
    alert_preferences = Column(JSONB)
    fcm_token = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
