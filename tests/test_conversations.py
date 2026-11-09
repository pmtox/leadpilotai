from unittest.mock import MagicMock, patch
import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.services.conversation_service import conversation_service
from backend.app.services.llm_service import LLMService, detect_language, llm_service
from backend.app.core.config import settings
from backend.app.services.extraction_service import extraction_service

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_language_detection():
    assert detect_language("Hello, I want to build a website") == "English"
    assert detect_language("नमस्ते, मुझे ऑनलाइन स्टोर बनाना है") == "Hindi"
    assert detect_language("నమస్కారం, నాకు ఇ-కామర్స్ వెబ్‌సైట్ కావాలి") == "Telugu"
    assert detect_language("Namaste, mujhe dukan ke liye site chahiye") == "Hindi"
    assert detect_language("Namaskaram, nenu online business cheyali") == "Telugu"

def test_english_conversation_flow(setup_db):
    db = setup_db
    # Create test customer
    cust = Customer(name="Aarav Sharma", phone="+919876543210", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # 1. Start conversation
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")
    assert conv.status == "active"
    assert len(conv.messages) == 1
    assert "LeadPilot AI" in conv.messages[0].content
    assert conv.messages[0].speaker == "agent"

    # 2. First turn
    conv = conversation_service.process_turn(db, conv.id, "I want to sell handcrafted clothing items.")
    assert len(conv.messages) == 3  # greeting + user + agent
    assert conv.messages[1].speaker == "customer"
    assert conv.messages[2].speaker == "agent"

    # 3. Second turn (budget & products)
    conv = conversation_service.process_turn(db, conv.id, "I have around 150 products and my budget is ₹75,000.")
    assert len(conv.messages) == 5

    # 4. End conversation
    conv = conversation_service.end_conversation(db, conv.id)
    assert conv.status == "completed"
    assert conv.summary is not None

def test_hindi_conversation_flow(setup_db):
    db = setup_db
    cust = Customer(name="राजेश कुमार", phone="+919811122233", preferred_language="Hindi")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # 1. Start conversation in Hindi
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="Hindi")
    assert len(conv.messages) == 1
    assert "नमस्ते" in conv.messages[0].content

    # 2. Turn in Hindi
    conv = conversation_service.process_turn(db, conv.id, "मुझे कपड़ों की ऑनलाइन दुकान शुरू करनी है।")
    assert len(conv.messages) == 3
    # Check that agent reply contains Hindi text
    assert any('\u0900' <= c <= '\u097F' for c in conv.messages[2].content)

def test_telugu_conversation_flow(setup_db):
    db = setup_db
    cust = Customer(name="సురేష్ వర్మ", phone="+919844455566", preferred_language="Telugu")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # 1. Start conversation in Telugu
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="Telugu")
    assert len(conv.messages) == 1
    assert "నమస్కారం" in conv.messages[0].content

    # 2. Turn in Telugu
    conv = conversation_service.process_turn(db, conv.id, "నేను కిరాణా సామాను ఆన్‌లైన్‌లో విక్రయించాలనుకుంటున్నాను.")
    assert len(conv.messages) == 3
    # Check that agent reply contains Telugu text
    assert any('\u0C00' <= c <= '\u0C7F' for c in conv.messages[2].content)

def test_customer_opt_out(setup_db):
    db = setup_db
    cust = Customer(name="Busy Prospect", phone="+919999900000", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")
    conv = conversation_service.process_turn(db, conv.id, "I am not interested right now, please stop.")
    assert "time" in conv.messages[-1].content.lower() or "reach back" in conv.messages[-1].content.lower()

def test_fallback_does_not_repeat_timeline_question():
    history = [
        {"speaker": "agent", "content": "Are you looking to launch within the next few weeks or next month?"},
        {"speaker": "customer", "content": "I run a jewelry store with 100 items."},
        {"speaker": "agent", "content": "Which payment features do you need?"},
        {"speaker": "customer", "content": "I need UPI, credit cards, and Razorpay."},
        {"speaker": "agent", "content": "Are you looking to launch within the next few weeks or next month?"},
        {"speaker": "customer", "content": "I am looking for next week, very early."},
    ]

    requirements = extraction_service._extract_with_rules(
        " ".join(message["content"] for message in history if message["speaker"] == "customer")
    )
    reply = llm_service._intelligent_fallback_reply(history, "English")

    assert requirements["timeline"] == "Next week"
    assert "next month" not in reply.lower()
    assert "budget" in reply.lower()

def test_incomplete_turn_asks_only_next_missing_requirement(setup_db, monkeypatch):
    db = setup_db
    customer = Customer(
        name="Catalog Customer",
        phone="+919876543210",
        preferred_language="English",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    conversation = conversation_service.start_conversation(db, customer.id, "English")
    generated_by_llm = []
    monkeypatch.setattr(
        llm_service,
        "generate_reply",
        lambda **kwargs: generated_by_llm.append(kwargs) or "LLM response",
    )
    monkeypatch.setattr(llm_service, "is_live_provider_available", lambda: False)

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "I sell clothing and have 10,000 items.",
    )

    assert conversation.lead.product_count == 10000
    assert "budget" in conversation.messages[-1].content.lower()
    assert "timeline" not in conversation.messages[-1].content.lower()
    assert generated_by_llm == []

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "Our budget is ₹60K to ₹1L.",
    )
    assert "launch" in conversation.messages[-1].content.lower()
    assert "feature" not in conversation.messages[-1].content.lower()
    assert generated_by_llm == []

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "We need to launch next week.",
    )
    assert "feature" in conversation.messages[-1].content.lower()
    assert generated_by_llm == []

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "We need UPI, inventory, and WhatsApp order alerts.",
    )
    assert conversation.messages[-1].content == "LLM response"
    assert len(generated_by_llm) == 1

def test_project_catalog_and_numeric_budget_answers_advance_dialogue(setup_db, monkeypatch):
    db = setup_db
    customer = Customer(
        name="Priya Sharma",
        phone="+919876543210",
        preferred_language="English",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    conversation = conversation_service.start_conversation(db, customer.id, "English")
    monkeypatch.setattr(llm_service, "is_live_provider_available", lambda: False)

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "I sell clothing and have 50,000 project products.",
    )
    assert conversation.lead.product_count == 50000
    assert "budget" in conversation.messages[-1].content.lower()

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "$70,000",
    )
    assert "INR equivalent" in conversation.messages[-1].content

    conversation = conversation_service.process_turn(
        db,
        conversation.id,
        "70,000",
    )
    assert conversation.lead.budget == 70000
    assert "launch" in conversation.messages[-1].content.lower()

def test_duplicate_provider_reply_is_detected():
    history = [
        {"speaker": "agent", "content": "What is your launch timeline?"},
        {"speaker": "customer", "content": "Next week."},
    ]

    assert llm_service._repeats_previous_agent_reply(history, "  What is your launch timeline? ")

def test_groq_model_id_is_sent_without_legacy_replacement(monkeypatch):
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "choices": [{"message": {"content": "How many products will you list?"}}]
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value = response

    with patch("backend.app.services.llm_service.httpx.Client", return_value=client):
        llm_service._call_groq(
            [{"speaker": "customer", "content": "Next week."}],
            "English",
            "You are a sales assistant.",
        )

    assert client.post.call_args.kwargs["json"]["model"] == "openai/gpt-oss-120b"

def test_groq_truncated_reply_is_rejected(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "choices": [{
            "message": {"content": "Thanks, I have noted your"},
            "finish_reason": "length",
        }]
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value = response

    with patch("backend.app.services.llm_service.httpx.Client", return_value=client):
        reply = llm_service._call_groq(
            [{"speaker": "customer", "content": "Here are all my requirements."}],
            "English",
            "You are a sales assistant.",
        )

    assert reply is None

def test_reply_generation_respects_per_conversation_request_cap(monkeypatch):
    service = LLMService()
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "DEFAULT_LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "LLM_MAX_CALLS_PER_CONVERSATION", 1)
    monkeypatch.setattr(settings, "LLM_MAX_CALLS_PER_DAY", 10)
    provider_call = MagicMock(return_value="A tailored response.")
    monkeypatch.setattr(service, "_call_gemini", provider_call)
    messages = [{"speaker": "customer", "content": "I have shared my requirements."}]

    first_reply = service.generate_reply(messages, conversation_id=123)
    second_reply = service.generate_reply(messages, conversation_id=123)

    assert first_reply == "A tailored response."
    assert provider_call.call_count == 1
    assert second_reply != "A tailored response."

def test_reply_generation_respects_daily_request_cap(monkeypatch):
    service = LLMService()
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "DEFAULT_LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "LLM_MAX_CALLS_PER_CONVERSATION", 10)
    monkeypatch.setattr(settings, "LLM_MAX_CALLS_PER_DAY", 1)
    provider_call = MagicMock(return_value="A tailored response.")
    monkeypatch.setattr(service, "_call_gemini", provider_call)
    messages = [{"speaker": "customer", "content": "I have shared my requirements."}]

    service.generate_reply(messages)
    service.generate_reply(messages)

    assert provider_call.call_count == 1
