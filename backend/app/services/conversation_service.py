"""Conversation Service managing dialogue state, LLM turn-taking, and multilingual persistence."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.conversation import Conversation, Message
from backend.app.models.customer import Customer
from backend.app.services.llm_service import llm_service, detect_language

GREETINGS = {
    "English": "Hello! I am LeadPilot AI. I understand you're looking to build an e-commerce website. Do you have a couple of minutes to discuss your requirements?",
    "Hindi": "नमस्ते! मैं LeadPilot AI हूँ। मुझे पता चला है कि आप एक ई-कॉमर्स वेबसाइट बनाना चाहते हैं। क्या आपके पास अपनी आवश्यकताओं पर चर्चा करने के लिए कुछ मिनट हैं?",
    "Telugu": "నమస్కారం! నేను LeadPilot AI. మీరు ఇ-కామర్స్ వెబ్‌సైట్ నిర్మించాలనుకుంటున్నారని తెలిసింది. మీ అవసరాల గురించి మాట్లాడటానికి మీకు రెండు నిమిషాలు సమయం ఉందా?"
}

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ConversationService:
    def start_conversation(self, db: Session, customer_id: int, initial_language: Optional[str] = None) -> Conversation:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        conv = Conversation(
            customer_id=customer.id,
            status="active",
            started_at=utc_now()
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        lang = initial_language or customer.preferred_language or "English"
        greeting_text = GREETINGS.get(lang, GREETINGS["English"])

        greeting_msg = Message(
            conversation_id=conv.id,
            speaker="agent",
            content=greeting_text,
            language=lang,
            timestamp=utc_now()
        )
        db.add(greeting_msg)
        db.commit()
        db.refresh(conv)
        return conv

    def process_turn(
        self,
        db: Session,
        conversation_id: int,
        message_text: str,
        language: Optional[str] = None
    ) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError("Conversation not found")

        # Determine language (fallback to customer preference or English)
        customer = conv.customer
        fallback_lang = language or (customer.preferred_language if customer else "English")
        detected_lang = detect_language(message_text, fallback_lang=fallback_lang)

        # 1. Save customer turn to DB
        user_msg = Message(
            conversation_id=conv.id,
            speaker="customer",
            content=message_text,
            language=detected_lang,
            timestamp=utc_now()
        )
        db.add(user_msg)
        db.commit()

        # 2. Reconstruct entire conversation context for LLM
        db_messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.timestamp.asc()).all()
        history = [
            {"speaker": m.speaker, "content": m.content, "language": m.language}
            for m in db_messages
        ]

        # 3. Generate context-aware sales reply from LLM
        agent_reply_text = llm_service.generate_reply(
            messages=history,
            language=detected_lang
        )

        # 4. Save agent turn to DB
        agent_msg = Message(
            conversation_id=conv.id,
            speaker="agent",
            content=agent_reply_text,
            language=detected_lang,
            timestamp=utc_now()
        )
        db.add(agent_msg)
        db.commit()
        db.refresh(conv)

        return conv

    def end_conversation(self, db: Session, conversation_id: int) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError("Conversation not found")

        conv.status = "completed"
        conv.ended_at = utc_now()
        if conv.started_at:
            # Handle tz-aware or naive subtraction safely
            started = conv.started_at
            if started.tzinfo is None and conv.ended_at.tzinfo is not None:
                started = started.replace(tzinfo=timezone.utc)
            conv.duration = int((conv.ended_at - started).total_seconds())

        turn_count = len(conv.messages)
        conv.summary = f"Conversation completed with {turn_count} turns recorded."
        db.commit()
        db.refresh(conv)
        return conv

conversation_service = ConversationService()
