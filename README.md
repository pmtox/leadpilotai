# LeadPilot AI

LeadPilot AI is a multilingual sales-assistance app for e-commerce website projects. It helps teams talk with prospective customers, capture their requirements, qualify leads, and prepare follow-ups.

## What it does

- Supports text and voice conversations in English, Hindi, and Telugu.
- Collects business category, catalog size, budget, target launch date, and requested features.
- Scores leads and organizes them in a CRM-style dashboard.
- Creates written call recaps and can email them automatically when SMTP is configured.
- Prepares WhatsApp follow-up drafts; sending requires customer opt-in.
- Supports Gemini and Groq for AI-generated conversation replies, with local rule-based qualification and configurable request limits.

## Technology

- **Frontend:** React and Vite
- **Backend:** Python, FastAPI, and SQLAlchemy
- **Database:** SQLite by default
- **AI providers:** Gemini and Groq

## Run locally

### Backend

```powershell
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
Copy-Item backend\.env.example backend\.env
```

Add a Gemini or Groq API key to `backend/.env`, then start the API:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

The API is at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend is at `http://localhost:5173`.

## Configuration

AI replies are limited to 2 provider requests per conversation and 100 requests per day per running backend process by default. Configure `LLM_MAX_CALLS_PER_CONVERSATION` and `LLM_MAX_CALLS_PER_DAY` in `backend/.env`. Rule-based lead extraction is enabled by default; optional model-based extraction can be enabled with `LLM_EXTRACTION_ENABLED=true`. These process-local limits reset when the backend restarts; use provider-side quotas for hard spending limits.

To send call recaps automatically when a conversation ends, configure SMTP in `backend/.env`. For Gmail, use a Google App Password:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your-sending-address@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM_EMAIL=your-sending-address@gmail.com
```

If SMTP is unavailable or delivery fails, the recap remains in the Action Center as a draft. Keep real API keys, passwords, customer data, and local environment files out of source control.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```
