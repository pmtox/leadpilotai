from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class LeadBase(BaseModel):
    business_type: Optional[str] = None
    product_count: Optional[int] = None
    budget: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    timeline: Optional[str] = None
    features: List[str] = []
    buying_intent: Optional[str] = "UNKNOWN"
    score: int = 0
    classification: str = "COLD"
    qualification_reason: Optional[str] = None
    followup_draft: Optional[str] = None

class LeadResponse(LeadBase):
    id: int
    customer_id: int
    conversation_id: Optional[int] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
