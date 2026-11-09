import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.models.lead import Lead
from backend.app.models.action import Action
from backend.app.services.lead_scoring import lead_scoring_engine
from backend.app.services.conversation_service import conversation_service

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_hot_lead_scoring():
    lead_data = {
        "business_type": "Clothing",
        "product_count": 200,
        "budget": 80000.0,
        "timeline": "Next month",
        "features": ["Online Payments (UPI/Cards)", "Delivery Tracking"],
        "buying_intent": "HIGH"
    }
    score, classification, reason = lead_scoring_engine.calculate_score(lead_data, turn_count=3)
    # 30 (intent) + 25 (budget) + 15 (timeline) + 15 (clarity) + 10 (engagement) = 95
    assert score >= 70
    assert classification == "HOT"
    assert "HOT" in reason
    assert "High buying intent" in reason

def test_warm_lead_scoring():
    lead_data = {
        "business_type": "Grocery",
        "product_count": 50,
        "budget": 25000.0,
        "timeline": None,
        "features": [],
        "buying_intent": "MEDIUM"
    }
    score, classification, reason = lead_scoring_engine.calculate_score(lead_data, turn_count=2)
    # 15 (intent) + 15 (budget < 50k) + 0 (timeline) + 10 (clarity) + 5 (engagement) = 45
    assert 40 <= score < 70
    assert classification == "WARM"

def test_cold_lead_scoring():
    lead_data = {
        "business_type": None,
        "product_count": None,
        "budget": None,
        "timeline": None,
        "features": [],
        "buying_intent": "LOW"
    }
    score, classification, reason = lead_scoring_engine.calculate_score(lead_data, turn_count=1)
    assert score < 40
    assert classification == "COLD"

def test_personalized_followup_generation():
    lead_data = {
        "business_type": "Clothing",
        "product_count": 200,
        "budget": 80000.0,
        "timeline": "Next month",
        "features": ["UPI payments", "delivery tracking"]
    }

    # English
    msg_en = lead_scoring_engine.generate_followup_message("Priya", lead_data, language="English")
    assert "Priya" in msg_en
    assert "Clothing" in msg_en
    assert "80,000" in msg_en

    # Hindi
    msg_hi = lead_scoring_engine.generate_followup_message("राजेश", lead_data, language="Hindi")
    assert "राजेश" in msg_hi
    assert "LeadPilot AI" in msg_hi

    # Telugu
    msg_te = lead_scoring_engine.generate_followup_message("సురేష్", lead_data, language="Telugu")
    assert "సురేష్" in msg_te
    assert "LeadPilot AI" in msg_te

def test_lead_qualification_end_to_end(setup_db):
    db = setup_db
    cust = Customer(name="Ananya Verma", phone="+919876500000", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")

    # Turn 1
    conv = conversation_service.process_turn(db, conv.id, "I want to create an online fashion clothing store.")
    # Turn 2
    conv = conversation_service.process_turn(db, conv.id, "I have 200 items, my budget is ₹80,000, and I need payments and shipping.")
    # Turn 3
    conv = conversation_service.process_turn(db, conv.id, "We must launch next month for sure.")

    lead = db.query(Lead).filter(Lead.conversation_id == conv.id).first()
    assert lead is not None
    assert lead.classification == "HOT"
    assert lead.score >= 70

    # Verify drafted follow-up Action
    action = db.query(Action).filter(Action.conversation_id == conv.id).first()
    assert action is not None
    assert action.action_type == "whatsapp_followup"
    assert action.status == "draft"
    assert "Ananya" in action.payload.get("message", "")
