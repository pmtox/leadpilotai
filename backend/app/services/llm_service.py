"""LLM Service supporting Gemini and Groq providers with graceful fallback and multilingual intelligence."""
import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.prompts import SALES_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def detect_language(text: str, fallback_lang: str = "English") -> str:
    """Detect whether text is primarily Hindi, Telugu, or English."""
    if not text:
        return fallback_lang
    
    # Check Unicode ranges
    # Devanagari: \u0900 - \u097F
    # Telugu: \u0C00 - \u0C7F
    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    telugu_count = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')

    if devanagari_count > 0:
        return "Hindi"
    if telugu_count > 0:
        return "Telugu"
    
    # Check common romanized keywords
    lower = text.lower()
    hindi_keywords = ["namaste", "aapka", "kya", "chahiye", "dukan", "samaan", "rupaye", "karna", "hai", "mujhe", "kitna"]
    telugu_keywords = ["namaskaram", "meeru", "kavali", "ento", "undi", "cheyandi", "ela", "nenu", "entha", "avunu"]

    if any(f" {w} " in f" {lower} " for w in hindi_keywords):
        return "Hindi"
    if any(f" {w} " in f" {lower} " for w in telugu_keywords):
        return "Telugu"

    return fallback_lang

class LLMService:
    def __init__(self):
        self.provider = settings.DEFAULT_LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL

    def is_live_provider_available(self) -> bool:
        """Check if a live LLM API key is present."""
        if self.provider == "gemini" and self.gemini_key:
            return True
        if self.provider == "groq" and self.groq_key:
            return True
        if self.gemini_key or self.groq_key:
            return True
        return False

    def generate_reply(
        self,
        messages: List[Dict[str, str]],
        language: str = "English",
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate conversational reply using configured LLM or intelligent fallback."""
        sys_prompt = system_prompt or SALES_AGENT_SYSTEM_PROMPT

        # 1. Try Google Gemini API if key is available
        if self.gemini_key:
            try:
                reply = self._call_gemini(messages, language, sys_prompt)
                if reply:
                    return reply
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back.")

        # 2. Try Groq API if key is available
        if self.groq_key:
            try:
                reply = self._call_groq(messages, language, sys_prompt)
                if reply:
                    return reply
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Falling back.")

        # 3. Intelligent rule-based multilingual fallback
        return self._intelligent_fallback_reply(messages, language)

    def _call_gemini(self, messages: List[Dict[str, str]], language: str, system_prompt: str) -> Optional[str]:
        """Invoke Google Gemini REST API."""
        model_name = self.model if "gemini" in self.model else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"

        # Convert conversation messages to Gemini format
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
                "maxOutputTokens": 300,
            }
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None

    def _call_groq(self, messages: List[Dict[str, str]], language: str, system_prompt: str) -> Optional[str]:
        """Invoke Groq OpenAI-compatible API."""
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

        model_name = "llama-3.3-70b-versatile" if "llama" not in self.model else self.model
        payload = {
            "model": model_name,
            "messages": groq_messages,
            "temperature": 0.7,
            "max_tokens": 300
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            else:
                logger.error(f"Groq API returned status {resp.status_code}: {resp.text}")
                return None

    def _intelligent_fallback_reply(self, messages: List[Dict[str, str]], language: str) -> str:
        """Intelligent contextual sales flow simulator for English, Hindi, and Telugu."""
        # Find latest customer turn
        customer_msgs = [m for m in messages if m.get("speaker") in ("customer", "user")]
        latest_text = customer_msgs[-1].get("content", "") if customer_msgs else ""
        turn_count = len(customer_msgs)

        detected_lang = detect_language(latest_text, fallback_lang=language)
        lower_input = latest_text.lower()

        # Check for opt-out / stopping intent
        stop_keywords = ["stop", "not interested", "bye", "nahi chahiye", "baad me", "vaddu", "odhu"]
        if any(w in lower_input for w in stop_keywords):
            if detected_lang == "Hindi":
                return "समझ गया। आपके समय के लिए धन्यवाद! यदि आपको भविष्य में सहायता चाहिए तो कृपया हमसे संपर्क करें।"
            elif detected_lang == "Telugu":
                return "అర్థమైంది. మీ సమయానికి ధన్యవాదాలు! భవిష్యత్తులో మీకు సహాయం అవసరమైతే మమ్మల్ని సంప్రదించండి."
            else:
                return "Understood. Thank you so much for your time! Feel free to reach back out whenever you are ready."

        # Consultative conversational flow based on turns
        if turn_count <= 1:
            if detected_lang == "Hindi":
                return "बहुत बढ़िया! आपकी किस प्रकार की दुकान या व्यवसाय है? (जैसे कपड़े, इलेक्ट्रॉनिक्स, या किराने का सामान?)"
            elif detected_lang == "Telugu":
                return "చాలా బాగుంది! మీది ఏ రకమైన వ్యాపారం? (ఉదాహరణకు బట్టలు, ఎలక్ట్రానిక్స్, లేదా కిరాణా?)"
            else:
                return "That's wonderful! What kind of products or business do you plan to sell online? (e.g., clothing, electronics, or groceries?)"

        elif turn_count == 2:
            if detected_lang == "Hindi":
                return "शानदार! आपके पास लगभग कितने उत्पाद (products) सूचीबद्ध करने के लिए होंगे, और आपका लक्षित बजट क्या है?"
            elif detected_lang == "Telugu":
                return "అద్భుతం! మీ వద్ద సుమారు ఎన్ని ఉత్పత్తులు ఉంటాయి మరియు మీ అంచనా బడ్జెట్ ఎంత?"
            else:
                return "Sounds great! Approximately how many products do you plan to list, and do you have an estimated budget in mind?"

        elif turn_count == 3:
            if detected_lang == "Hindi":
                return "बिल्कुल सही! क्या आपको ऑनलाइन पेमेंट (UPI/कार्ड्स) और डिलीवरी ट्रैकिंग जैसी विशेष सुविधाएं चाहिए?"
            elif detected_lang == "Telugu":
                return "తప్పకుండా! మీకు ఆన్‌లైన్ చెల్లింపులు (UPI/కార్డులు) మరియు డెలివరీ ట్రాకింగ్ ఫీచర్లు అవసరమా?"
            else:
                return "Understood! Would you need integrated online payments (like UPI/Credit Cards) and automatic delivery tracking?"

        else:
            if detected_lang == "Hindi":
                return "धन्यवाद! मैंने आपकी सभी आवश्यकताएं नोट कर ली हैं। क्या आप अगले महीने तक वेबसाइट लॉन्च करने की योजना बना रहे हैं?"
            elif detected_lang == "Telugu":
                return "ధన్యవాదాలు! మీ అన్ని అవసరాలు నమోదు చేసుకున్నాను. మీరు వచ్చే నెలలోపు వెబ్‌సైట్‌ను ప్రారంభించాలనుకుంటున్నారా?"
            else:
                return "Thank you! I have recorded your requirements. Are you looking to launch within the next few weeks or next month?"

llm_service = LLMService()
