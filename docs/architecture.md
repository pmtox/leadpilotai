# 🏛️ LeadPilot AI — Architecture & Technical Design

## 1. System Overview
LeadPilot AI is an autonomous, multilingual AI-powered sales agent designed to interact with e-commerce prospects, assess buying intent, qualify leads into **HOT**, **WARM**, or **COLD**, and trigger automated follow-up workflows.

```
                  ┌──────────────────────┐
                  │    Sales Operator    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   React Dashboard    │
                  │     (Vite + CSS)     │
                  └──────────┬───────────┘
                             │
                      REST & WebSockets
                             │
                             ▼
                  ┌──────────────────────┐
                  │   FastAPI Backend    │
                  └──────────┬───────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  LLM Engine  │      │ SQLite DB    │      │ Action Engine│
│ Gemini/Groq  │      │ SQLAlchemy   │      │ WhatsApp/Cal │
└──────────────┘      └──────────────┘      └──────────────┘
```

## 2. Directory Structure
```
LeadPilotAI/
├── frontend/             # React + Vite client
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Dashboard, Call Center, Leads views
│   │   ├── hooks/        # Audio & WebSocket hooks
│   │   ├── services/     # API client functions
│   │   ├── context/      # Global state
│   │   ├── utils/        # Formatters & language helpers
│   │   ├── App.jsx       # Root view
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/              # FastAPI Python server
│   ├── app/
│   │   ├── main.py       # FastAPI application entrypoint
│   │   ├── api/          # Route handlers (customers, conv, leads, actions)
│   │   ├── core/         # Config and system prompts
│   │   ├── services/     # LLM, speech, scoring, WhatsApp services
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic v2 schemas
│   │   └── database/     # DB engine and session
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   ├── architecture.md
│   └── experiment_log.md
├── tests/                # Automated pytest suite
├── PROJECT_TASKS.md      # Sprint progress tracking
├── LEADPILOT AI.docx     # Project report and requirements
├── .gitignore            # Confidential information protection
└── README.md
```

## 3. Data Flow
1. **Initiation**: Operator registers prospect details (Name, Phone, Preferred Language).
2. **Conversation**: AI greets prospect in preferred language (English, Hindi, Telugu).
3. **Turn Processing**: Speech/Text turns captured and dispatched to LLM.
4. **Structured Extraction**: Extracted requirements (budget, product count, timeline, features) saved to `leads` table.
5. **Scoring & Classification**: Lead scored (0-100) and categorized into HOT, WARM, or COLD.
6. **Action Dispatch**: WhatsApp follow-up or callback scheduled based on classification.

