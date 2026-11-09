"""
WhatsApp Follow-Up Service — CP-07
Integrates with Meta Cloud API.
Falls back to draft mode when credentials are not configured.
"""

import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


# Delivery status lifecycle: draft → queued → sent → delivered | failed
STATUS_DRAFT     = "draft"
STATUS_QUEUED    = "queued"
STATUS_SENT      = "sent"
STATUS_DELIVERED = "delivered"
STATUS_FAILED    = "failed"

META_GRAPH_URL = "https://graph.facebook.com/{api_version}/{phone_number_id}/messages"


class WhatsAppService:
    """Handles WhatsApp message dispatch via Meta Cloud API with draft fallback."""

    def __init__(self):
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """True when all three Meta Cloud API credentials are present."""
        return bool(
            self.api_token
            and self.phone_number_id
            and self.business_account_id
        )

    def check_opt_in(
        self,
        customer_phone: Optional[str],
        consent_confirmed: bool = False,
    ) -> Tuple[bool, str]:
        """
        Require an operator to explicitly confirm opt-in before a live send.
        """
        if not consent_confirmed:
            return False, "Customer WhatsApp consent has not been confirmed"

        if not customer_phone:
            return False, "No phone number on record for this customer"

        # Strip spaces, dashes, country code
        clean = customer_phone.strip().replace(" ", "").replace("-", "")
        if clean.startswith("+91"):
            clean = clean[3:]
        elif clean.startswith("91") and len(clean) == 12:
            clean = clean[2:]

        if len(clean) == 10 and clean[0] in "6789":
            return True, "opt-in-verified"

        return False, f"Phone number '{customer_phone}' does not match Indian mobile format"

    def send_whatsapp_message(
        self,
        to_phone: str,
        message_text: str,
        action_id: Optional[int] = None,
        consent_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        Attempt to send a WhatsApp message via Meta Cloud API.

        Returns a result dict with keys:
          - status: "sent" | "draft" | "failed"
          - provider_reference: wamid string or None
          - message: human-readable outcome
          - draft_text: the prepared message (always present for operator review)
        """
        result: Dict[str, Any] = {
            "status": STATUS_DRAFT,
            "provider_reference": None,
            "draft_text": message_text,
            "action_id": action_id,
        }

        # --- Opt-in check ---
        opted_in, reason = self.check_opt_in(to_phone, consent_confirmed)
        if not opted_in:
            result["status"] = STATUS_DRAFT
            result["message"] = f"Consent check failed: {reason}. Message saved as draft."
            logger.warning("WhatsApp consent check failed for %s: %s", to_phone, reason)
            return result

        # --- Credentials check → draft fallback ---
        if not self.is_configured:
            result["status"] = STATUS_DRAFT
            result["message"] = (
                "WhatsApp API credentials not configured. "
                "Message saved as draft — operator can copy and send manually."
            )
            logger.info("WhatsApp draft fallback (credentials missing) for action_id=%s", action_id)
            return result

        # --- Attempt live dispatch ---
        return self._dispatch_via_meta(to_phone=to_phone, message_text=message_text, result=result)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch_via_meta(
        self,
        to_phone: str,
        message_text: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call Meta Graph API to send message; update result dict in-place."""
        url = META_GRAPH_URL.format(
            api_version=settings.WHATSAPP_GRAPH_API_VERSION,
            phone_number_id=self.phone_number_id,
        )

        # WhatsApp phone numbers must include country code, no leading +
        clean_phone = to_phone.strip().replace(" ", "").replace("-", "")
        if not clean_phone.startswith("91"):
            clean_phone = "91" + clean_phone.lstrip("+")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            # Extract WhatsApp message ID (wamid)
            wamid = None
            if "messages" in resp_body and resp_body["messages"]:
                wamid = resp_body["messages"][0].get("id")

            result["status"] = STATUS_SENT
            result["provider_reference"] = wamid
            result["message"] = f"Message dispatched via Meta Cloud API. wamid={wamid}"
            logger.info("WhatsApp sent OK: wamid=%s to=%s", wamid, clean_phone)

        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            result["status"] = STATUS_FAILED
            result["message"] = f"Meta API HTTP {exc.code}: {body[:200]}"
            logger.error("WhatsApp HTTP error %s: %s", exc.code, body[:200])

        except urllib.error.URLError as exc:
            result["status"] = STATUS_FAILED
            result["message"] = f"Meta API network error: {exc.reason}"
            logger.error("WhatsApp network error: %s", exc.reason)

        except Exception as exc:  # noqa: BLE001
            result["status"] = STATUS_FAILED
            result["message"] = f"Unexpected error: {exc}"
            logger.exception("WhatsApp unexpected error")

        return result

    def prepare_draft(
        self,
        customer_name: str,
        message_body: str,
        language: str = "en",
    ) -> str:
        """
        Return a formatted draft message string ready for operator review / copy-paste.
        """
        lang_greetings = {
            "en": f"Dear {customer_name},",
            "hi": f"प्रिय {customer_name},",
            "te": f"ప్రియమైన {customer_name},",
        }
        greeting = lang_greetings.get(language, lang_greetings["en"])
        footer_map = {
            "en": "\n\nBest regards,\nLeadPilot AI Sales Team",
            "hi": "\n\nसादर,\nLeadPilot AI सेल्स टीम",
            "te": "\n\nధన్యవాదాలు,\nLeadPilot AI సేల్స్ టీమ్",
        }
        footer = footer_map.get(language, footer_map["en"])
        return f"{greeting}\n\n{message_body}{footer}"

    def get_delivery_status(self, wamid: str) -> Dict[str, Any]:
        """
        Webhook-based delivery tracking stub.
        In production, Meta pushes delivery receipts to your webhook URL.
        This method is a placeholder for outbound status polling — not
        recommended by Meta but useful for MVP dashboard display.
        """
        return {
            "wamid": wamid,
            "status": STATUS_SENT,
            "note": (
                "Delivery receipts are pushed by Meta via webhook. "
                "Register POST /api/whatsapp/webhook to receive real-time updates."
            ),
        }


# Singleton
whatsapp_service = WhatsAppService()
