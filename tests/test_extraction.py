import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.models.lead import Lead
from backend.app.models.conversation import Message
from backend.app.services.conversation_service import conversation_service
from backend.app.services.extraction_service import extraction_service
from backend.app.core.config import settings

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_english_doc_example_extraction():
    # Exactly matching document section 3.2 example
    sample_text = "I want to build an online clothing store. I have around 200 products and my budget is ₹80,000. I want to launch next month."
    data = extraction_service._extract_with_rules(sample_text)

    assert data["business_type"] == "Clothing"
    assert data["product_count"] == 200
    assert data["budget"] == 80000.0
    assert data["timeline"] == "Next month"
    assert data["buying_intent"] == "HIGH"

def test_hindi_extraction():
    hindi_text = "मुझे कपड़ों की ऑनलाइन दुकान शुरू करनी है, 150 उत्पाद हैं और बजट ₹50,000 है।"
    data = extraction_service._extract_with_rules(hindi_text)

    assert data["business_type"] == "Clothing"
    assert data["product_count"] == 150
    assert data["budget"] == 50000.0

def test_telugu_extraction_with_lakh():
    telugu_text = "నాకు ఎలక్ట్రానిక్స్ స్టోర్ కావాలి, 100 వస్తువులు, బడ్జెట్ 1.5 లక్ష."
    data = extraction_service._extract_with_rules(telugu_text)

    assert data["business_type"] == "Electronics"
    assert data["product_count"] == 100
    assert data["budget"] == 150000.0

def test_reported_call_details_are_extracted_as_a_range():
    text = (
        "Our budget is ₹60K–₹1L. We have 10 products and need UPI, credit card, "
        "Razorpay, and WhatsApp alerts. Please send me a proposal next week. "
        "My email is priya@example.com."
    )
    data = extraction_service._extract_with_rules(text)

    assert data["budget_min"] == 60000.0
    assert data["budget_max"] == 100000.0
    assert data["budget"] == 80000.0
    assert data["product_count"] == 10
    assert data["timeline"] == "Next week"
    assert data["buying_intent"] == "HIGH"
    assert data["email"] == "priya@example.com"
    assert "UPI Payments" in data["features"]
    assert "Credit/Debit Card Payments" in data["features"]
    assert "Razorpay Integration" in data["features"]
    assert "WhatsApp Notifications" in data["features"]

def test_product_count_with_thousands_separator():
    data = extraction_service._extract_with_rules(
        "I have 10,000 items in my clothing catalog."
    )

    assert data["product_count"] == 10000

def test_rule_extraction_fills_fields_omitted_by_llm(monkeypatch):
    history = [{
        "speaker": "customer",
        "content": "Budget ₹60K–₹1L, launch next week, email me at priya@example.com.",
    }]
    monkeypatch.setattr(extraction_service, "_extract_with_llm", lambda _, conversation_id=None: {
        "business_type": "Clothing",
        "buying_intent": "LOW",
    })
    monkeypatch.setattr(
        "backend.app.services.extraction_service.llm_service.is_live_provider_available",
        lambda: True,
    )
    monkeypatch.setattr(settings, "LLM_EXTRACTION_ENABLED", True)

    data = extraction_service.extract_from_transcript(history)

    assert data["budget_min"] == 60000.0
    assert data["budget_max"] == 100000.0
    assert data["timeline"] == "Next week"
    assert data["email"] == "priya@example.com"
    assert data["buying_intent"] == "HIGH"

def test_llm_extraction_is_skipped_by_default(monkeypatch):
    history = [{"speaker": "customer", "content": "I run a clothing business."}]
    monkeypatch.setattr(
        "backend.app.services.extraction_service.llm_service.is_live_provider_available",
        lambda: True,
    )
    monkeypatch.setattr(settings, "LLM_EXTRACTION_ENABLED", False)
    monkeypatch.setattr(
        extraction_service,
        "_extract_with_llm",
        lambda _, conversation_id=None: pytest.fail(
            "optional LLM extraction should be disabled by default"
        ),
    )

    data = extraction_service.extract_from_transcript(history)

    assert data["business_type"] == "Clothing"

def test_multi_turn_incremental_extraction(setup_db):
    db = setup_db
    cust = Customer(name="Vikram Patel", phone="+919123456789", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # Start conversation
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")

    # Turn 1: Business type
    conv = conversation_service.process_turn(db, conv.id, "I run a grocery store and want to sell groceries online.")
    lead = db.query(Lead).filter(Lead.conversation_id == conv.id).first()
    assert lead is not None
    assert "Grocery" in lead.business_type
    assert lead.budget is None

    # Turn 2: Budget & Features
    conv = conversation_service.process_turn(db, conv.id, "Our budget is ₹1,00,000 and we need UPI payments and delivery tracking.")
    db.refresh(lead)
    assert "Grocery" in lead.business_type
    assert lead.budget == 100000.0
    assert "Online Payments (UPI/Cards)" in lead.features
    assert "Delivery Tracking" in lead.features

    # Turn 3: Timeline & Product Count
    conv = conversation_service.process_turn(db, conv.id, "We have about 350 items and we must launch next month.")
    db.refresh(lead)
    assert lead.product_count == 350
    assert lead.timeline == "Next month"
    assert lead.buying_intent == "HIGH"

def test_email_is_saved_and_call_summary_draft_is_created(setup_db, monkeypatch):
    db = setup_db
    customer = Customer(
        name="Priya Sharma",
        phone="+919876543210",
        email="priya@example.com",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    conversation = conversation_service.start_conversation(db, customer.id, "English")
    conversation.messages.append(
        Message(
            speaker="customer",
            content="Budget ₹60K–₹1L, 10 products, launch next week. Please send a proposal.",
            language="English",
        )
    )
    db.commit()
    monkeypatch.setattr(
        extraction_service,
        "extract_from_transcript",
        lambda _, conversation_id=None: {
            "business_type": "Clothing",
            "product_count": 10,
            "budget": 80000.0,
            "budget_min": 60000.0,
            "budget_max": 100000.0,
            "timeline": "Next week",
            "features": ["UPI Payments", "WhatsApp Notifications"],
            "buying_intent": "HIGH",
            "language": "English",
            "email": "priya@example.com",
        },
    )

    lead = extraction_service.extract_and_update_lead(db, conversation.id)
    actions = [action for action in lead.customer.actions if action.action_type == "email_followup"]

    assert lead.budget_min == 60000.0
    assert lead.budget_max == 100000.0
    assert lead.customer.email == "priya@example.com"
    assert len(actions) == 1
    assert actions[0].status == "draft"
    assert actions[0].payload["recipient"] == "priya@example.com"
    assert "₹60,000–₹100,000" in actions[0].payload["message"]
    assert "WhatsApp Notifications" in actions[0].payload["message"]
    assert "Requested during the conversation" in actions[0].payload["message"]
