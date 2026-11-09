from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False, index=True)
    preferred_language = Column(String(20), default="English")
    created_at = Column(DateTime, default=utc_now)

    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="customer", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="customer", cascade="all, delete-orphan")
