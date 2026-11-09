# 📋 LeadPilot AI — Project Execution & Task Tracker

> **Product**: Autonomous Multilingual AI Sales Agent  
> **Architecture**: React (Vite) + FastAPI (Python) + SQLite (SQLAlchemy) + LLM + Browser Voice + Action Engine  
> **Current Sprint Checkpoint**: **`CP-03` — Structured Information Extraction [COMPLETED]**  
> **Next Milestone**: **`CP-04` — Lead Qualification Engine (Hour 4)**

---

## 🏆 Sprint Progress Summary

| Checkpoint | Milestone Description | Target Hour | Status | Verified Deliverable |
|:---|:---|:---:|:---:|:---|
| **CP-01** | **Project Foundation** | **Hour 1** | **✅ COMPLETED** | Git, `.gitignore`, React + Vite, FastAPI, SQLite DB, Health tests (2/2) |
| **CP-02** | **Text-based AI Conversation** | **Hour 2** | **✅ COMPLETED** | Unified LLM service (Gemini/Groq/Simulator), multilingual dialogue (EN/HI/TE), conversation history persistence, interactive chat UI, 7/7 tests passed |
| **CP-03** | **Structured Information Extraction** | **Hour 3** | **✅ COMPLETED** | ExtractionService, Indian currency/Lakh parser, multilingual entity extraction (EN/HI/TE), cumulative state, live lead card in UI, 11/11 tests passed |
| **CP-04** | Lead Qualification Engine | Hour 4 | ⏳ UP NEXT | Scoring algorithm (0-100), HOT/WARM/COLD classification, qualification reasoning, personalized follow-up generation |
| **CP-05** | Browser-based Voice Engine | Hour 5 | 📋 Planned | Whisper transcription, speech synthesis, mic capture |
| **CP-06** | Interactive Dashboard | Hour 6 | 📋 Planned | Live call view, lead qualification cards, transcript streams |
| **CP-07** | WhatsApp Follow-Up Workflow | Hour 7 | 📋 Planned | Cloud API template dispatch / Draft fallback |
| **CP-08** | Callback Scheduler | Hour 8 | 📋 Planned | DateTime extraction, reminder persistence, calendar view |
| **CP-09** | End-to-End Validation | Hour 9 | 📋 Planned | Multilingual conversation & qualification integration tests |
| **CP-10** | Submission-Ready MVP | Hour 10 | 📋 Planned | Architecture docs, demo recording, deployment runbook |

---

## 🔍 Detailed Component Status

| Component | Architecture Role | Target Tech | Status |
|:---|:---|:---|:---:|
| **Project Identity & Scope** | Anti-Scope Creep Rules & Spec | Markdown / Docx | **LOCKED** |
| **Security & Privacy** | Credential protection & Git rules | `.gitignore`, `.env.example` | **ACTIVE & PROTECTED** |
| **Frontend Foundation** | User Interface & Audio Capture | React 19 + Vite | **INITIALIZED & OPERATIONAL** |
| **Backend Foundation** | REST API & WebSocket Server | FastAPI + Uvicorn | **INITIALIZED & OPERATIONAL** |
| **Database & ORM** | Persistent storage | SQLite + SQLAlchemy | **INITIALIZED & OPERATIONAL** |
| **LLM Engine** | Multilingual Dialogue & Reasoning | Gemini / Groq / Fallback Simulator | **CONFIGURED & OPERATIONAL** |
| **Conversation Engine** | Session lifecycles & Turn Management | Python + SQLite Messages | **INITIALIZED & OPERATIONAL** |
| **Information Extraction** | Entity & Requirement Parsing | Structured Output + Regex/NLP | **INITIALIZED & OPERATIONAL** |
| **Lead Qualification** | Rule-Based Qualification & Scoring | Python Rule Engine | *UP NEXT (CP-04)* |
| **Speech Recognition** | Voice-to-Text | Whisper / Browser STT | *PLANNED (CP-05)* |
| **Speech Generation** | Text-to-Voice | Web SpeechSynthesis API | *PLANNED (CP-05)* |
| **Action & Callback Engine** | Follow-Up & Task Dispatch | APScheduler + WhatsApp API | *NOT STARTED (CP-07/08)* |
| **Automated Testing** | Regression & Integration Testing | Pytest | **11/11 PASSED (0 WARNINGS)** |
| **Documentation & Logs** | Architecture, Spec, and Tasks | Docx + Markdown | **IN PROGRESS & SYNCED** |

---

## 🛠️ Hour 3: Checkpoint CP-03 Execution Log

- [x] **Extraction Service & Pipeline**:
  - Implemented `backend/app/services/extraction_service.py` to extract:
    - `business_type`: Clothing, Electronics, Grocery, Jewelry, Footwear, Cosmetics, Bakery, Furniture, Handmade crafts.
    - `product_count`: Approximate or exact product count.
    - `budget`: INR currency parsing supporting standard numbers, `₹`, `Rs`, `k` notation (e.g. `80k`), and Indian `Lakh` notation (e.g. `1.5 lakh`).
    - `timeline`: "Immediately", "2 weeks", "Next month", "3 months".
    - `features`: "Online Payments (UPI/Cards)", "Delivery Tracking", "Inventory Management", "WhatsApp Notifications", "Multi-currency".
    - `buying_intent`: "HIGH", "MEDIUM", "LOW".
- [x] **Multilingual Support (EN / HI / TE)**:
  - Added Hindi entity and currency stem matching (`कपड़`, `किराना`, `लाख`, `₹50,000`).
  - Added Telugu entity and currency stem matching (`బట్ట`, `ఎలక్ట్రానిక్స్`, `లక్ష`).
- [x] **Cumulative State Persistence**:
  - Automatically updates the `leads` table in SQLite after each customer turn without erasing previously extracted values.
- [x] **API & Response Schema**:
  - Extended `ConversationResponse` with `lead: Optional[LeadResponse]`, delivering live requirement state to callers.
- [x] **Frontend Lead Intelligence Card**:
  - Enhanced `frontend/src/App.jsx` with a 2-column view displaying live requirement badges, budget, timeline, and feature tags.
- [x] **Test Verification**:
  - Authored `tests/test_extraction.py` covering doc sample extraction, Hindi, Telugu Lakhs, and multi-turn incremental state.
  - Test suite: **11 passed in 1.08s** with 0 warnings.
- [x] **Document Synchronization**:
  - Updated `LEADPILOT AI.docx` with:
    - Header Status: `CP-03 Completed / Extraction Engine Operational`.
    - Checkpoint CP-03 marked `[COMPLETED]`.
    - Updated Table 5 component status (`Requirement extraction` -> `INITIALIZED & OPERATIONAL`).
    - Appended Hour 3 deliverables to Section 22.

---

## ⏩ Next Immediate Tasks (Hour 4 — Checkpoint CP-04)

1. Implement scoring algorithm and classification logic in `backend/app/services/lead_scoring.py`:
   - Calculate score from 0 to 100 based on budget, timeline, catalog size, feature clarity, and buying intent.
   - Categorize lead into **HOT**, **WARM**, or **COLD**.
   - Generate transparent human-readable qualification explanation.
2. Implement personalized post-conversation follow-up message generation in customer's preferred language.
3. Automatically compute qualification score upon conversation turn / conclusion.
4. Display HOT / WARM / COLD status badge and score gauge in the frontend dashboard.
5. Create automated test cases in `tests/test_lead_scoring.py` for HOT, WARM, and COLD customer scenarios.
6. Synchronize CP-04 completion in `PROJECT_TASKS.md` and `LEADPILOT AI.docx`.
