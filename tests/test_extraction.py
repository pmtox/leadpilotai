import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.models.lead import Lead
from backend.app.services.conversation_service import conversation_service
from backend.app.services.extraction_service import extraction_service

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
    assert lead.business_type == "Grocery"
    assert lead.budget is None

    # Turn 2: Budget & Features
    conv = conversation_service.process_turn(db, conv.id, "Our budget is ₹1,00,000 and we need UPI payments and delivery tracking.")
    db.refresh(lead)
    assert lead.business_type == "Grocery"
    assert lead.budget == 100000.0
    assert "Online Payments (UPI/Cards)" in lead.features
    assert "Delivery Tracking" in lead.features

    # Turn 3: Timeline & Product Count
    conv = conversation_service.process_turn(db, conv.id, "We have about 350 items and we must launch next month.")
    db.refresh(lead)
    assert lead.product_count == 350
    assert lead.timeline == "Next month"
    assert lead.buying_intent == "HIGH"
