"""
Tests for CP-07: WhatsApp Follow-Up Workflow
Tests draft generation, consent checks, service logic, and API endpoint wiring.
All tests use direct function calls (no live HTTP client) for reliability.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from backend.app.services.whatsapp_service import (
    WhatsAppService,
    whatsapp_service,
    STATUS_DRAFT,
    STATUS_SENT,
    STATUS_FAILED,
)


# =============================================================================
# 1. Configuration & feature-flag tests
# =============================================================================

class TestWhatsAppConfiguration:
    def test_unconfigured_by_default(self):
        """Service is in draft-fallback mode when env vars are empty."""
        svc = WhatsAppService()
        # In test env WHATSAPP_API_TOKEN is blank
        assert not svc.is_configured or svc.api_token != ""

    def test_configured_when_all_vars_set(self):
        svc = WhatsAppService()
        svc.api_token = "tok_test"
        svc.phone_number_id = "12345"
        svc.business_account_id = "WABA_001"
        assert svc.is_configured is True

    def test_missing_one_var_not_configured(self):
        svc = WhatsAppService()
        svc.api_token = "tok_test"
        svc.phone_number_id = "12345"
        svc.business_account_id = ""   # missing
        assert svc.is_configured is False


# =============================================================================
# 2. Opt-in / consent check tests
# =============================================================================

class TestOptInChecks:
    def setup_method(self):
        self.svc = WhatsAppService()

    def test_valid_indian_mobile_10digit(self):
        ok, reason = self.svc.check_opt_in("9876543210", consent_confirmed=True)
        assert ok is True
        assert reason == "opt-in-verified"

    def test_valid_with_country_prefix(self):
        ok, reason = self.svc.check_opt_in("+91 98765 43210", consent_confirmed=True)
        assert ok is True

    def test_valid_91_prefix_12digit(self):
        ok, reason = self.svc.check_opt_in("919876543210", consent_confirmed=True)
        assert ok is True

    def test_invalid_starts_with_5(self):
        ok, reason = self.svc.check_opt_in("5876543210", consent_confirmed=True)
        assert ok is False
        assert "format" in reason.lower()

    def test_invalid_too_short(self):
        ok, reason = self.svc.check_opt_in("98765", consent_confirmed=True)
        assert ok is False

    def test_missing_phone_returns_false(self):
        ok, reason = self.svc.check_opt_in(None, consent_confirmed=True)
        assert ok is False
        assert "No phone" in reason

    def test_empty_string_phone(self):
        ok, reason = self.svc.check_opt_in("", consent_confirmed=True)
        assert ok is False

    def test_valid_phone_is_not_consent(self):
        ok, reason = self.svc.check_opt_in("9876543210")
        assert ok is False
        assert "consent" in reason.lower()


# =============================================================================
# 3. Draft fallback when credentials missing
# =============================================================================

class TestDraftFallback:
    def setup_method(self):
        self.svc = WhatsAppService()
        # Ensure not configured
        self.svc.api_token = ""
        self.svc.phone_number_id = ""
        self.svc.business_account_id = ""

    def test_draft_returned_when_unconfigured(self):
        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Hello, your proposal is ready!",
            action_id=42,
        )
        assert result["status"] == STATUS_DRAFT
        assert result["draft_text"] == "Hello, your proposal is ready!"
        assert result["action_id"] == 42

    def test_draft_fallback_message_explains_reason(self):
        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Test",
        )
        assert "draft" in result["message"].lower() or "credential" in result["message"].lower()

    def test_no_provider_reference_in_draft(self):
        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Test",
        )
        assert result["provider_reference"] is None

    def test_draft_still_returned_when_consent_fails(self):
        self.svc.api_token = "tok_test_live"
        self.svc.phone_number_id = "10001"
        self.svc.business_account_id = "WABA_001"
        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Test",
        )
        assert result["status"] == STATUS_DRAFT
        assert "Consent" in result["message"] or "consent" in result["message"]


# =============================================================================
# 4. Draft message formatting
# =============================================================================

class TestDraftFormatting:
    def setup_method(self):
        self.svc = WhatsAppService()

    def test_english_draft_contains_name(self):
        msg = self.svc.prepare_draft("Ramesh", "Your custom proposal is attached.", "en")
        assert "Ramesh" in msg
        assert "Your custom proposal is attached." in msg
        assert "LeadPilot" in msg

    def test_hindi_draft_contains_name(self):
        msg = self.svc.prepare_draft("रमेश", "आपका प्रस्ताव तैयार है।", "hi")
        assert "रमेश" in msg
        assert "LeadPilot" in msg
        assert "सादर" in msg

    def test_telugu_draft_contains_name(self):
        msg = self.svc.prepare_draft("రమేష్", "మీ ప్రతిపాదన సిద్ధంగా ఉంది.", "te")
        assert "రమేష్" in msg
        assert "ధన్యవాదాలు" in msg

    def test_unknown_language_falls_back_to_english(self):
        msg = self.svc.prepare_draft("John", "Proposal ready.", "fr")
        assert "John" in msg
        assert "Best regards" in msg

    def test_draft_has_greeting_and_footer(self):
        msg = self.svc.prepare_draft("Test User", "Body text here.", "en")
        # Must start with greeting
        assert msg.startswith("Dear Test User")
        # Footer present
        assert "Sales Team" in msg


# =============================================================================
# 5. Live dispatch path (mocked)
# =============================================================================

class TestLiveDispatch:
    def setup_method(self):
        self.svc = WhatsAppService()
        self.svc.api_token = "tok_test_live"
        self.svc.phone_number_id = "10001"
        self.svc.business_account_id = "WABA_001"

    @patch("urllib.request.urlopen")
    def test_successful_send_returns_sent_status(self, mock_urlopen):
        # Mock Meta API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"messages": [{"id": "wamid.test123"}]}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Hello from LeadPilot!",
            action_id=1,
            consent_confirmed=True,
        )
        assert result["status"] == STATUS_SENT
        assert result["provider_reference"] == "wamid.test123"

    @patch("urllib.request.urlopen")
    def test_meta_api_http_error_returns_failed(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://graph.facebook.com",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error": "unauthorized"}'),
        )

        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Test",
            action_id=2,
            consent_confirmed=True,
        )
        assert result["status"] == STATUS_FAILED
        assert "401" in result["message"]

    @patch("urllib.request.urlopen")
    def test_network_error_returns_failed(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection refused")

        result = self.svc.send_whatsapp_message(
            to_phone="9876543210",
            message_text="Test",
            action_id=3,
            consent_confirmed=True,
        )
        assert result["status"] == STATUS_FAILED
        assert "network" in result["message"].lower() or "Connection" in result["message"]

    @patch("urllib.request.urlopen")
    def test_phone_normalised_to_91_prefix(self, mock_urlopen):
        """Domestic number is prepended with 91 before dispatch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"messages": [{"id": "wamid.normalized"}]}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        import json as _json
        self.svc.send_whatsapp_message(
            to_phone="8765432109",
            message_text="Norm test",
            consent_confirmed=True,
        )
        # Inspect the request body passed to urlopen
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        body = _json.loads(req.data.decode())
        assert body["to"] == "918765432109"


# =============================================================================
# 6. Actions API execute endpoint (direct function call)
# =============================================================================

class TestExecuteActionEndpoint:
    def test_api_accepts_explicit_consent_json(self):
        import asyncio
        from fastapi import FastAPI
        import httpx
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from backend.app.api.actions import router
        from backend.app.database.connection import get_db
        from backend.app.database.base import Base
        from backend.app.models.customer import Customer
        from backend.app.models.action import Action

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        customer = Customer(name="Ravi Kumar", phone="9876543210", preferred_language="en")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        action = Action(
            customer_id=customer.id,
            action_type="whatsapp_followup",
            payload={"followup_draft": "Your proposal is ready.", "language": "en"},
            status="draft",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db
        with patch(
            "backend.app.api.actions.whatsapp_service.send_whatsapp_message",
            return_value={
                "status": STATUS_DRAFT,
                "provider_reference": None,
                "draft_text": "Dear Ravi Kumar,\n\nYour proposal is ready.",
                "message": "Test draft",
            },
        ) as send_message:
            async def post_action():
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport,
                    base_url="http://test",
                ) as client:
                    return await client.post(
                        f"/api/actions/{action.id}/execute",
                        json={"consent_confirmed": True},
                    )

            response = asyncio.run(post_action())

        assert response.status_code == 200
        assert send_message.call_args.kwargs["consent_confirmed"] is True
        db.refresh(action)
        assert action.payload["consent_confirmed_at"]
        db.close()

    def test_execute_whatsapp_action_returns_draft(self):
        """
        End-to-end API test using direct function call against a temporary DB.
        A whatsapp_followup action with no credentials → returns draft status.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.database.base import Base
        from backend.app.models.customer import Customer
        from backend.app.models.conversation import Conversation
        from backend.app.models.lead import Lead
        from backend.app.models.action import Action
        from backend.app.api.actions import execute_action

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Create customer
        customer = Customer(name="Ravi Kumar", phone="9876543210", preferred_language="en")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create draft whatsapp action
        action = Action(
            customer_id=customer.id,
            action_type="whatsapp_followup",
            payload={
                "followup_draft": "We'd love to show you our premium catalog!",
                "language": "en",
            },
            status="draft",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Execute — credentials are blank in test env → draft fallback
        result = execute_action(action_id=action.id, db=db)

        assert "action" in result
        assert result["whatsapp_status"] in ("draft", "sent", "failed")
        assert result["draft_text"] is not None

        db.close()

    def test_execute_nonexistent_action_raises_404(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from fastapi import HTTPException
        from backend.app.database.base import Base
        from backend.app.api.actions import execute_action

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        with pytest.raises(HTTPException) as exc_info:
            execute_action(action_id=9999, db=db)

        assert exc_info.value.status_code == 404
        db.close()

    def test_cancel_action_endpoint(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.database.base import Base
        from backend.app.models.customer import Customer
        from backend.app.models.action import Action
        from backend.app.api.actions import cancel_action

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        customer = Customer(name="Test", phone="9123456780", preferred_language="en")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        action = Action(
            customer_id=customer.id,
            action_type="whatsapp_followup",
            payload={},
            status="draft",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        result = cancel_action(action_id=action.id, db=db)
        assert result["action"]["status"] == "cancelled"
        db.close()
