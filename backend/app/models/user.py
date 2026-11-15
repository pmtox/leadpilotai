from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(254), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    picture = Column(String(500), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=utc_now)

    customer = relationship("Customer", back_populates="user", uselist=False)
