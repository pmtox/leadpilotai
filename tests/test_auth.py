from fastapi.testclient import TestClient
import pytest
from backend.app.api import auth as auth_api
from backend.app.core.auth import get_current_user
from backend.app.core.config import settings
from backend.app.database.base import Base
from backend.app.database.connection import SessionLocal, engine
from backend.app.main import app
from backend.app.models.conversation import Conversation
from backend.app.models.customer import Customer
from backend.app.models.lead import Lead
from backend.app.models.user import User
import uuid
from backend.app.services.conversation_service import conversation_service


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_google_callback_creates_account_and_customer_session(client, db, monkeypatch):
    class GoogleClient:
        async def authorize_access_token(self, request):
            return {
                "userinfo": {
                    "sub": "google-user-auth-test",
                    "email": "auth-test@example.test",
                    "email_verified": True,
                    "name": "Auth Test User",
                    "picture": "https://example.test/avatar.png",
                }
            }

    monkeypatch.setattr(settings, "ADMIN_EMAILS", "auth-test@example.test")
    monkeypatch.setattr(auth_api, "get_google_client", lambda: GoogleClient())

    response = client.get("/api/auth/google/callback", follow_redirects=False)
    assert response.status_code == 303

    profile = client.get("/api/auth/me")
    assert profile.status_code == 200
    assert profile.json()["email"] == "auth-test@example.test"
    assert profile.json()["role"] == "admin"

    user = db.query(User).filter(User.google_sub == "google-user-auth-test").one()
    customer = db.query(Customer).filter(Customer.user_id == user.id).one()
    assert customer.email == user.email
    assert customer.name == user.name

    db.delete(customer)
    db.delete(user)
    db.commit()


def test_admin_routes_reject_regular_users(client, monkeypatch):
    user = User(
        id=987654,
        google_sub="regular-user-auth-test",
        email="regular-user@example.test",
        name="Regular User",
        role="user",
    )
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "")
    app.dependency_overrides[get_current_user] = lambda: user

    for path in ("/api/customers", "/api/leads", "/api/actions", "/api/callbacks"):
        response = client.get(path)
        assert response.status_code == 403


def test_conversation_response_hides_lead_data_from_regular_users(client, db, monkeypatch):
    user = User(
        google_sub="conversation-user-auth-test",
        email="conversation-user@example.test",
        name="Conversation User",
        role="user",
    )
    db.add(user)
    db.flush()
    customer = Customer(
        name=user.name,
        phone="",
        email=user.email,
        user_id=user.id,
    )
    db.add(customer)
    db.flush()
    conversation = Conversation(customer_id=customer.id, status="active")
    db.add(conversation)
    db.flush()
    db.add(
        Lead(
            customer_id=customer.id,
            conversation_id=conversation.id,
            score=95,
            classification="HOT",
            buying_intent="HIGH",
            qualification_reason="Internal qualification data",
        )
    )
    db.commit()

    monkeypatch.setattr(settings, "ADMIN_EMAILS", "")
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get(f"/api/conversations/{conversation.id}")
    assert response.status_code == 200
    assert "lead" not in response.json()

    other_user = User(
        google_sub="other-conversation-user-auth-test",
        email="other-conversation-user@example.test",
        name="Other User",
    )
    db.add(other_user)
    db.flush()
    other_customer = Customer(
        name=other_user.name,
        phone="",
        email=other_user.email,
        user_id=other_user.id,
    )
    db.add(other_customer)
    db.flush()
    other_conversation = Conversation(customer_id=other_customer.id, status="active")
    db.add(other_conversation)
    db.commit()
    other_response = client.get(f"/api/conversations/{other_conversation.id}")
    assert other_response.status_code == 404

    db.delete(db.query(Lead).filter(Lead.conversation_id == conversation.id).one())
    db.delete(conversation)
    db.delete(other_conversation)
    db.delete(other_customer)
    db.delete(other_user)
    db.delete(customer)
    db.delete(user)
    db.commit()


def test_admin_conversation_list_includes_all_customers_and_lead_data(client, db, monkeypatch):
    suffix = uuid.uuid4().hex
    admin = User(
        google_sub=f"admin-list-{suffix}",
        email=f"admin-list-{suffix}@example.test",
        name="Admin",
        role="admin",
    )
    customer_user = User(
        google_sub=f"customer-list-{suffix}",
        email=f"customer-list-{suffix}@example.test",
        name="Customer",
        role="user",
    )
    db.add_all([admin, customer_user])
    db.flush()
    admin_customer = Customer(name=admin.name, email=admin.email, phone="", user_id=admin.id)
    customer = Customer(
        name=customer_user.name,
        email=customer_user.email,
        phone="",
        user_id=customer_user.id,
    )
    db.add_all([admin_customer, customer])
    db.flush()
    admin_conversation = Conversation(customer_id=admin_customer.id, status="active")
    customer_conversation = Conversation(customer_id=customer.id, status="active")
    db.add_all([admin_conversation, customer_conversation])
    db.flush()
    lead = Lead(
        customer_id=customer.id,
        conversation_id=customer_conversation.id,
        score=95,
        classification="HOT",
        buying_intent="HIGH",
    )
    db.add(lead)
    db.commit()

    monkeypatch.setattr(settings, "ADMIN_EMAILS", admin.email)
    app.dependency_overrides[get_current_user] = lambda: admin

    response = client.get("/api/conversations")
    assert response.status_code == 200
    conversations = response.json()
    assert {
        admin_conversation.id,
        customer_conversation.id,
    }.issubset({
        item["id"] for item in conversations
    })
    customer_record = next(item for item in conversations if item["id"] == customer_conversation.id)
    assert customer_record["lead"]["classification"] == "HOT"

    db.delete(lead)
    db.delete(admin_conversation)
    db.delete(customer_conversation)
    db.delete(admin_customer)
    db.delete(customer)
    db.delete(admin)
    db.delete(customer_user)
    db.commit()


def test_admin_audio_response_includes_lead_data(client, db, monkeypatch):
    suffix = uuid.uuid4().hex
    user = User(
        google_sub=f"admin-audio-{suffix}",
        email=f"admin-audio-{suffix}@example.test",
        name="Admin",
        role="admin",
    )
    db.add(user)
    db.flush()
    customer = Customer(name=user.name, email=user.email, phone="", user_id=user.id)
    db.add(customer)
    db.flush()
    conversation = Conversation(customer_id=customer.id, status="active")
    db.add(conversation)
    db.flush()
    lead = Lead(
        customer_id=customer.id,
        conversation_id=conversation.id,
        score=95,
        classification="HOT",
        buying_intent="HIGH",
    )
    db.add(lead)
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        "backend.app.api.conversations.speech_service.transcribe_audio",
        lambda **kwargs: "I would like to discuss the project.",
    )
    monkeypatch.setattr(
        conversation_service,
        "process_turn",
        lambda **kwargs: conversation,
    )

    response = client.post(
        f"/api/conversations/{conversation.id}/audio",
        files={"file": ("recording.wav", b"audio", "audio/wav")},
        data={"language": "English"},
    )
    assert response.status_code == 200
    assert response.json()["lead"]["classification"] == "HOT"

    db.delete(lead)
    db.delete(conversation)
    db.delete(customer)
    db.delete(user)
    db.commit()


def test_profile_accepts_tamil_preference(client, db):
    suffix = uuid.uuid4().hex
    user = User(
        google_sub=f"tamil-profile-{suffix}",
        email=f"tamil-profile-{suffix}@example.test",
        name="Tamil User",
    )
    db.add(user)
    db.flush()
    customer = Customer(name=user.name, email=user.email, phone="", user_id=user.id)
    db.add(customer)
    db.commit()
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.patch("/api/auth/profile", json={"preferred_language": "Tamil"})

    assert response.status_code == 200
    assert response.json()["preferred_language"] == "Tamil"
    db.delete(customer)
    db.delete(user)
    db.commit()


def test_auth_profile_requires_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
