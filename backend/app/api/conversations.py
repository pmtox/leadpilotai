from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.customer import Customer
from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.conversation import (
    ConversationStartRequest, MessageTurnRequest, ConversationResponse, MessageResponse
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

GREETINGS = {
    "English": "Hello! I am LeadPilot AI. I understand you're looking to build an e-commerce website. Do you have a couple of minutes to discuss your requirements?",
    "Hindi": "नमस्ते! मैं LeadPilot AI हूँ। मुझे पता चला है कि आप एक ई-कॉमर्स वेबसाइट बनाना चाहते हैं। क्या आपके पास अपनी आवश्यकताओं पर चर्चा करने के लिए कुछ मिनट हैं?",
    "Telugu": "నమస్కారం! నేను LeadPilot AI. మీరు ఇ-కామర్స్ వెబ్‌సైట్ నిర్మించాలనుకుంటున్నారని తెలిసింది. మీ అవసరాల గురించి మాట్లాడటానికి మీకు రెండు నిమిషాలు సమయం ఉందా?"
}

@router.post("/start", response_model=ConversationResponse)
def start_conversation(req: ConversationStartRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    conversation = Conversation(
        customer_id=customer.id,
        status="active",
        started_at=datetime.utcnow()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    lang = req.initial_language or customer.preferred_language or "English"
    greeting_text = GREETINGS.get(lang, GREETINGS["English"])

    greeting_msg = Message(
        conversation_id=conversation.id,
        speaker="agent",
        content=greeting_text,
        language=lang,
        timestamp=datetime.utcnow()
    )
    db.add(greeting_msg)
    db.commit()
    db.refresh(conversation)

    return conversation

@router.post("/{conversation_id}/message", response_model=ConversationResponse)
def send_message(conversation_id: int, turn: MessageTurnRequest, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    lang = turn.language or "English"

    # Save customer message
    user_msg = Message(
        conversation_id=conv.id,
        speaker="customer",
        content=turn.message,
        language=lang,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()

    # Initial rule-based / MVP conversational response (Hour 1 foundation)
    agent_reply = f"Thank you for sharing that. Could you tell me more about your expected product count and launch timeline?"
    if "hindi" in lang.lower() or any('\u0900' <= c <= '\u097F' for c in turn.message):
        agent_reply = "धन्यवाद! क्या आप मुझे अपने उत्पादों की संख्या और अपने लक्षित बजट के बारे में बता सकते हैं?"
        lang = "Hindi"
    elif "telugu" in lang.lower() or any('\u0C00' <= c <= '\u0C7F' for c in turn.message):
        agent_reply = "ధన్యవాదాలు! మీ ఉత్పత్తుల సంఖ్య మరియు మీ బడ్జెట్ ఎంత ఉంటుందో చెప్పగలరా?"
        lang = "Telugu"

    agent_msg = Message(
        conversation_id=conv.id,
        speaker="agent",
        content=agent_reply,
        language=lang,
        timestamp=datetime.utcnow()
    )
    db.add(agent_msg)
    db.commit()
    db.refresh(conv)

    return conv

@router.post("/{conversation_id}/end", response_model=ConversationResponse)
def end_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "completed"
    conv.ended_at = datetime.utcnow()
    if conv.started_at:
        conv.duration = int((conv.ended_at - conv.started_at).total_seconds())
    conv.summary = "Conversation ended. Lead details recorded."

    db.commit()
    db.refresh(conv)
    return conv

@router.get("", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.id.desc()).all()
