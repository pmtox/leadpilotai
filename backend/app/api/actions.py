from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.action import Action

router = APIRouter(prefix="/api/actions", tags=["actions"])

@router.get("")
def list_actions(db: Session = Depends(get_db)):
    actions = db.query(Action).order_by(Action.id.desc()).all()
    return [
        {
            "id": a.id,
            "customer_id": a.customer_id,
            "conversation_id": a.conversation_id,
            "action_type": a.action_type,
            "payload": a.payload,
            "status": a.status,
            "scheduled_at": a.scheduled_at,
            "executed_at": a.executed_at,
            "provider_reference": a.provider_reference
        }
        for a in actions
    ]

@router.post("/{action_id}/execute")
def execute_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "executed"
    db.commit()
    db.refresh(action)
    return {"message": "Action marked as executed", "action_id": action.id, "status": action.status}
