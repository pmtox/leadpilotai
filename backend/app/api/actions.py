"""
Actions API — CP-07 updated
Wires POST /api/actions/{id}/execute to WhatsApp service with draft fallback.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.action import Action
from backend.app.models.customer import Customer
from backend.app.services.email_service import email_service
from backend.app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/api/actions", tags=["actions"])

class ExecuteActionRequest(BaseModel):
    consent_confirmed: bool = False


def _action_dict(a: Action) -> Dict[str, Any]:
    return {
        "id": a.id,
        "customer_id": a.customer_id,
        "conversation_id": a.conversation_id,
        "action_type": a.action_type,
        "payload": a.payload,
        "status": a.status,
        "scheduled_at": a.scheduled_at,
        "executed_at": a.executed_at,
        "provider_reference": a.provider_reference,
    }


@router.get("")
def list_actions(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    actions = db.query(Action).order_by(Action.id.desc()).all()
    return [_action_dict(a) for a in actions]


@router.get("/{action_id}")
def get_action(action_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return _action_dict(action)


@router.post("/{action_id}/execute")
def execute_action(
    action_id: int,
    db: Session = Depends(get_db),
    request: Optional[ExecuteActionRequest] = None,
) -> Dict[str, Any]:
    """
    Execute an action.

    For whatsapp_followup actions:
      - Fetches customer phone number.
      - Calls WhatsApp service (live dispatch or draft fallback).
      - Updates action status and provider_reference in DB.

    For other action types: marks as executed.
    """
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status in ("sent", "delivered", "executed"):
        return {
            "message": f"Action already in terminal state: {action.status}",
            "action": _action_dict(action),
        }

    # --- WhatsApp follow-up ---
    if action.action_type == "whatsapp_followup":
        consent_confirmed = request.consent_confirmed if request else False
        customer = db.query(Customer).filter(Customer.id == action.customer_id).first()
        customer_phone = customer.phone if customer else None
        customer_name = customer.name if customer else "Customer"
        language = (action.payload or {}).get("language", "en")

        # Extract message body from payload
        message_body: str = (action.payload or {}).get(
            "followup_draft",
            (action.payload or {}).get("message", "Thank you for your interest!"),
        )

        # Optionally wrap in polite greeting / footer
        full_message = whatsapp_service.prepare_draft(
            customer_name=customer_name,
            message_body=message_body,
            language=language,
        )

        result = whatsapp_service.send_whatsapp_message(
            to_phone=customer_phone or "",
            message_text=full_message,
            action_id=action_id,
            consent_confirmed=consent_confirmed,
        )

        # Map WhatsApp service status → DB status
        status_map = {
            "sent":  "sent",
            "draft": "draft",
            "failed": "failed",
        }
        action.status = status_map.get(result["status"], "draft")
        if result.get("provider_reference"):
            action.provider_reference = result["provider_reference"]
        payload = dict(action.payload or {})
        payload["whatsapp_delivery_status"] = result["status"]
        if result.get("draft_text"):
            payload["followup_draft"] = result["draft_text"]
        if consent_confirmed:
            payload["consent_confirmed_at"] = datetime.now(timezone.utc).isoformat()
        action.payload = payload
        if result["status"] == "sent":
            action.executed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(action)

        return {
            "message": result.get("message", "Action processed"),
            "whatsapp_status": result["status"],
            "draft_text": result.get("draft_text"),
            "provider_reference": result.get("provider_reference"),
            "action": _action_dict(action),
        }

    if action.action_type == "email_followup":
        payload = dict(action.payload or {})
        result = email_service.send_email(
            recipient=payload.get("recipient"),
            subject=payload.get("subject", "Your project discussion summary"),
            body=payload.get("message", ""),
            consent_confirmed=request.consent_confirmed if request else False,
        )
        action.status = result["status"]
        payload["email_delivery_status"] = result["status"]
        if result.get("message"):
            payload["delivery_message"] = result["message"]
        action.payload = payload
        if result["status"] == "sent":
            action.executed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(action)
        return {
            "message": result["message"],
            "email_status": result["status"],
            "draft_text": result.get("draft_text"),
            "action": _action_dict(action),
        }

    # --- Generic action fallback ---
    action.status = "executed"
    action.executed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(action)

    return {
        "message": "Action marked as executed",
        "action": _action_dict(action),
    }


@router.post("/{action_id}/cancel")
def cancel_action(action_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Cancel a pending or draft action."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status in ("sent", "delivered", "executed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel action in terminal state: {action.status}",
        )
    action.status = "cancelled"
    db.commit()
    db.refresh(action)
    return {"message": "Action cancelled", "action": _action_dict(action)}
