from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String(30), default="pending")
    scheduled_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    provider_reference = Column(String(100), nullable=True)

    customer = relationship("Customer", back_populates="actions")
