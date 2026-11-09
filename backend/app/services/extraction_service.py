"""Structured Information Extraction Service for LeadPilot AI.
Extracts business type, product count, budget, timeline, features, and buying intent.
Integrates with LeadScoringEngine for HOT/WARM/COLD qualification and follow-up drafts.
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.conversation import Conversation, Message
from backend.app.models.lead import Lead
from backend.app.models.action import Action
from backend.app.core.prompts import EXTRACTION_SYSTEM_PROMPT
from backend.app.services.llm_service import llm_service
from backend.app.services.lead_scoring import lead_scoring_engine

logger = logging.getLogger(__name__)

BUSINESS_TYPES = {
    "clothing": ["clothing", "cloth", "garment", "apparel", "fashion", "saree", "kurti", "t-shirt", "कपड़", "బట్ట"],
    "electronics": ["electronic", "gadget", "phone", "laptop", "mobile", "इलेक्ट्रॉनिक", "ఎలక్ట్రానిక్స్"],
    "grocery": ["grocer", "supermarket", "kirana", "किराना", "కిరాణా"],
    "jewelry": ["jewel", "ornament", "gold", "silver", "गहन", "జ్యువెలరీ", "ఆభరణ"],
    "footwear": ["footwear", "shoe", "sandal", "slipper", "जूत", "పాదరక్ష"],
    "cosmetics": ["cosmetic", "skincare", "beauty", "makeup", "कॉस्मेटिक", "సౌందర్య"],
    "bakery": ["baker", "cake", "pastr", "cookie", "बेकरी", "బేకరీ"],
    "furniture": ["furniture", "sofa", "chair", "woodwork", "फर्नीचर", "ఫర్నిచర్"],
    "handmade": ["handicraft", "handmade", "craft", "art", "हस्तशिल्प", "చేతివృత్తు"]
}

FEATURE_KEYWORDS = {
    "Online Payments (UPI/Cards)": ["payment", "upi", "razorpay", "card", "पेमेंट", "యూపీఐ", "చెల్లింపు"],
    "UPI Payments": ["upi"],
    "Credit/Debit Card Payments": ["credit card", "debit card", "cards"],
    "Razorpay Integration": ["razorpay"],
    "Delivery Tracking": ["delivery", "shipping", "tracking", "courier", "डिलीवरी", "డెలివరీ"],
    "Inventory Management": ["inventory", "stock", "स्टॉक", "ఇన్వెంటరీ"],
    "WhatsApp Notifications": ["whatsapp", "sms", "notification", "alerts", "व्हाट्सएप", "వాట్సాప్"],
    "Multi-currency / International": ["international", "export", "dollar", "nri"]
}

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

class ExtractionService:
    def extract_from_transcript(
        self,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        rule_extracted = self.extract_rules_from_history(conversation_history)
        if not llm_service.is_live_provider_available() or not llm_service.extraction_enabled:
            return rule_extracted

        try:
            llm_extracted = self._extract_with_llm(
                conversation_history,
                conversation_id=conversation_id,
            )
            if llm_extracted and any(llm_extracted.values()):
                cleaned = self._clean_extracted_data(llm_extracted)
                for field, rule_value in rule_extracted.items():
                    if rule_value not in (None, [], "UNKNOWN"):
                        cleaned[field] = rule_value
                return cleaned
        except Exception as e:
            logger.warning(f"LLM extraction error: {e}. Falling back to rule extraction.")

        return rule_extracted

    def extract_rules_from_history(
        self,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        customer_texts = [
            m.get("content", "")
            for m in conversation_history
            if m.get("speaker") in ("customer", "user")
        ]
        full_customer_transcript = " ".join(customer_texts)
        rule_extracted = self._extract_with_rules(full_customer_transcript)

        latest_customer_index = next(
            (
                index
                for index in range(len(conversation_history) - 1, -1, -1)
                if conversation_history[index].get("speaker") in ("customer", "user")
            ),
            None,
        )
        if latest_customer_index is None:
            return rule_extracted

        latest_customer_text = conversation_history[latest_customer_index].get("content", "").strip()
        previous_agent_text = next(
            (
                message.get("content", "").lower()
                for message in reversed(conversation_history[:latest_customer_index])
                if message.get("speaker") == "agent"
            ),
            "",
        )

        # A plain numeric answer is a budget when it directly answers the
        # budget/INR clarification, even without a currency symbol or label.
        if (
            rule_extracted["budget"] is None
            and re.fullmatch(r"\s*[\d,]+(?:\.\d+)?\s*", latest_customer_text)
            and ("budget" in previous_agent_text or "inr" in previous_agent_text)
        ):
            rule_extracted.update(self._extract_budget(f"budget {latest_customer_text}"))

        return rule_extracted

    def _extract_with_llm(
        self,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        prompt = (
            f"{EXTRACTION_SYSTEM_PROMPT}\n\n"
            f"Conversation History:\n"
            + "\n".join([f"{m.get('speaker', 'user')}: {m.get('content', '')}" for m in conversation_history])
            + "\n\nOutput only JSON:"
        )

        reply = llm_service.generate_reply(
            messages=[{"speaker": "customer", "content": prompt}],
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            conversation_id=conversation_id,
        )
        if not reply:
            return None

        clean_json = re.sub(r"^```json\s*", "", reply.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r"^```\s*", "", clean_json.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE)

        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return None

    def _extract_with_rules(self, text: str) -> Dict[str, Any]:
        lower = text.lower()
        result: Dict[str, Any] = {
            "business_type": None,
            "product_count": None,
            "budget": None,
            "budget_min": None,
            "budget_max": None,
            "timeline": None,
            "features": [],
            "buying_intent": "UNKNOWN",
            "language": "English",
            "email": None,
        }

        # 1. Detect Business Type
        for b_type, syns in BUSINESS_TYPES.items():
            if any(syn in lower for syn in syns):
                result["business_type"] = b_type.capitalize()
                break

        # 2. Extract Product Count
        count_pattern = r"(\d{1,3}(?:,\d{3})+|\d+)"
        prod_match = re.search(
            rf"{count_pattern}\s*(?:(?:project|catalog|store|total)\s+)?"
            rf"(?:products?|items?|articles?|pieces?|skus?|उत्पाद|वस्तुएं|వస్తువులు)?",
            lower,
        )
        prod_specific = re.search(
            rf"{count_pattern}\s*(?:(?:project|catalog|store|total)\s+)?"
            rf"(?:products|items|skus|pieces|उत्पाद|वस्तु|వస్తువులు|వస్తు)",
            lower,
        )
        if prod_specific:
            result["product_count"] = int(prod_specific.group(1).replace(",", ""))
        elif prod_match:
            val = int(prod_match.group(1).replace(",", ""))
            if val < 5000 and not any(curr in lower for curr in ["₹", "rs", "rupees", "lakh", "k"]):
                result["product_count"] = val

        # 3. Extract exact or ranged INR budgets, e.g. ₹60K–₹1L.
        result.update(self._extract_budget(lower))

        # 4. Extract Timeline
        if any(t in lower for t in ["next week", "within a week", "in a week", "this week", "one week", "अगले सप्ताह", "వచ్చే వారం"]):
            result["timeline"] = "Next week"
        elif any(t in lower for t in ["next month", "1 month", "अगले महीने", "వచ్చే నెల"]):
            result["timeline"] = "Next month"
        elif any(t in lower for t in ["2 weeks", "two weeks", "दो हफ्ते", "రెండు వారాలు"]):
            result["timeline"] = "2 weeks"
        elif any(t in lower for t in ["immediately", "asap", "urgent", "तुरंत", "వెంటనే"]):
            result["timeline"] = "Immediately"
        elif any(t in lower for t in ["3 months", "next quarter", "3 महीने", "3 నెలలు"]):
            result["timeline"] = "3 months"
        elif any(t in lower for t in ["this month", "इसी महीने", "ఈ నెల"]):
            result["timeline"] = "This month"

        # 5. Extract Features
        features_found = []
        for feat_name, syns in FEATURE_KEYWORDS.items():
            if any(syn in lower for syn in syns):
                features_found.append(feat_name)
        result["features"] = features_found

        email_match = EMAIL_PATTERN.search(text)
        if email_match:
            result["email"] = email_match.group(0)

        # 6. Buying Intent determination
        proposal_requested = any(
            phrase in lower
            for phrase in (
                "send me a proposal",
                "send a proposal",
                "requested a proposal",
                "need a proposal",
                "send me a quote",
                "request a quote",
                "email me the proposal",
                "send the proposal",
            )
        )
        if proposal_requested or result["timeline"] in {"Next week", "Immediately"}:
            result["buying_intent"] = "HIGH"
        elif result["budget"] and result["timeline"] and result["business_type"]:
            result["buying_intent"] = "HIGH"
        elif result["business_type"] or result["budget"]:
            result["buying_intent"] = "MEDIUM"
        else:
            result["buying_intent"] = "LOW"

        return result

    @classmethod
    def _extract_budget(cls, text: str) -> Dict[str, Optional[float]]:
        amount = r"\d+(?:,\d{2,3})*(?:\.\d+)?"
        unit = r"(?:lakhs?|lacs?|lac|लाख|లక్ష|l|k|thousand)?"
        prefix = r"(?:₹|rs\.?|inr)?\s*"
        range_match = re.search(
            rf"{prefix}(?P<low>{amount})\s*(?P<low_unit>{unit})\s*"
            rf"(?:-|–|—|to|through)\s*{prefix}"
            rf"(?P<high>{amount})\s*(?P<high_unit>{unit})",
            text,
        )
        if range_match:
            low_unit = range_match.group("low_unit")
            high_unit = range_match.group("high_unit")
            low = cls._amount_to_inr(range_match.group("low"), low_unit)
            high = cls._amount_to_inr(range_match.group("high"), high_unit)
            if not high_unit and low_unit:
                high = cls._amount_to_inr(range_match.group("high"), low_unit)
            if not low_unit and high_unit:
                low = cls._amount_to_inr(range_match.group("low"), high_unit)
            if low is not None and high is not None and high >= low:
                return {"budget_min": low, "budget_max": high, "budget": (low + high) / 2}

        labeled_match = re.search(
            rf"(?:₹|rs\.?|inr|budget(?:\s+is|\s+of)?|बजट|బడ్జెట్)\s*[:=]?\s*"
            rf"(?P<amount>{amount})\s*(?P<unit>{unit})",
            text,
        )
        single_match = labeled_match or re.search(
            rf"(?P<amount>{amount})\s*(?P<unit>lakhs?|lacs?|lac|लाख|లక్ష|l|k|thousand)\b",
            text,
        )
        if single_match:
            value = cls._amount_to_inr(single_match.group("amount"), single_match.group("unit"))
            if value is not None and value > 500:
                return {"budget_min": value, "budget_max": value, "budget": value}

        large_number = re.search(rf"\b(?P<amount>\d{{4,7}})\b", text)
        if large_number:
            value = float(large_number.group("amount"))
            return {"budget_min": value, "budget_max": value, "budget": value}
        return {"budget_min": None, "budget_max": None, "budget": None}

    @staticmethod
    def _amount_to_inr(value: str, unit: Optional[str]) -> Optional[float]:
        try:
            amount = float(value.replace(",", ""))
        except ValueError:
            return None
        normalized_unit = (unit or "").lower()
        if normalized_unit in {"k", "thousand"}:
            amount *= 1_000
        elif normalized_unit in {"l", "lac", "lacs", "lakh", "lakhs", "लाख", "లక్ష"}:
            amount *= 100_000
        return amount

    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raw_biz = data.get("business_type")
        cleaned_biz = None
        if raw_biz:
            cleaned_biz = re.sub(r"\s+(?:store|shop|business|boutique|dukan)\b", "", str(raw_biz), flags=re.I).strip().capitalize()

        return {
            "business_type": cleaned_biz,
            "product_count": int(data.get("product_count")) if data.get("product_count") is not None else None,
            "budget": float(data.get("budget")) if data.get("budget") is not None else None,
            "budget_min": float(data.get("budget_min")) if data.get("budget_min") is not None else None,
            "budget_max": float(data.get("budget_max")) if data.get("budget_max") is not None else None,
            "timeline": str(data.get("timeline")) if data.get("timeline") else None,
            "features": list(data.get("features", [])) if isinstance(data.get("features"), list) else [],
            "buying_intent": str(data.get("buying_intent", "UNKNOWN")).upper(),
            "language": str(data.get("language", "English")),
            "email": str(data.get("email")) if data.get("email") else None,
        }

    def extract_and_update_lead(self, db: Session, conversation_id: int) -> Optional[Lead]:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        history = [
            {"speaker": m.speaker, "content": m.content, "language": m.language}
            for m in conv.messages
        ]

        extracted = self.extract_from_transcript(history, conversation_id=conv.id)

        lead = db.query(Lead).filter(Lead.conversation_id == conv.id).first()
        if not lead:
            lead = Lead(
                customer_id=conv.customer_id,
                conversation_id=conv.id
            )
            db.add(lead)

        if extracted.get("business_type"):
            lead.business_type = extracted["business_type"]
        if extracted.get("product_count"):
            lead.product_count = extracted["product_count"]
        if extracted.get("budget"):
            lead.budget = extracted["budget"]
        if extracted.get("budget_min") is not None:
            lead.budget_min = extracted["budget_min"]
        if extracted.get("budget_max") is not None:
            lead.budget_max = extracted["budget_max"]
        if extracted.get("timeline"):
            lead.timeline = extracted["timeline"]
        if extracted.get("features"):
            lead.features = list(dict.fromkeys((lead.features or []) + extracted["features"]))
        if extracted.get("buying_intent") and extracted["buying_intent"] != "UNKNOWN":
            intent_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
            current_intent = (lead.buying_intent or "UNKNOWN").upper()
            new_intent = extracted["buying_intent"].upper()
            if new_intent == "HIGH" or intent_rank.get(new_intent, 0) > intent_rank.get(current_intent, 0):
                lead.buying_intent = new_intent
        if extracted.get("email") and conv.customer:
            conv.customer.email = extracted["email"]

        # Run Lead Qualification Engine
        lead_dict = {
            "business_type": lead.business_type,
            "product_count": lead.product_count,
            "budget": lead.budget,
            "budget_min": lead.budget_min,
            "budget_max": lead.budget_max,
            "timeline": lead.timeline,
            "features": lead.features,
            "buying_intent": lead.buying_intent,
        }
        turn_count = len([m for m in conv.messages if m.speaker in ("customer", "user")])
        score, classification, reason = lead_scoring_engine.calculate_score(lead_dict, turn_count=turn_count)
        lead.score = score
        lead.classification = classification
        lead.qualification_reason = reason

        # Generate Personalized Follow-up Draft
        customer_name = conv.customer.name if conv.customer else "Valued Customer"
        cust_lang = conv.customer.preferred_language if conv.customer else "English"
        followup_msg = lead_scoring_engine.generate_followup_message(
            customer_name=customer_name,
            lead_data=lead_dict,
            language=cust_lang
        )

        # Save/Update Action draft
        action = db.query(Action).filter(
            Action.conversation_id == conv.id,
            Action.action_type == "whatsapp_followup"
        ).first()

        if not action:
            action = Action(
                customer_id=conv.customer_id,
                conversation_id=conv.id,
                action_type="whatsapp_followup",
                payload={"message": followup_msg, "recipient": conv.customer.phone if conv.customer else "", "name": customer_name},
                status="draft"
            )
            db.add(action)
        elif action.status == "draft":
            action.payload = {"message": followup_msg, "recipient": conv.customer.phone if conv.customer else "", "name": customer_name}

        customer_email = conv.customer.email if conv.customer else None
        if customer_email:
            email_action = db.query(Action).filter(
                Action.conversation_id == conv.id,
                Action.action_type == "email_followup",
            ).first()
            email_payload = {
                "subject": "Your e-commerce project discussion summary",
                "message": self._build_email_summary(conv, lead_data=lead_dict),
                "recipient": customer_email,
            }
            if email_action is None:
                db.add(Action(
                    customer_id=conv.customer_id,
                    conversation_id=conv.id,
                    action_type="email_followup",
                    payload=email_payload,
                    status="draft",
                ))
            elif email_action.status == "draft":
                email_action.payload = email_payload

        db.commit()
        db.refresh(lead)

        # Attach transient followup_draft for API serialization
        setattr(lead, "followup_draft", followup_msg)
        return lead

    @staticmethod
    def _build_email_summary(conv: Conversation, lead_data: Dict[str, Any]) -> str:
        customer_name = conv.customer.name if conv.customer else "there"
        budget_min = lead_data.get("budget_min")
        budget_max = lead_data.get("budget_max")
        if budget_min is not None and budget_max is not None and budget_min != budget_max:
            budget_text = f"₹{budget_min:,.0f}–₹{budget_max:,.0f}"
        elif lead_data.get("budget") is not None:
            budget_text = f"₹{lead_data['budget']:,.0f}"
        else:
            budget_text = "Not discussed"

        features = lead_data.get("features") or []
        feature_text = "\n".join(f"- {feature}" for feature in features) or "- No specific features captured"
        customer_text = " ".join(
            message.content.lower()
            for message in conv.messages
            if message.speaker in ("customer", "user")
        )
        proposal_status = (
            "Requested during the conversation"
            if "proposal" in customer_text or "quote" in customer_text
            else "Not explicitly requested"
        )
        return (
            f"Hi {customer_name},\n\n"
            "Thank you for speaking with us. Here is a written recap of what we discussed:\n\n"
            f"- Business: {lead_data.get('business_type') or 'Not specified'}\n"
            f"- Products at launch: {lead_data.get('product_count') if lead_data.get('product_count') is not None else 'Not discussed'}\n"
            f"- Budget: {budget_text}\n"
            f"- Target launch: {lead_data.get('timeline') or 'Not discussed'}\n"
            f"- Buying intent: {lead_data.get('buying_intent') or 'Not confirmed'}\n"
            f"- Proposal/quote: {proposal_status}\n"
            f"- Requested features:\n{feature_text}\n\n"
            "Please reply if anything needs correcting or if you would like to discuss the proposal and next steps.\n\n"
            "Best regards,\nLeadPilot AI"
        )

extraction_service = ExtractionService()
