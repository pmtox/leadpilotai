# 📋 LeadPilot AI — Project Execution & Task Tracker

> **Product**: Autonomous Multilingual AI Sales Agent  
> **Architecture**: React (Vite) + FastAPI (Python) + SQLite (SQLAlchemy) + LLM + Browser Voice + Action Engine  
> **Current Sprint Checkpoint**: **`CP-02` — LLM Conversation Engine [COMPLETED]**  
> **Next Milestone**: **`CP-03` — Structured Information Extraction (Hour 3)**

---

## 🏆 Sprint Progress Summary

| Checkpoint | Milestone Description | Target Hour | Status | Verified Deliverable |
|:---|:---|:---:|:---:|:---|
| **CP-01** | **Project Foundation** | **Hour 1** | **✅ COMPLETED** | Git, `.gitignore`, React + Vite, FastAPI, SQLite DB, Health tests (2/2) |
| **CP-02** | **Text-based AI Conversation** | **Hour 2** | **✅ COMPLETED** | Unified LLM service (Gemini/Groq/Simulator), multilingual dialogue (EN/HI/TE), conversation history persistence, interactive chat UI, 7/7 tests passed |
| **CP-03** | Structured Information Extraction | Hour 3 | ⏳ UP NEXT | Requirement schema, budget/products/timeline extraction engine, validation rules |
| **CP-04** | Lead Qualification Engine | Hour 4 | 📋 Planned | Scoring rules, HOT/WARM/COLD classification, personalized follow-ups |
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
| **Speech Recognition** | Voice-to-Text | Whisper / Browser STT | *PLANNED (CP-05)* |
| **Speech Generation** | Text-to-Voice | Web SpeechSynthesis API | *PLANNED (CP-05)* |
| **Information Extraction** | Entity & Requirement Parsing | Structured Output Schema | *UP NEXT (CP-03)* |
| **Lead Qualification** | Rule-Based Qualification & Scoring | Python Rule Engine | *NOT STARTED (CP-04)* |
| **Action & Callback Engine** | Follow-Up & Task Dispatch | APScheduler + WhatsApp API | *NOT STARTED (CP-07/08)* |
| **Automated Testing** | Regression & Integration Testing | Pytest | **7/7 PASSED (0 WARNINGS)** |
| **Documentation & Logs** | Architecture, Spec, and Tasks | Docx + Markdown | **IN PROGRESS & SYNCED** |

---

## 🛠️ Hour 2: Checkpoint CP-02 Execution Log

- [x] **LLM Service & Provider Integration**:
  - Implemented `backend/app/services/llm_service.py` with multi-provider abstraction:
    - **Google Gemini API**: Direct REST integration supporting `gemini-1.5-flash` with system instruction formatting.
    - **Groq API**: OpenAI-compatible REST integration supporting Llama models.
    - **Intelligent Multilingual Sales Simulator**: Fallback when external API keys are not supplied, enabling full consultative sales simulation offline and in test environments.
- [x] **Consultative Sales System Prompting**:
  - Authored comprehensive `SALES_AGENT_SYSTEM_PROMPT` in `backend/app/core/prompts.py`:
    - Enforces 1–3 sentence concise replies suitable for voice and interactive chat.
    - Covers business type, product catalog size, budget (INR), launch timeline, and required features.
    - Handles polite customer opt-outs.
- [x] **Multilingual Support (English, Hindi, Telugu)**:
  - Added automatic Unicode script and keyword detection in `detect_language`.
  - Implemented localized greetings and conversational responses for English, Hindi (हिंदी), and Telugu (తెలుగు).
- [x] **Conversation State & History Persistence**:
  - Implemented `ConversationService` in `backend/app/services/conversation_service.py`.
  - Stored every turn in the `messages` table with speaker (`agent`/`customer`), timestamp, and language.
  - Reconstructs chronological message history and passes it to the LLM on every turn.
  - Added session completion with duration tracking and turn summary.
- [x] **Frontend Live Chat Simulator**:
  - Upgraded `frontend/src/App.jsx` with customer registration and interactive sales chat.
  - Added language selector pills for English, Hindi, and Telugu.
  - Added real-time message bubble stream, typing indicators, and session termination controls.
- [x] **Test Verification**:
  - Created `tests/test_conversations.py` with 5 automated test cases:
    - `test_language_detection`
    - `test_english_conversation_flow`
    - `test_hindi_conversation_flow`
    - `test_telugu_conversation_flow`
    - `test_customer_opt_out`
  - Total test suite: **7 passed in 0.92s** with 0 warnings.
- [x] **Document Synchronization**:
  - Updated `LEADPILOT AI.docx` with:
    - Header Status: `CP-02 Completed / LLM Engine Operational`.
    - Checkpoint CP-02 marked `[COMPLETED]`.
    - Updated Table 5 component status (LLM provider, Conversation engine, Testing).
    - Appended Hour 2 deliverables to Section 22.

---

## ⏩ Next Immediate Tasks (Hour 3 — Checkpoint CP-03)

1. Define structured customer requirement extraction schema in `backend/app/schemas/lead.py`.
2. Implement extraction engine in `backend/app/services/extraction_service.py` to extract:
   - `business_type` (Clothing, Electronics, Grocery, etc.)
   - `product_count` (Integer)
   - `budget` (Float INR)
   - `timeline` (e.g., "next month", "2 weeks")
   - `features` (Payment gateway, delivery tracking, inventory, etc.)
   - `buying_intent` (HIGH, MEDIUM, LOW)
3. Integrate extraction after each conversation turn to update the `leads` table in SQLite.
4. Expose extracted lead state in conversation responses and frontend UI.
5. Create automated test cases in `tests/test_extraction.py` validating requirement extraction across English, Hindi, and Telugu turns.
6. Synchronize CP-03 completion in `PROJECT_TASKS.md` and `LEADPILOT AI.docx`.
