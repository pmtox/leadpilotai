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
    "Delivery Tracking": ["delivery", "shipping", "tracking", "courier", "डिलीवरी", "డెలివరీ"],
    "Inventory Management": ["inventory", "stock", "स्टॉक", "ఇన్వెంటరీ"],
    "WhatsApp Notifications": ["whatsapp", "sms", "notification", "व्हाट्सएप", "వాట్సాప్"],
    "Multi-currency / International": ["international", "export", "dollar", "nri"]
}

class ExtractionService:
    def extract_from_transcript(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        customer_texts = [
            m.get("content", "")
            for m in conversation_history
            if m.get("speaker") in ("customer", "user")
        ]
        full_customer_transcript = " ".join(customer_texts)

        if llm_service.is_live_provider_available():
            try:
                llm_extracted = self._extract_with_llm(conversation_history)
                if llm_extracted and any(llm_extracted.values()):
                    return self._clean_extracted_data(llm_extracted)
            except Exception as e:
                logger.warning(f"LLM extraction error: {e}. Falling back to rule extraction.")

        return self._extract_with_rules(full_customer_transcript)

    def _extract_with_llm(self, conversation_history: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        prompt = (
            f"{EXTRACTION_SYSTEM_PROMPT}\n\n"
            f"Conversation History:\n"
            + "\n".join([f"{m.get('speaker', 'user')}: {m.get('content', '')}" for m in conversation_history])
            + "\n\nOutput only JSON:"
        )

        reply = llm_service.generate_reply(
            messages=[{"speaker": "customer", "content": prompt}],
            system_prompt=EXTRACTION_SYSTEM_PROMPT
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
            "timeline": None,
            "features": [],
            "buying_intent": "UNKNOWN",
            "language": "English"
        }

        # 1. Detect Business Type
        for b_type, syns in BUSINESS_TYPES.items():
            if any(syn in lower for syn in syns):
                result["business_type"] = b_type.capitalize()
                break

        # 2. Extract Product Count
        prod_match = re.search(r"(\d+)\s*(?:products?|items?|articles?|pieces?|skus?|उत्पाद|वस्तुएं|వస్తువులు)?", lower)
        prod_specific = re.search(r"(\d+)\s*(?:products|items|skus|pieces|उत्पाद|वस्तु|వస్తువులు|వస్తు)", lower)
        if prod_specific:
            result["product_count"] = int(prod_specific.group(1))
        elif prod_match:
            val = int(prod_match.group(1))
            if val < 5000 and not any(curr in lower for curr in ["₹", "rs", "rupees", "lakh", "k"]):
                result["product_count"] = val

        # 3. Extract Budget
        budget_val = None
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakhs?|lac|लाख|लख|లక్ష)", lower)
        if lakh_match:
            budget_val = float(lakh_match.group(1)) * 100000
        else:
            k_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+)\s*k\b", lower)
            if k_match:
                budget_val = float(k_match.group(1)) * 1000
            else:
                curr_match = re.search(r"(?:₹|rs\.?|inr|budget\s*is|बजट|బడ్జెట్)\s*[:=]?\s*(\d[\d,]*\d|\d+)", lower)
                if curr_match:
                    num_str = curr_match.group(1).replace(",", "")
                    budget_val = float(num_str)
                else:
                    big_num = re.search(r"\b(\d{4,7})\b", lower)
                    if big_num:
                        budget_val = float(big_num.group(1))

        if budget_val and budget_val > 500:
            result["budget"] = budget_val

        # 4. Extract Timeline
        if any(t in lower for t in ["next month", "1 month", "अगले महीने", "వచ్చే నెల"]):
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

        # 6. Buying Intent determination
        if result["budget"] and result["timeline"] and result["business_type"]:
            result["buying_intent"] = "HIGH"
        elif result["business_type"] or result["budget"]:
            result["buying_intent"] = "MEDIUM"
        else:
            result["buying_intent"] = "LOW"

        return result

    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raw_biz = data.get("business_type")
        cleaned_biz = None
        if raw_biz:
            cleaned_biz = re.sub(r"\s+(?:store|shop|business|boutique|dukan)\b", "", str(raw_biz), flags=re.I).strip().capitalize()

        return {
            "business_type": cleaned_biz,
            "product_count": int(data.get("product_count")) if data.get("product_count") is not None else None,
            "budget": float(data.get("budget")) if data.get("budget") is not None else None,
            "timeline": str(data.get("timeline")) if data.get("timeline") else None,
            "features": list(data.get("features", [])) if isinstance(data.get("features"), list) else [],
            "buying_intent": str(data.get("buying_intent", "UNKNOWN")).upper(),
            "language": str(data.get("language", "English"))
        }

    def extract_and_update_lead(self, db: Session, conversation_id: int) -> Optional[Lead]:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        history = [
            {"speaker": m.speaker, "content": m.content, "language": m.language}
            for m in conv.messages
        ]

        extracted = self.extract_from_transcript(history)

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
        if extracted.get("timeline"):
            lead.timeline = extracted["timeline"]
        if extracted.get("features"):
            existing_feats = set(lead.features or [])
            new_feats = existing_feats.union(set(extracted["features"]))
            lead.features = list(new_feats)
        if extracted.get("buying_intent") and extracted["buying_intent"] != "UNKNOWN":
            lead.buying_intent = extracted["buying_intent"]

        # Run Lead Qualification Engine
        lead_dict = {
            "business_type": lead.business_type,
            "product_count": lead.product_count,
            "budget": lead.budget,
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
        else:
            action.payload = {"message": followup_msg, "recipient": conv.customer.phone if conv.customer else "", "name": customer_name}

        db.commit()
        db.refresh(lead)

        # Attach transient followup_draft for API serialization
        setattr(lead, "followup_draft", followup_msg)
        return lead

extraction_service = ExtractionService()
