import pytest
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.models.action import Action
from backend.app.services.conversation_service import conversation_service
from backend.app.api.customers import list_customers
from backend.app.api.conversations import list_conversations
from backend.app.api.leads import list_leads
from backend.app.api.actions import list_actions, execute_action
from backend.app.api.callbacks import list_callbacks

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_dashboard_api_endpoints(setup_db):
    db = setup_db
    # Create customer
    cust = Customer(name="Dashboard Prospect", phone="+919900011222", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # Start conversation
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")
    conv = conversation_service.process_turn(db, conv.id, "I want a jewelry website with 300 pieces and ₹1,50,000 budget.")

    # 1. Test customers listing
    customers = list_customers(db)
    assert len(customers) >= 1
    assert any(c.name == "Dashboard Prospect" for c in customers)

    # 2. Test conversations listing
    conversations = list_conversations(db)
    assert len(conversations) >= 1
    assert any(c.id == conv.id for c in conversations)

    # 3. Test leads listing
    leads = list_leads(db)
    assert len(leads) >= 1
    lead = next(l for l in leads if l.conversation_id == conv.id)
    assert lead.score > 0
    assert lead.classification in ("HOT", "WARM", "COLD")

    # 4. Test actions listing and execution
    actions = list_actions(db)
    assert len(actions) >= 1
    action = next(a for a in actions if a["conversation_id"] == conv.id)
    assert action["status"] in ("draft", "pending", "executed")

    # Execute action — CP-07: response now wraps action inside "action" key
    exec_res = execute_action(action["id"], db)
    result_status = exec_res.get("action", {}).get("status") or exec_res.get("whatsapp_status")
    assert result_status in ("draft", "sent", "executed", "failed")

    # 5. Test callbacks listing
    callback = Action(
        customer_id=cust.id,
        conversation_id=conv.id,
        action_type="callback_scheduled",
        payload={"note": "Call customer next Monday"},
        status="pending"
    )
    db.add(callback)
    db.commit()

    callbacks = list_callbacks(db)
    assert len(callbacks) >= 1

