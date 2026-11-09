"""Speech Service handling Speech-to-Text (STT) via Groq Whisper."""
import io
import logging
import mimetypes
import httpx
from typing import Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.groq_key = settings.GROQ_API_KEY

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None) -> str:
        """Transcribe audio bytes with Groq Whisper; raise an explicit error on failure."""
        if not audio_bytes:
            raise ValueError("No audio data was received")
        if not self.groq_key:
            raise RuntimeError("Groq API key is not configured for audio transcription")

        try:
            transcript = self._call_groq_whisper(audio_bytes, filename, language)
        except Exception as exc:
            logger.exception("Groq Whisper transcription failed")
            raise RuntimeError("Audio transcription service failed. Check the Groq API key and try again.") from exc

        if transcript is None:
            raise RuntimeError("Groq Whisper returned no transcript. Check model access and audio format.")
        if not transcript.strip():
            raise RuntimeError("No speech was recognized. Try recording again in a quieter place.")
        return transcript.strip()

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
            "file": (
                filename,
                io.BytesIO(audio_bytes),
                mimetypes.guess_type(filename)[0] or "application/octet-stream",
            )
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
                raise RuntimeError(f"Groq Whisper returned HTTP {resp.status_code}")

speech_service = SpeechService()
