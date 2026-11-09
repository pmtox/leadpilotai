"""Conversation Service managing dialogue state, LLM turn-taking, and multilingual persistence."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.conversation import Conversation, Message
from backend.app.models.customer import Customer
from backend.app.models.action import Action
from backend.app.services.llm_service import llm_service, detect_language
from backend.app.services.extraction_service import extraction_service
from backend.app.services.email_service import email_service

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

        # Keep requirement gathering deterministic so the agent asks for only
        # the next missing field instead of inventing details or recap content.
        requirements = extraction_service.extract_rules_from_history(history)
        next_question = llm_service._next_missing_requirement_question(
            requirements,
            detected_lang,
        )
        if next_question:
            agent_reply_text = llm_service._intelligent_fallback_reply(
                history,
                detected_lang,
            )
        else:
            agent_reply_text = llm_service.generate_reply(
                messages=history,
                language=detected_lang,
                conversation_id=conv.id,
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

        # 5. Extract newly available structured requirements & update Lead
        extraction_service.extract_and_update_lead(db, conv.id)

        db.refresh(conv)
        return conv

    def end_conversation(self, db: Session, conversation_id: int) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError("Conversation not found")

        conv.status = "completed"
        conv.ended_at = utc_now()
        if conv.started_at:
            started = conv.started_at
            if started.tzinfo is None and conv.ended_at.tzinfo is not None:
                started = started.replace(tzinfo=timezone.utc)
            conv.duration = int((conv.ended_at - started).total_seconds())

        turn_count = len(conv.messages)
        conv.summary = f"Conversation completed with {turn_count} turns recorded."
        db.commit()

        # Refresh the recap with the complete transcript, then send it if an
        # email address was supplied. EmailService retains a draft if SMTP is
        # unavailable or delivery fails.
        extraction_service.extract_and_update_lead(db, conv.id)
        email_action = db.query(Action).filter(
            Action.conversation_id == conv.id,
            Action.action_type == "email_followup",
        ).first()
        if email_action and email_action.status in ("draft", "pending"):
            payload = dict(email_action.payload or {})
            result = email_service.send_email(
                recipient=payload.get("recipient"),
                subject=payload.get("subject", "Your project discussion summary"),
                body=payload.get("message", ""),
                consent_confirmed=True,
            )
            email_action.status = result["status"]
            payload["email_delivery_status"] = result["status"]
            payload["delivery_message"] = result["message"]
            email_action.payload = payload
            if result["status"] == "sent":
                email_action.executed_at = utc_now()
            db.commit()

        db.refresh(conv)
        return conv

conversation_service = ConversationService()
