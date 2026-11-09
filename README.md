# 🚀 LeadPilot AI

**Autonomous Multilingual AI Sales Agent** for e-commerce website qualification and consultative selling.

---

## ⚡ Quick Start

### 1. Backend Setup
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r backend/requirements.txt

# Configure environment variables
copy backend\.env.example backend\.env
# Add your GEMINI_API_KEY or GROQ_API_KEY in backend/.env
# To send recap emails, also configure the SMTP settings described below

# Run backend development server
uvicorn backend.app.main:app --reload --port 8000
```
Backend API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development server will be available at `http://localhost:5173`.

### LLM usage controls
Lead extraction uses local rules by default, avoiding an extra model request on each conversation turn. AI-generated replies are capped at 2 provider requests per conversation and 100 requests per day per running backend process. Adjust `LLM_MAX_CALLS_PER_CONVERSATION` and `LLM_MAX_CALLS_PER_DAY` in `backend/.env`; set either to `0` to disable those calls. Set `LLM_EXTRACTION_ENABLED=true` only if you want to opt back into model-based extraction. These in-process caps reset when the backend restarts and are not a hard billing limit; set usage quotas in the Gemini/Groq provider consoles for a hard cap.

### Automatic email recap delivery
If an email is entered for the customer, the call summary is sent automatically when the conversation ends. Configure SMTP in `backend/.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your-sending-address@gmail.com
SMTP_PASSWORD=your-provider-app-password
SMTP_FROM_EMAIL=your-sending-address@gmail.com
```

For Gmail, use a Google App Password (not your regular account password). For another provider, use its SMTP hostname, port, and credentials. If SMTP is not configured or delivery fails, the recap is retained as a draft in the Action Center. Never put real credentials in `.env.example`.

### 3. Running Tests
```bash
.\.venv\Scripts\python.exe -m pytest tests/
```

---

## 🔒 Confidentiality & Security
All sensitive credentials, environment files (`.env`), API keys, SQLite databases (`*.db`), audio recordings, and customer conversation transcripts are strictly ignored by `.gitignore` and must never be committed to source control.

---

## 📊 Sprint Status & Checkpoints
- **Current Milestone**: `CP-01` — Project Foundation [COMPLETED]
- **Next Milestone**: `CP-02` — LLM Conversation Engine
- See [LEADPILOT AI.docx](./LEADPILOT%20AI.docx) for the official project specification.
