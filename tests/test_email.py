from unittest.mock import MagicMock, patch

from backend.app.core.config import settings
from backend.app.database.base import Base
from backend.app.database.connection import SessionLocal, engine
from backend.app.models.action import Action
from backend.app.models.customer import Customer
from backend.app.models.conversation import Conversation
from backend.app.api.actions import ExecuteActionRequest, execute_action
from backend.app.services.conversation_service import conversation_service
from backend.app.services.email_service import EmailService


def test_email_is_not_sent_without_explicit_confirmation(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sales@example.test")

    with patch("backend.app.services.email_service.smtplib.SMTP") as smtp:
        result = service.send_email(
            "customer@example.test",
            "Call summary",
            "Summary body",
            consent_confirmed=False,
        )

    assert result["status"] == "draft"
    assert "confirmation" in result["message"].lower()
    smtp.assert_not_called()


def test_email_is_sent_via_smtp_after_confirmation(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sales@example.test")
    smtp_context = MagicMock()
    smtp = smtp_context.__enter__.return_value

    with patch(
        "backend.app.services.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ) as smtp_factory:
        result = service.send_email(
            "customer@example.test",
            "Call summary",
            "Summary body",
            consent_confirmed=True,
        )

    assert result["status"] == "sent"
    smtp_factory.assert_called_once_with("smtp.example.test", 587, timeout=20)
    smtp.send_message.assert_called_once()
    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["To"] == "customer@example.test"
    assert sent_message["Subject"] == "Call summary"
    assert sent_message.get_content() == "Summary body\n"


def test_gmail_port_465_uses_implicit_tls(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "sender@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sender@gmail.com")
    smtp_context = MagicMock()
    smtp = smtp_context.__enter__.return_value

    with patch(
        "backend.app.services.email_service.smtplib.SMTP_SSL",
        return_value=smtp_context,
    ) as smtp_factory, patch(
        "backend.app.services.email_service.smtplib.SMTP",
    ) as starttls_factory:
        result = service.send_email(
            "customer@example.test",
            "Call summary",
            "Summary body",
            consent_confirmed=True,
        )

    assert result["status"] == "sent"
    smtp_factory.assert_called_once()
    smtp.starttls.assert_not_called()
    smtp.login.assert_called_once_with("sender@gmail.com", "test-app-password")
    starttls_factory.assert_not_called()


def test_smtp_login_normalizes_copied_app_password_spaces(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_USERNAME", " sender@gmail.com ")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "abcd efgh ijkl mnop")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sender@gmail.com")
    smtp_context = MagicMock()
    smtp = smtp_context.__enter__.return_value

    with patch(
        "backend.app.services.email_service.smtplib.SMTP_SSL",
        return_value=smtp_context,
    ):
        result = service.send_email(
            "customer@example.test",
            "Call summary",
            "Summary body",
            consent_confirmed=True,
        )

    assert result["status"] == "sent"
    smtp.login.assert_called_once_with("sender@gmail.com", "abcdefghijklmnop")


def test_smtp_disconnect_during_authentication_explains_gmail_setup(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "sender@example.test")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-password")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sender@example.test")
    smtp_context = MagicMock()
    smtp = smtp_context.__enter__.return_value
    smtp.login.side_effect = __import__("smtplib").SMTPServerDisconnected(
        "Connection unexpectedly closed"
    )

    with patch(
        "backend.app.services.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        result = service.send_email(
            "customer@example.test",
            "Call summary",
            "Summary body",
            consent_confirmed=True,
        )

    assert result["status"] == "failed"
    assert "during authentication" in result["message"]
    assert "App Password" in result["message"]


def test_email_action_requires_consent_and_updates_status(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customer = Customer(name="Email Action Customer", phone="9876543210")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        action = Action(
            customer_id=customer.id,
            action_type="email_followup",
            payload={
                "recipient": "customer@example.test",
                "subject": "Call summary",
                "message": "Summary body",
            },
            status="draft",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        calls = []

        def fake_send_email(recipient, subject, body, consent_confirmed=False):
            calls.append(consent_confirmed)
            return {
                "status": "sent" if consent_confirmed else "draft",
                "message": "Email sent." if consent_confirmed else "Email remains a draft.",
                "draft_text": None if consent_confirmed else body,
            }

        monkeypatch.setattr(
            "backend.app.api.actions.email_service.send_email",
            fake_send_email,
        )
        draft_result = execute_action(
            action.id,
            db,
            ExecuteActionRequest(consent_confirmed=False),
        )
        assert draft_result["email_status"] == "draft"
        assert action.status == "draft"

        sent_result = execute_action(
            action.id,
            db,
            ExecuteActionRequest(consent_confirmed=True),
        )

        assert sent_result["email_status"] == "sent"
        assert action.status == "sent"
        assert action.executed_at is not None
        assert calls == [False, True]
    finally:
        db.close()


def test_ending_conversation_automatically_sends_recap_once(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customer = Customer(
            name="Automatic Recap Customer",
            phone="9876543210",
            email="customer@example.test",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        conversation = Conversation(customer_id=customer.id, status="active")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        action = Action(
            customer_id=customer.id,
            conversation_id=conversation.id,
            action_type="email_followup",
            payload={
                "recipient": customer.email,
                "subject": "Call summary",
                "message": "Recap of the conversation",
            },
            status="draft",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        monkeypatch.setattr(
            "backend.app.services.conversation_service.extraction_service.extract_and_update_lead",
            lambda _db, _conversation_id: None,
        )
        send_calls = []

        def fake_send_email(recipient, subject, body, consent_confirmed=False):
            send_calls.append((recipient, consent_confirmed))
            return {"status": "sent", "message": "Email sent.", "draft_text": None}

        monkeypatch.setattr(
            "backend.app.services.conversation_service.email_service.send_email",
            fake_send_email,
        )

        conversation_service.end_conversation(db, conversation.id)
        conversation_service.end_conversation(db, conversation.id)

        assert send_calls == [("customer@example.test", True)]
        assert action.status == "sent"
        assert action.executed_at is not None
    finally:
        db.close()
