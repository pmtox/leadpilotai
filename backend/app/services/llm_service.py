"""LLM Service supporting Gemini and Groq providers with graceful fallback and multilingual intelligence."""
import os
import json
import re
import time
import logging
from datetime import date
import httpx
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.prompts import SALES_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Track temporary provider rate-limiting / outage
_rate_limited_until: Dict[str, float] = {}

def detect_language(text: str, fallback_lang: str = "English") -> str:
    """Detect whether text is primarily Hindi, Telugu, or English."""
    if not text:
        return fallback_lang

    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    telugu_count = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')

    if devanagari_count > 0:
        return "Hindi"
    if telugu_count > 0:
        return "Telugu"

    lower = text.lower()
    hindi_keywords = ["namaste", "aapka", "kya", "chahiye", "dukan", "samaan", "rupaye", "karna", "hai", "mujhe", "kitna"]
    telugu_keywords = ["namaskaram", "meeru", "kavali", "ento", "undi", "cheyandi", "ela", "nenu", "entha", "avunu"]

    if any(f" {w} " in f" {lower} " for w in hindi_keywords):
        return "Hindi"
    if any(f" {w} " in f" {lower} " for w in telugu_keywords):
        return "Telugu"

    return fallback_lang

class LLMService:
    def __init__(self) -> None:
        self._request_date = date.today()
        self._daily_request_count = 0
        self._conversation_request_counts: Dict[int, int] = {}

    @property
    def provider(self) -> str:
        return settings.DEFAULT_LLM_PROVIDER

    @property
    def gemini_key(self) -> str:
        return settings.GEMINI_API_KEY

    @property
    def groq_key(self) -> str:
        return settings.GROQ_API_KEY

    @property
    def gemini_model(self) -> str:
        return settings.GEMINI_MODEL or "gemini-3.8-flash"

    @property
    def groq_model(self) -> str:
        return settings.GROQ_MODEL or "openai/gpt-oss-120b"

    @property
    def extraction_enabled(self) -> bool:
        return settings.LLM_EXTRACTION_ENABLED

    def is_live_provider_available(self) -> bool:
        return bool(self.gemini_key or self.groq_key)

    def _reserve_request(self, conversation_id: Optional[int]) -> bool:
        today = date.today()
        if today != self._request_date:
            self._request_date = today
            self._daily_request_count = 0
            self._conversation_request_counts.clear()

        daily_limit = max(0, settings.LLM_MAX_CALLS_PER_DAY)
        if self._daily_request_count >= daily_limit:
            logger.warning("Daily LLM request cap reached; using rule-based reply.")
            return False

        if conversation_id is not None:
            conversation_limit = max(0, settings.LLM_MAX_CALLS_PER_CONVERSATION)
            conversation_count = self._conversation_request_counts.get(conversation_id, 0)
            if conversation_count >= conversation_limit:
                logger.info(
                    "LLM request cap reached for conversation %s; using rule-based reply.",
                    conversation_id,
                )
                return False
            self._conversation_request_counts[conversation_id] = conversation_count + 1

        self._daily_request_count += 1
        return True

    def generate_reply(
        self,
        messages: List[Dict[str, str]],
        language: str = "English",
        system_prompt: Optional[str] = None,
        conversation_id: Optional[int] = None,
    ) -> str:
        sys_prompt = system_prompt or SALES_AGENT_SYSTEM_PROMPT
        now = time.time()

        # Try providers in order based on settings
        providers = ["gemini", "groq"] if self.provider == "gemini" else ["groq", "gemini"]

        for prov in providers:
            if prov == "gemini" and self.gemini_key:
                if now < _rate_limited_until.get("gemini", 0):
                    continue
                if not self._reserve_request(conversation_id):
                    break
                try:
                    reply = self._call_gemini(messages, language, sys_prompt)
                    if reply:
                        if not self._repeats_previous_agent_reply(messages, reply):
                            return reply
                        logger.warning("Gemini repeated its previous reply; using the contextual fallback.")
                except Exception as e:
                    logger.warning(f"Gemini API call failed: {e}. Falling back.")

            elif prov == "groq" and self.groq_key:
                if now < _rate_limited_until.get("groq", 0):
                    continue
                if not self._reserve_request(conversation_id):
                    break
                try:
                    reply = self._call_groq(messages, language, sys_prompt)
                    if reply:
                        if not self._repeats_previous_agent_reply(messages, reply):
                            return reply
                        logger.warning("Groq repeated its previous reply; using the contextual fallback.")
                except Exception as e:
                    logger.warning(f"Groq API call failed: {e}. Falling back.")

        # Intelligent rule-based multilingual fallback
        return self._intelligent_fallback_reply(messages, language)

    def _call_gemini(self, messages: List[Dict[str, str]], language: str, system_prompt: str) -> Optional[str]:
        model_name = self.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"

        gemini_contents = []
        for msg in messages:
            role = "user" if msg.get("speaker") in ("customer", "user") else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": f"{system_prompt}\nCustomer language preference: {language}."}]
            },
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 200,
            }
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    if candidates[0].get("finishReason") == "MAX_TOKENS":
                        logger.warning("Gemini reply reached its output limit; using fallback.")
                        return None
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            elif resp.status_code == 429:
                logger.warning("Gemini API 429 Quota Exceeded. Backing off for 60 seconds.")
                _rate_limited_until["gemini"] = time.time() + 60.0
                return None
            else:
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None

    def _call_groq(self, messages: List[Dict[str, str]], language: str, system_prompt: str) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }

        groq_messages = [
            {"role": "system", "content": f"{system_prompt}\nCustomer language preference: {language}."}
        ]
        for msg in messages:
            role = "user" if msg.get("speaker") in ("customer", "user") else "assistant"
            groq_messages.append({"role": role, "content": msg.get("content", "")})

        payload = {
            "model": self.groq_model,
            "messages": groq_messages,
            "temperature": 0.7,
            "max_tokens": 200
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    if choices[0].get("finish_reason") == "length":
                        logger.warning("Groq reply reached its output limit; using fallback.")
                        return None
                    return choices[0].get("message", {}).get("content", "").strip()
            elif resp.status_code == 429:
                logger.warning("Groq API 429 Rate limit exceeded. Backing off for 30s.")
                _rate_limited_until["groq"] = time.time() + 30.0
                return None
            else:
                logger.error(f"Groq API returned status {resp.status_code}: {resp.text}")
                return None

    def _intelligent_fallback_reply(self, messages: List[Dict[str, str]], language: str) -> str:
        customer_msgs = [m for m in messages if m.get("speaker") in ("customer", "user")]
        latest_text = customer_msgs[-1].get("content", "") if customer_msgs else ""

        detected_lang = detect_language(latest_text, fallback_lang=language)
        lower_input = latest_text.lower()

        stop_keywords = ["stop", "not interested", "bye", "nahi chahiye", "baad me", "vaddu", "odhu"]
        if any(w in lower_input for w in stop_keywords):
            if detected_lang == "Hindi":
                return "समझ गया। आपके समय के लिए धन्यवाद! यदि आपको भविष्य में सहायता चाहिए तो कृपया हमसे संपर्क करें।"
            elif detected_lang == "Telugu":
                return "అర్థమైంది. మీ సమయానికి ధన్యవాదాలు! భవిష్యత్తులో మీకు సహాయం అవసరమైతే మమ్మల్ని సంప్రదించండి."
            else:
                return "Understood. Thank you so much for your time! Feel free to reach back out whenever you are ready."

        from backend.app.services.extraction_service import extraction_service

        requirements = extraction_service.extract_rules_from_history(messages)
        if (
            requirements.get("budget") is None
            and customer_msgs
            and re.search(r"(?:\$|usd\b|dollars?\b)", latest_text, flags=re.IGNORECASE)
            and re.search(r"[\d,]+", latest_text)
        ):
            return (
                "I heard that as a dollar amount. Since our project estimates are in INR, "
                "could you share the INR equivalent?"
            )
        next_question = self._next_missing_requirement_question(requirements, detected_lang)
        if next_question:
            acknowledgments = {
                "Hindi": "समझ गया।",
                "Telugu": "అర్థమైంది.",
                "English": "Got it.",
            }
            return f"{acknowledgments.get(detected_lang, acknowledgments['English'])} {next_question}"

        return {
            "Hindi": "धन्यवाद, मैंने आपकी सभी आवश्यकताएँ नोट कर ली हैं। क्या आप चाहेंगे कि हमारी टीम आपके लिए अगला कदम तय करे?",
            "Telugu": "ధన్యవాదాలు, మీ అవసరాలన్నీ నమోదు చేశాను. తదుపరి దశ గురించి మా బృందం మీతో మాట్లాడాలా?",
            "English": "Thanks, I have noted your requirements. Would you like me to arrange a follow-up with our team?",
        }.get(detected_lang, "Thanks, I have noted your requirements. Would you like me to arrange a follow-up with our team?")

    @staticmethod
    def _next_missing_requirement_question(requirements: Dict[str, Any], language: str) -> Optional[str]:
        prompts = {
            "English": [
                ("business_type", "What type of business or products will your online store focus on?"),
                ("product_count", "About how many products do you plan to list at launch?"),
                ("budget", "Do you have an estimated budget for the website?"),
                ("timeline", "When are you hoping to launch the store?"),
                ("features", "Which key features should the store include, such as payments, inventory, WhatsApp alerts, or delivery integration?"),
            ],
            "Hindi": [
                ("business_type", "आपका व्यवसाय किस प्रकार के उत्पादों से जुड़ा है?"),
                ("product_count", "शुरुआत में आप लगभग कितने उत्पाद सूचीबद्ध करेंगे?"),
                ("budget", "वेबसाइट के लिए आपका अनुमानित बजट क्या है?"),
                ("timeline", "आप स्टोर कब तक शुरू करना चाहते हैं?"),
                ("features", "स्टोर में कौन-सी सुविधाएँ जरूरी हैं, जैसे भुगतान, इन्वेंटरी, WhatsApp अलर्ट या डिलीवरी इंटीग्रेशन?"),
            ],
            "Telugu": [
                ("business_type", "మీ ఆన్‌లైన్ స్టోర్‌లో ఏ రకమైన వ్యాపారం లేదా ఉత్పత్తులు ఉంటాయి?"),
                ("product_count", "ప్రారంభంలో సుమారు ఎన్ని ఉత్పత్తులను జాబితా చేస్తారు?"),
                ("budget", "వెబ్‌సైట్ కోసం మీ అంచనా బడ్జెట్ ఎంత?"),
                ("timeline", "మీరు స్టోర్‌ను ఎప్పటికి ప్రారంభించాలనుకుంటున్నారు?"),
                ("features", "చెల్లింపులు, ఇన్వెంటరీ, WhatsApp అలర్ట్లు లేదా డెలివరీ ఇంటిగ్రేషన్ వంటి ఏ ఫీచర్లు కావాలి?"),
            ],
        }
        questions = prompts.get(language, prompts["English"])
        for field, question in questions:
            value = requirements.get(field)
            if field == "features":
                if not value:
                    return question
            elif not value:
                return question
        return None

    @staticmethod
    def _repeats_previous_agent_reply(messages: List[Dict[str, str]], reply: str) -> bool:
        normalized_reply = " ".join(reply.split()).casefold()
        if not normalized_reply:
            return False
        for message in reversed(messages):
            if message.get("speaker") == "agent":
                previous_reply = " ".join(message.get("content", "").split()).casefold()
                return previous_reply == normalized_reply
        return False

llm_service = LLMService()
