from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.core.auth import get_current_user
from backend.app.database.connection import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.customer import Customer
from backend.app.models.user import User
from backend.app.schemas.conversation import (
    AdminConversationResponse,
    ConversationResponse,
    ConversationStartRequest,
    MessageTurnRequest,
)
from backend.app.services.conversation_service import conversation_service
from backend.app.services.speech_service import speech_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _owned_customer(db: Session, user: User) -> Customer:
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if customer is None:
        raise HTTPException(status_code=409, detail="Account profile not found")
    return customer


def _owned_conversation(db: Session, conversation_id: int, user: User) -> Conversation:
    customer = _owned_customer(db, user)
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.customer_id == customer.id,
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _conversation_response(conversation: Conversation, user: User) -> Dict[str, Any]:
    response_model = (
        AdminConversationResponse
        if user.role == "admin"
        else ConversationResponse
    )
    return response_model.model_validate(conversation).model_dump()


@router.post("/start")
def start_conversation(
    req: ConversationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = _owned_customer(db, current_user)
    if req.customer_id != customer.id:
        raise HTTPException(status_code=403, detail="Cannot start a conversation for another account")
    try:
        conversation = conversation_service.start_conversation(
            db=db,
            customer_id=req.customer_id,
            initial_language=req.initial_language
        )
        return _conversation_response(conversation, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{conversation_id}/message")
def send_message(
    conversation_id: int,
    turn: MessageTurnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_conversation(db, conversation_id, current_user)
    try:
        conversation = conversation_service.process_turn(
            db=db,
            conversation_id=conversation_id,
            message_text=turn.message,
            language=turn.language
        )
        return _conversation_response(conversation, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{conversation_id}/audio")
async def process_audio_turn(
    conversation_id: int,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_conversation(db, conversation_id, current_user)
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty")
        transcription = speech_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.wav",
            language=language
        )
        if not transcription:
            raise HTTPException(status_code=400, detail="Audio transcription failed")

        conversation = conversation_service.process_turn(
            db=db,
            conversation_id=conversation_id,
            message_text=transcription,
            language=language
        )
        return _conversation_response(conversation, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _owned_conversation(db, conversation_id, current_user)
    return _conversation_response(conv, current_user)

@router.post("/{conversation_id}/end")
def end_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_conversation(db, conversation_id, current_user)
    try:
        conversation = conversation_service.end_conversation(db=db, conversation_id=conversation_id)
        return _conversation_response(conversation, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Conversation)
    if current_user.role != "admin":
        customer = _owned_customer(db, current_user)
        query = query.filter(Conversation.customer_id == customer.id)
    conversations = query.order_by(Conversation.id.desc()).all()
    return [_conversation_response(conversation, current_user) for conversation in conversations]
