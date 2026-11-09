from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CustomerBase(BaseModel):
    name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="Customer phone number")
    email: Optional[str] = Field(
        None,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Customer email address for follow-up summaries",
    )
    preferred_language: Optional[str] = Field("English", description="Preferred language (English, Hindi, Telugu)")

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
