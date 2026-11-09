# 📋 LeadPilot AI — Project Execution & Task Tracker

> **Product**: Autonomous Multilingual AI Sales Agent  
> **Architecture**: React (Vite) + FastAPI (Python) + SQLite (SQLAlchemy) + LLM + Browser Voice + Action Engine  
> **Current Sprint Checkpoint**: **`CP-04` — Lead Qualification Engine [COMPLETED]**  
> **Next Milestone**: **`CP-05` — Browser-based Voice Engine (Hour 5)**

---

## 🏆 Sprint Progress Summary

| Checkpoint | Milestone Description | Target Hour | Status | Verified Deliverable |
|:---|:---|:---:|:---:|:---|
| **CP-01** | **Project Foundation** | **Hour 1** | **✅ COMPLETED** | Git, `.gitignore`, React + Vite, FastAPI, SQLite DB, Health tests (2/2) |
| **CP-02** | **Text-based AI Conversation** | **Hour 2** | **✅ COMPLETED** | Unified LLM service (Gemini/Groq/Simulator), multilingual dialogue (EN/HI/TE), conversation history persistence, interactive chat UI, 7/7 tests passed |
| **CP-03** | **Structured Information Extraction** | **Hour 3** | **✅ COMPLETED** | ExtractionService, Indian currency/Lakh parser, multilingual entity extraction (EN/HI/TE), cumulative state, live lead card in UI, 11/11 tests passed |
| **CP-04** | **Lead Qualification Engine** | **Hour 4** | **✅ COMPLETED** | 0-100 scoring engine, HOT/WARM/COLD status, qualification reason, personalized follow-ups (EN/HI/TE), SQLite draft action, 16/16 tests passed |
| **CP-05** | Browser-based Voice Engine | Hour 5 | ⏳ UP NEXT | Browser Speech Recognition (STT), SpeechSynthesis (TTS), microphone controls, turn-taking |
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
| **Lead Qualification** | Rule-Based Qualification & Scoring | Python Rule Engine (0-100) | **INITIALIZED & OPERATIONAL** |
| **Speech Recognition** | Voice-to-Text | Web SpeechRecognition / Whisper | *UP NEXT (CP-05)* |
| **Speech Generation** | Text-to-Voice | Web SpeechSynthesis API | *UP NEXT (CP-05)* |
| **Action & Callback Engine** | Follow-Up & Task Dispatch | APScheduler + WhatsApp API | *NOT STARTED (CP-07/08)* |
| **Automated Testing** | Regression & Integration Testing | Pytest | **16/16 PASSED (0 WARNINGS)** |
| **Documentation & Logs** | Architecture, Spec, and Tasks | Docx + Markdown | **IN PROGRESS & SYNCED** |

---

## 🛠️ Hour 4: Checkpoint CP-04 Execution Log

- [x] **Transparent Lead Scoring Algorithm**:
  - Implemented `LeadScoringEngine` in `backend/app/services/lead_scoring.py`:
    - **Buying Intent**: Up to 30 points (HIGH=30, MEDIUM=15, LOW/UNKNOWN=0-5).
    - **Budget Readiness**: Up to 25 points (>= ₹50,000=25, < ₹50,000=15, unknown=0).
    - **Timeline Readiness**: Up to 20 points (Immediately/2 weeks=20, Next month=15, 3 months=10).
    - **Requirement Clarity**: Up to 15 points (Business type=5, Product count=5, Features=5).
    - **Engagement**: Up to 10 points (3+ turns=10, 2 turns=5).
  - Explicit rule-based scoring without LLM fabrication.
- [x] **HOT / WARM / COLD Classification**:
  - Configured thresholds: **HOT (70–100)**, **WARM (40–69)**, **COLD (0–39)**.
  - Automatically synthesizes plain-language qualification explanation itemizing each factor.
- [x] **Personalized Follow-up Generator**:
  - Generates personalized proposal drafts in **English**, **Hindi (हिंदी)**, and **Telugu (తెలుగు)** citing the exact business category, product volume, confirmed budget, and target timeline.
  - Automatically records draft in the SQLite `actions` table (`action_type: whatsapp_followup`, `status: draft`).
- [x] **Frontend Score Gauge & Badge UI**:
  - Upgraded `frontend/src/App.jsx` with a real-time Lead Qualification header:
    - Glowing status badge (`🔥 HOT LEAD`, `☀️ WARM LEAD`, `❄️ COLD LEAD`).
    - Dynamic progress bar reflecting lead score (`X / 100`).
    - Transparent qualification breakdown card.
    - WhatsApp follow-up proposal draft preview.
- [x] **Test Verification**:
  - Authored `tests/test_lead_scoring.py` covering:
    - `test_hot_lead_scoring`
    - `test_warm_lead_scoring`
    - `test_cold_lead_scoring`
    - `test_personalized_followup_generation` (EN, HI, TE)
    - `test_lead_qualification_end_to_end`
  - Total test suite: **16 passed in 8.90s** with 0 warnings.
- [x] **Document Synchronization**:
  - Updated `LEADPILOT AI.docx` with:
    - Header Status: `CP-04 Completed / Lead Intelligence Operational`.
    - Checkpoint CP-04 marked `[COMPLETED]`.
    - Updated Table 5 component status (`Lead scoring` -> `INITIALIZED & OPERATIONAL`).
    - Appended Hour 4 deliverables to Section 22.

---

## ⏩ Next Immediate Tasks (Hour 5 — Checkpoint CP-05)

1. Implement Browser Microphone Capture and Speech Recognition (Web Speech API / Whisper STT endpoint).
2. Integrate Speech Synthesis (TTS) using browser `window.speechSynthesis` with language matching for English, Hindi, and Telugu voices.
3. Add live voice recording toggle, audio wave visualizer, and transcription feedback in the React dashboard.
4. Implement turn-taking logic (listen → transcribe → send turn → speak response).
5. Add audio turn API endpoint in FastAPI: `POST /api/conversations/{id}/audio`.
6. Author tests in `tests/test_voice.py` verifying speech turn handling.
7. Synchronize CP-05 completion in `PROJECT_TASKS.md` and `LEADPILOT AI.docx`.
