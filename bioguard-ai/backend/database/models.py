"""Database models for BioGuard AI."""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON
from datetime import datetime
import uuid
from database.db import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "analyzer" or "pi_sender"
    device_id = Column(String, nullable=True)  # For pi_sender: "RPI5-UNIT-001"
    village_id = Column(String, nullable=True)  # For pi_sender: "MH_SHP"
    village_name = Column(String, nullable=True)  # For pi_sender: "Shirpur"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Alert(Base):
    """Alert model for disease outbreak alerts."""
    
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.now)
    village_id = Column(String, nullable=False)
    village_name = Column(String, nullable=False)
    alert_level = Column(String, nullable=False)  # baseline/low/medium/high/critical
    risk_score = Column(Float, nullable=False)
    trigger_reason = Column(String, nullable=False)
    predicted_disease = Column(String, nullable=False)
    cases_at_risk = Column(Integer, default=0)
    triggered_by_sensor = Column(Boolean, default=False)
    sensor_device_id = Column(String, nullable=True)
    sensor_reading_summary = Column(String, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    resources_required = Column(JSON, nullable=True)
    notification_sent = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    action_taken = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
