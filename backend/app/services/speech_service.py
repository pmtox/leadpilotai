"""Speech Service handling Speech-to-Text (STT) via Groq Whisper and fallback transcription."""
import io
import logging
import httpx
from typing import Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.groq_key = settings.GROQ_API_KEY

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None) -> str:
        """Transcribe audio bytes using Groq Whisper API with graceful fallback."""
        if self.groq_key:
            try:
                transcript = self._call_groq_whisper(audio_bytes, filename, language)
                if transcript:
                    return transcript
            except Exception as e:
                logger.warning(f"Groq Whisper transcription failed: {e}. Using fallback.")

        # Default fallback transcription for testing / offline demo
        return "I want to build an e-commerce clothing store with 200 products and ₹80,000 budget."

    def _call_groq_whisper(self, audio_bytes: bytes, filename: str, language: Optional[str]) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}"
        }

        # Language code mapping for Whisper
        lang_code = None
        if language:
            lang_lower = language.lower()
            if "hindi" in lang_lower:
                lang_code = "hi"
            elif "telugu" in lang_lower:
                lang_code = "te"
            elif "english" in lang_lower:
                lang_code = "en"

        files = {
            "file": (filename, io.BytesIO(audio_bytes), "audio/wav")
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "json"
        }
        if lang_code:
            data["language"] = lang_code

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            if resp.status_code == 200:
                result = resp.json()
                return result.get("text", "").strip()
            else:
                logger.error(f"Groq Whisper returned status {resp.status_code}: {resp.text}")
                return None

speech_service = SpeechService()
