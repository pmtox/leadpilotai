import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    business_type = Column(String(100), nullable=True)
    product_count = Column(Integer, nullable=True)
    budget = Column(Float, nullable=True)
    timeline = Column(String(100), nullable=True)
    features = Column(JSON, default=list)  # list of feature strings
    buying_intent = Column(String(20), default="UNKNOWN")
    score = Column(Integer, default=0)
    classification = Column(String(10), default="COLD")  # HOT, WARM, COLD
    qualification_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="leads")
    conversation = relationship("Conversation", back_populates="lead")
