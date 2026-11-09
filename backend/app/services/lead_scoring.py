"""Lead Qualification Engine for LeadPilot AI.
Implements deterministic scoring (0-100), HOT/WARM/COLD classification,
qualification explanations, and personalized follow-up generation.
"""
from typing import Dict, Any, Tuple, Optional

class LeadScoringEngine:
    """Deterministic, transparent lead scoring and qualification."""

    def calculate_score(self, lead_data: Dict[str, Any], turn_count: int = 1) -> Tuple[int, str, str]:
        """Compute score (0-100), classification (HOT/WARM/COLD), and human-readable explanation."""
        score = 0
        reasons = []

        # 1. Buying Intent (Max 30 pts)
        intent = (lead_data.get("buying_intent") or "UNKNOWN").upper()
        if intent == "HIGH":
            score += 30
            reasons.append("High buying intent expressed")
        elif intent == "MEDIUM":
            score += 15
            reasons.append("Moderate buying interest")
        else:
            reasons.append("Buying intent unconfirmed")

        # 2. Budget Readiness (Max 25 pts)
        budget = lead_data.get("budget")
        if budget is not None and budget >= 50000:
            score += 25
            reasons.append(f"Strong budget (₹{int(budget):,})")
        elif budget is not None and budget > 0:
            score += 15
            reasons.append(f"Modest budget (₹{int(budget):,})")
        else:
            reasons.append("Budget not yet determined")

        # 3. Timeline Readiness (Max 20 pts)
        timeline = (lead_data.get("timeline") or "").lower()
        if any(t in timeline for t in ["immediately", "2 weeks", "urgent", "two weeks"]):
            score += 20
            reasons.append("Immediate/Short launch timeline")
        elif any(t in timeline for t in ["next month", "1 month", "this month"]):
            score += 15
            reasons.append("Near-term launch timeline (within 1 month)")
        elif any(t in timeline for t in ["3 months", "next quarter"]):
            score += 10
            reasons.append("Extended timeline (3 months)")
        else:
            reasons.append("Timeline unknown")

        # 4. Requirement Clarity (Max 15 pts)
        business_type = lead_data.get("business_type")
        product_count = lead_data.get("product_count")
        features = lead_data.get("features") or []

        if business_type:
            score += 5
            reasons.append(f"Business category: {business_type}")
        if product_count:
            score += 5
            reasons.append(f"Catalog size: {product_count} items")
        if features:
            score += 5
            reasons.append(f"{len(features)} feature requirements identified")

        # 5. Engagement (Max 10 pts)
        if turn_count >= 3:
            score += 10
            reasons.append("High conversation engagement (3+ turns)")
        elif turn_count >= 2:
            score += 5
            reasons.append("Active conversation participation")

        # Classification thresholds per specification:
        # HOT: 70–100, WARM: 40–69, COLD: 0–39
        if score >= 70:
            classification = "HOT"
        elif score >= 40:
            classification = "WARM"
        else:
            classification = "COLD"

        explanation = f"Classified as {classification} ({score}/100 pts). Key factors: " + "; ".join(reasons) + "."
        return score, classification, explanation

    def generate_followup_message(
        self,
        customer_name: str,
        lead_data: Dict[str, Any],
        language: str = "English"
    ) -> str:
        """Generate personalized follow-up message draft addressing collected requirements."""
        biz = lead_data.get("business_type") or "e-commerce"
        prods = lead_data.get("product_count")
        budget = lead_data.get("budget")
        features = lead_data.get("features") or []
        timeline = lead_data.get("timeline") or "your target timeline"

        feat_str = ", ".join(features) if features else "payment gateway and order management"
        prod_str = f"with around {prods} products" if prods else ""
        budget_str = f"within your estimated budget of ₹{int(budget):,}" if budget else "tailored to your budget"

        if language == "Hindi":
            hindi_prod = f"{prods} उत्पादों" if prods else "आपके उत्पादों"
            hindi_budget = f"₹{int(budget):,} के बजट में" if budget else "आपके बजट अनुसार"
            return (
                f"नमस्ते {customer_name}! LeadPilot AI से जुड़ने के लिए धन्यवाद। "
                f"हमने आपके {biz} व्यवसाय के लिए {hindi_prod} और {feat_str} के साथ ऑनलाइन स्टोर का प्रस्ताव तैयार किया है, "
                f"जो {hindi_budget} उपलब्ध होगा। क्या हम इस पर चर्चा करने के लिए एक छोटी कॉल शेड्यूल करें?"
            )
        elif language == "Telugu":
            telugu_prod = f"{prods} ఉత్పత్తులతో" if prods else "మీ ఉత్పత్తులతో"
            telugu_budget = f"₹{int(budget):,} బడ్జెట్‌లో" if budget else "మీ బడ్జెట్‌కు అనుగుణంగా"
            return (
                f"నమస్కారం {customer_name}! LeadPilot AI తో సంప్రదించినందుకు ధన్యవాదాలు. "
                f"మీ {biz} వ్యాపారం కోసం {telugu_prod} మరియు {feat_str} ఫీచర్లతో ఆన్‌లైన్ స్టోర్ ప్రతిపాదన సిద్ధంగా ఉంది ({telugu_budget}). "
                f"తదుపరి వివరాలు చర్చించడానికి తగిన సమయం తెలపగలరు."
            )
        else:
            return (
                f"Hi {customer_name}, thank you for speaking with LeadPilot AI today! "
                f"Based on our discussion, we have drafted a custom plan for your {biz} online store {prod_str}, "
                f"featuring {feat_str}, designed to launch by {timeline} {budget_str}. "
                f"Would you like us to schedule a brief follow-up call with our senior technical architect?"
            )

lead_scoring_engine = LeadScoringEngine()
