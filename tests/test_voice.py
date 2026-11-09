from unittest.mock import patch
import pytest
import asyncio
from fastapi import HTTPException, UploadFile
from io import BytesIO
from backend.app.database.connection import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.customer import Customer
from backend.app.services.speech_service import speech_service
from backend.app.services.conversation_service import conversation_service

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_speech_service_transcription():
    dummy_wav = b"RIFF....WAVEfmt ...."
    with patch.object(speech_service, "groq_key", "test-key"), patch.object(
        speech_service, "_call_groq_whisper", return_value="  I need an online store.  "
    ):
        text = speech_service.transcribe_audio(dummy_wav, "sample.wav", "English")
    assert text == "I need an online store."

def test_speech_service_reports_missing_groq_key():
    with patch.object(speech_service, "groq_key", ""):
        with pytest.raises(RuntimeError, match="not configured"):
            speech_service.transcribe_audio(b"audio", "sample.wav", "English")

def test_speech_service_reports_transcription_failure():
    with patch.object(speech_service, "groq_key", "test-key"), patch.object(
        speech_service, "_call_groq_whisper", return_value=None
    ):
        with pytest.raises(RuntimeError, match="no transcript"):
            speech_service.transcribe_audio(b"audio", "sample.wav", "English")

def test_audio_endpoint_reports_transcription_failure():
    from backend.app.api.conversations import process_audio_turn

    upload = UploadFile(filename="recording.webm", file=BytesIO(b"audio"))
    with patch.object(
        speech_service,
        "transcribe_audio",
        side_effect=RuntimeError("Groq API key is not configured"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(process_audio_turn(1, upload, "English", None))

    assert exc_info.value.status_code == 503
    assert "Groq API key" in exc_info.value.detail

def test_audio_conversation_turn(setup_db):
    db = setup_db
    cust = Customer(name="Voice Prospect", phone="+919988776655", preferred_language="English")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # Start conversation
    conv = conversation_service.start_conversation(db, customer_id=cust.id, initial_language="English")
    assert len(conv.messages) == 1

    # Simulate transcribed audio turn
    dummy_wav = b"RIFF....WAVEfmt ...."
    with patch.object(speech_service, "groq_key", "test-key"), patch.object(
        speech_service, "_call_groq_whisper", return_value="I want a clothing store."
    ):
        transcription = speech_service.transcribe_audio(dummy_wav, "sample.wav", "English")
    conv = conversation_service.process_turn(db, conv.id, message_text=transcription, language="English")

    assert len(conv.messages) == 3
    assert conv.messages[1].speaker == "customer"
    assert conv.messages[2].speaker == "agent"
    assert conv.lead is not None
    assert conv.lead.score > 0
