from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.action import Action

router = APIRouter(prefix="/api/callbacks", tags=["callbacks"])

@router.get("")
def list_callbacks(db: Session = Depends(get_db)):
    callbacks = db.query(Action).filter(Action.action_type == "callback_scheduled").order_by(Action.scheduled_at.asc()).all()
    return [
        {
            "id": c.id,
            "customer_id": c.customer_id,
            "conversation_id": c.conversation_id,
            "payload": c.payload,
            "status": c.status,
            "scheduled_at": c.scheduled_at
        }
        for c in callbacks
    ]

