from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.conversation import Conversation
from backend.app.schemas.conversation import (
    ConversationStartRequest, MessageTurnRequest, ConversationResponse
)
from backend.app.services.conversation_service import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("/start", response_model=ConversationResponse)
def start_conversation(req: ConversationStartRequest, db: Session = Depends(get_db)):
    try:
        return conversation_service.start_conversation(
            db=db,
            customer_id=req.customer_id,
            initial_language=req.initial_language
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{conversation_id}/message", response_model=ConversationResponse)
def send_message(conversation_id: int, turn: MessageTurnRequest, db: Session = Depends(get_db)):
    try:
        return conversation_service.process_turn(
            db=db,
            conversation_id=conversation_id,
            message_text=turn.message,
            language=turn.language
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.post("/{conversation_id}/end", response_model=ConversationResponse)
def end_conversation(conversation_id: int, db: Session = Depends(get_db)):
    try:
        return conversation_service.end_conversation(db=db, conversation_id=conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.id.desc()).all()
