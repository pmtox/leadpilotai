# LeadPilot AI

LeadPilot AI is a multilingual sales-assistance app for e-commerce website projects. It helps teams talk with prospective customers, capture their requirements, qualify leads, and prepare follow-ups.

## What it does

- Supports text and voice conversations in English, Hindi, Telugu, and Tamil.
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

## Deploy (Netlify + Render + Supabase)

The included `netlify.toml` builds the React app and proxies `/api/*` and `/health` to the Render API. This keeps OAuth session cookies on the Netlify site origin; leave `VITE_API_BASE_URL` unset in Netlify. The Render Blueprint in `render.yaml` creates the Python API service.

1. **Create a Supabase project.** In **Connect**, copy the PostgreSQL URI for the **Session pooler** and set it as `DATABASE_URL` on Render. Keep the password encoded as provided, and include `?sslmode=require` if the URI does not already specify SSL. The backend creates its tables and applies the small existing-column migration on startup.
2. **Deploy the API on Render.** Push this repository to a Git provider, then create a Blueprint in Render from the repository root. The API service is named `leadpilot-api`; the Netlify proxy is configured for `https://leadpilot-api.onrender.com`. If Render assigns another hostname, update both proxy targets in `netlify.toml` and redeploy the Netlify site.
3. **Deploy the frontend on Netlify.** Import the same repository; Netlify reads the base directory, build command, and publish directory from `netlify.toml`.
4. **Finish Render environment settings** after Netlify shows the site URL:

   ```env
   FRONTEND_URL=https://your-site.netlify.app
   CORS_ORIGINS=https://your-site.netlify.app
   GOOGLE_REDIRECT_URI=https://your-site.netlify.app/api/auth/google/callback
   ADMIN_EMAILS=admin@example.com
   ```

   Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Render as secret environment variables. Set `DATABASE_URL` there as well; never commit production credentials.
5. **Update the Google OAuth web client.** Add the exact `GOOGLE_REDIRECT_URI` above to **Authorized redirect URIs**. Add the Netlify site origin to **Authorized JavaScript origins** if your OAuth client setup requests it. If the OAuth consent screen is in testing mode, add administrator/customer accounts as test users.
6. **Enable AI and email services as needed.** Add the Gemini or Groq key to Render for provider-generated responses; add Groq to enable voice transcription. Configure the SMTP variables there to deliver email summaries. Without those provider credentials, rule-based text responses continue to work and emails remain drafts.

Check `https://your-site.netlify.app/health` after both deploys; it should report `postgresql_connected`. The Render free web service can spin down when idle, so its first request may be delayed. Supabase free-tier projects may pause when inactive; review provider limits before relying on them for production.

This connects the deployed application to a fresh Supabase database; it does **not** copy existing records from local `leadpilot.db`. Keep that file private and request a separate data migration if you need to preserve its records.

## Configuration

AI replies are limited to 2 provider requests per conversation and 100 requests per day per running backend process by default. Configure `LLM_MAX_CALLS_PER_CONVERSATION` and `LLM_MAX_CALLS_PER_DAY` in `backend/.env`. Rule-based lead extraction is enabled by default; optional model-based extraction can be enabled with `LLM_EXTRACTION_ENABLED=true`. These process-local limits reset when the backend restarts; use provider-side quotas for hard spending limits.

When a signed-in customer finishes a conversation, LeadPilot creates a call-summary email action addressed to their verified Google account email. If SMTP is missing or delivery fails, the email stays visible in the admin Action Center for review or retry. Configure the sender in `backend/.env`; for Gmail, use a Google App Password:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your-sending-address@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM_EMAIL=your-sending-address@gmail.com
```

## Google sign-in and roles

Create a Google OAuth web client and add this authorized redirect URI for local development:

```text
http://localhost:8000/api/auth/google/callback
```

Set the following values in `backend/.env` (keep the client secret private):

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
AUTH_SESSION_SECRET=generate-a-long-random-secret
ADMIN_EMAILS=admin@example.com
```

Generate a session secret with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Add administrator Google account emails to the comma-separated `ADMIN_EMAILS` allowlist; other verified Google accounts are regular users. In production, use HTTPS and set `APP_ENV=production`, a persistent `AUTH_SESSION_SECRET`, and the production frontend origin and OAuth callback URL.

Gemini calls use the configured `GEMINI_MODEL` (default `gemini-3.8-flash`), send the API key in an HTTP header, and allow up to 30 seconds for a response. Check backend logs for the Google API status and error message if the provider rejects a request. Keep real API keys, passwords, customer data, and local environment files out of source control.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```
