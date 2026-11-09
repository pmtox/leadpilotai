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
- See [PROJECT_TASKS.md](./PROJECT_TASKS.md) for real-time task progress and [LEADPILOT AI.docx](./LEADPILOT%20AI.docx) for the official project specification.

