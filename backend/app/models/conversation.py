from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(30), default="active")  # active, completed, stopped
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)  # seconds
    summary = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")
    lead = relationship("Lead", back_populates="conversation", uselist=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    speaker = Column(String(20), nullable=False)  # "agent" or "customer"
    content = Column(Text, nullable=False)
    language = Column(String(20), default="English")
    timestamp = Column(DateTime, default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")
