# 🤖 Gemini ADK Text Summarizer Agent

A single-purpose AI agent built with **Google ADK patterns** and **Gemini 1.5 Flash**.  
Accepts text via HTTP, returns a structured JSON summary — callable from any client.

```
POST /run  →  { "text": "..." }  →  { "summary": "...", "key_points": [...] }
```

---

## 🏗 Architecture

```
HTTP Request
     │
     ▼
 Flask Server  (app.py)
     │
     ▼
SummarizerAgent  (agent.py)         ← ADK-style Agent
     │
     ├── SummarizeTool              ← ADK-style Tool
     │       └── build_prompt()
     │
     ▼
Gemini 1.5 Flash API
     │
     ▼
Structured JSON Response
```

**ADK Concepts used:**
| Concept | Implementation |
|---------|---------------|
| Agent   | `SummarizerAgent` class with `run()` entrypoint |
| Tool    | `SummarizeTool` with `name`, `description`, `build_prompt()` |
| Runner  | `app.py` → `POST /run` calls `agent.run(text)` |
| Model   | `gemini-1.5-flash` (quota-efficient) |

---

## 📁 File Structure

```
gemini-adk-agent/
├── agent.py          # ADK Agent + Tool definition
├── app.py            # Flask HTTP server + embedded UI
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container (Cloud Run compatible)
├── render.yaml       # Render.com deployment config
├── Procfile          # Railway/Heroku compatibility
└── README.md
```

---

## 🚀 Deployment (Free — No Billing Required)

### Option A: Render.com ⭐ (Recommended — easiest free deploy)

1. **Push to GitHub** (see Git section below)

2. Go to **[render.com](https://render.com)** → Sign up free → **New → Web Service**

3. Connect your GitHub repo

4. Render auto-detects `render.yaml`. Set these manually:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 60 app:app`
   - **Runtime:** Python 3

5. Go to **Environment** tab → Add:
   ```
   GEMINI_API_KEY = your_api_key_here
   ```

6. Click **Deploy** → Get your live URL:  
   `https://gemini-adk-agent.onrender.com`

---

### Option B: Railway.app (also free)

1. Go to **[railway.app](https://railway.app)** → New Project → Deploy from GitHub

2. Add environment variable:
   ```
   GEMINI_API_KEY = your_api_key_here
   ```

3. Railway uses the `Procfile` automatically. Deploy → get URL.

---

### Option C: Google Cloud Run (original spec — needs billing but has free tier)

> Cloud Run has a **generous free tier**: 2M requests/month, 360,000 vCPU-seconds/month.  
> A billing account is required but you won't be charged within free tier limits.

```bash
# 1. Install gcloud CLI, login
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build & push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gemini-adk-agent

# 3. Deploy to Cloud Run
gcloud run deploy gemini-adk-agent \
  --image gcr.io/YOUR_PROJECT_ID/gemini-adk-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here \
  --memory 256Mi \
  --port 8080
```

---

## 🛠 Local Development

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/gemini-adk-agent.git
cd gemini-adk-agent

# Install
pip install -r requirements.txt

# Set API key (get free key at aistudio.google.com)
export GEMINI_API_KEY="your_key_here"

# Run
python app.py
# → http://localhost:8080
```

---

## 📡 API Reference

### `POST /run` — Summarize Text

**Request:**
```json
{
  "text": "Artificial intelligence is transforming industries..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "summary": "AI is rapidly changing multiple industries with new capabilities...",
    "key_points": [
      "Machine learning models can now perform complex creative tasks",
      "Major tech companies are competing to build more capable AI systems",
      "Regulatory and economic implications are significant"
    ]
  }
}
```

**cURL example:**
```bash
curl -X POST https://YOUR_APP_URL/run \
  -H "Content-Type: application/json" \
  -d '{"text": "Your article text here..."}'
```

### `GET /health` — Health Check

```json
{ "status": "ok", "agent": "SummarizerAgent", "model": "gemini-1.5-flash" }
```

---

## 📤 Push to GitHub

```bash
cd gemini-adk-agent

git init
git add .
git commit -m "feat: Gemini ADK Summarizer Agent"

# Create repo on github.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/gemini-adk-agent.git
git branch -M main
git push -u origin main
```

---

## 💡 Quota Efficiency Design

This agent is designed to use minimal Gemini API quota:

| Design Choice | Quota Impact |
|--------------|-------------|
| `gemini-1.5-flash` model | Cheapest model, high speed |
| Input capped at 2000 chars | Limits input tokens |
| `max_output_tokens=300` | Limits output tokens |
| `temperature=0.2` | Fewer retries needed |
| Agent instantiated once at startup | No per-request init overhead |

Free tier: **1,500 requests/day** on Gemini 1.5 Flash (as of 2024).

---

## 🔑 Get a Free Gemini API Key

1. Go to **[aistudio.google.com](https://aistudio.google.com)**
2. Sign in with Google
3. Click **Get API Key** → **Create API key**
4. Copy the key — it's free, no billing required

---

## 📝 License

MIT
