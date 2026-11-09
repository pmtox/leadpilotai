import pytest
import io
from fastapi import UploadFile
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
    # Test transcription fallback / processing
    dummy_wav = b"RIFF....WAVEfmt ...."
    text = speech_service.transcribe_audio(dummy_wav, "sample.wav", "English")
    assert isinstance(text, str)
    assert len(text) > 0

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
    transcription = speech_service.transcribe_audio(dummy_wav, "sample.wav", "English")
    conv = conversation_service.process_turn(db, conv.id, message_text=transcription, language="English")

    assert len(conv.messages) == 3
    assert conv.messages[1].speaker == "customer"
    assert conv.messages[2].speaker == "agent"
    assert conv.lead is not None
    assert conv.lead.score > 0
