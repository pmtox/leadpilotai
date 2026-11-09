from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    business_type = Column(String(100), nullable=True)
    product_count = Column(Integer, nullable=True)
    budget = Column(Float, nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    timeline = Column(String(100), nullable=True)
    features = Column(JSON, default=list)
    buying_intent = Column(String(20), default="UNKNOWN")
    score = Column(Integer, default=0)
    classification = Column(String(10), default="COLD")  # HOT, WARM, COLD
    qualification_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="leads")
    conversation = relationship("Conversation", back_populates="lead")
