import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.services.conversation_service import conversation_service
from backend.app.services.llm_service import detect_language

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

