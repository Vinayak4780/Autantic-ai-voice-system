# VoiceStyle — AI That Writes Like *You*

A system that learns a user's writing voice from samples and rewrites any generic or AI-generated text to match their personal style.

**No tone sliders. No presets. Just your voice.**

---

## How It Works

### Architecture

```
┌─────────────────────┐     ┌──────────────────────────┐
│   Frontend (3000)   │────▶│   Backend API (8000)     │
│  HTML/CSS/JS        │◀────│   Python FastAPI          │
└─────────────────────┘     └──────────┬───────────────┘
                                       │
                            ┌──────────▼───────────────┐
                            │  Style Analysis Pipeline  │
                            │  (Programmatic — No LLM)  │
                            └──────────┬───────────────┘
                                       │
                            ┌──────────▼───────────────┐
                            │  Rewriting Engine         │
                            │  (Gemini + Style Profile) │
                            └──────────────────────────┘
```

### Pipeline Steps

1. **Onboarding** — User submits 5-7 writing samples
2. **Style Analysis** (Programmatic, deterministic) — Extracts quantitative metrics and qualitative signals
3. **Profile Storage** — Style profile saved as JSON on disk
4. **Rewriting** — Draft text + style profile → structured prompt → LLM → rewritten text

### Style Signals Captured

| Signal Category | What We Detect | How |
|---|---|---|
| **Sentence Structure** | Avg length, short/long ratios, std deviation | Regex-based sentence splitting + word counting |
| **Questions & Hooks** | Rhetorical question frequency, exclamation usage | Punctuation analysis per sentence |
| **Formatting** | Paragraph length, bullet point usage, line structure | Pattern matching on line breaks and markers |
| **Vocabulary** | Type-token ratio, word length, contractions, signature phrases | N-gram extraction, frequency counting vs. stop words |
| **Punctuation & Emoji** | Emoji frequency, ellipsis, dash, parenthetical usage | Regex pattern matching |
| **Rhythm** | Sentence length variation, paragraph opening patterns | Coefficient of variation, first-sentence analysis |

**Key design decision:** Style analysis is 100% programmatic — no LLM is used at this stage. This makes it deterministic, repeatable, and fast. The same samples always produce the same profile.

### Rewriting Engine

The LLM prompt is **not** "rewrite this in a casual tone." Instead, it includes:

- **Concrete numeric targets**: "Target avg sentence length: ~11 words"
- **User's actual phrases**: "Signature phrases to use: 'here's the truth', 'that's it'"
- **Vocabulary directives**: "Preferred words: customers, ship, product, build"
- **Formatting rules**: "Use short paragraphs (2-3 sentences). No bullet points."
- **Reference excerpts**: Direct quotes from the user's samples for voice matching

This structured approach ensures **repeatability** — the same profile + same draft → consistent output style.

---

## Setup & Running

### Prerequisites

- Python 3.10+
- A free Google Gemini API key

### 1. Get a Free Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### 2. Install Backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure API Key

Edit `backend/.env` and replace the placeholder:

```
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Start the Backend (Port 8000)

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 5. Start the Frontend (Port 3000)

In a **separate terminal**:

```bash
cd frontend
python serve_frontend.py
```

Open `http://localhost:3000` in your browser.

---

## Deployment

### Backend (Render)

The backend is deployed at: `https://autantic-ai-voice-system.onrender.com`

To deploy your own:

1. Create a [Render](https://render.com) account (free tier available)
2. Create a new **Web Service** from your GitHub repository
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your Gemini API key
5. Deploy! Your API will be live at `https://your-app-name.onrender.com`

### Frontend (Vercel)

The frontend can be deployed to Vercel for free:

1. Go to [Vercel](https://vercel.com) and sign in with GitHub
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure deployment settings:
   - **Framework Preset**: `Other`
   - **Root Directory**: `frontend`
   - **Build Command**: Leave empty or use `echo 'Static files'`
   - **Output Directory**: `.` (current directory)
   - **Install Command**: Leave empty
5. The frontend will auto-discover `index.html`
6. Click **Deploy**

**Important**: The frontend in this repository is already configured to use the Render backend at `https://autantic-ai-voice-system.onrender.com`. If you deployed your own backend, update the `API_BASE` constant in `frontend/app.js`:

```javascript
const API_BASE = "https://your-backend-url.onrender.com";
```

### Environment Variables (Vercel - Optional)

While not required for this static frontend, you can add the `GEMINI_API_KEY` as an environment variable in Vercel settings if needed for future enhancements.

### Local Development Without Python

If you prefer not to use Python for local frontend development:

```bash
# Using npx (Node.js)
cd frontend
npx serve -p 3000

# Or using Python's built-in server
python -m http.server 3000
```

---

## Usage

### Step 1: Create a Voice Profile

1. Go to the **Onboard** tab
2. Enter a profile name (e.g., "My LinkedIn Voice")
3. Paste 5-7 writing samples in the text areas
4. Click **Analyze My Style**
5. Review your style metrics and signature phrases

### Step 2: Rewrite Text

1. Go to the **Rewrite** tab
2. Select your voice profile from the dropdown
3. Paste any generic or AI-generated text
4. Click **Rewrite in My Voice**
5. Compare the original and rewritten versions side by side

---

## Example

### Input: Writing Samples (Tech Founder Voice)

> "Stop building features nobody asked for. I see it every single week. Founders come to me with a product that has 47 features and zero paying customers..."

> "I spent 3 years building the wrong thing. Not because I was lazy — because I was scared..."

*(See `examples/sample_io.json` for all 7 samples)*

### Style Profile Generated

| Metric | Value |
|---|---|
| Avg Sentence Length | ~11 words |
| Short Sentence Ratio | 35% |
| Question Ratio | 12% |
| Vocabulary Richness | 52% |
| Contraction Usage | 5.2% |
| Sentence Variation | High |

**Signature Phrases:** "here's the truth", "that's it", "don't be", "the whole game"  
**Vocabulary:** customers, product, build, ship, features, revenue

### Input: Generic Draft

> "Artificial intelligence is transforming the way businesses operate in today's digital landscape. Companies across various industries are leveraging AI technologies to improve efficiency..."

### Output: Rewritten in User's Voice

> "Everyone's talking about AI. But here's what nobody tells you: most companies are doing it wrong.
>
> They buy the tools. They hire the consultants. They build the dashboards. And nothing changes. Why? Because they're chasing technology instead of solving problems.
>
> Here's the truth: AI doesn't care about your digital transformation roadmap. Your customers don't either.
>
> Pick ONE process that's broken. Use AI to fix it. Measure the result. That's it."

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/onboard` | Submit writing samples, create style profile |
| POST | `/api/rewrite` | Rewrite draft text in a user's voice |
| GET | `/api/profiles` | List all saved profiles |
| GET | `/api/profiles/{id}` | Get a specific profile with all metrics |
| DELETE | `/api/profiles/{id}` | Delete a profile |

Full interactive docs available at `http://localhost:8000/docs` when the backend is running.

---

## Project Structure

```
Autantic-ai-voice-system/
├── backend/
│   ├── main.py              # FastAPI app + endpoints
│   ├── style_analyzer.py    # Programmatic style extraction (no LLM)
│   ├── rewriter.py          # LLM-based rewriting with structured prompts
│   ├── models.py            # Pydantic data models
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # API key (git-ignored)
│   └── .env.example         # Template for API key
├── frontend/
│   ├── index.html           # Main UI
│   ├── style.css            # Dark theme styling
│   ├── app.js               # Frontend logic
│   └── serve_frontend.py    # Simple HTTP server (port 3000)
├── examples/
│   └── sample_io.json       # Example inputs and expected outputs
├── .gitignore
└── README.md
```

---

## Technical Decisions

1. **Programmatic style analysis over LLM-based extraction**: Deterministic, fast, repeatable. No token cost for analysis.

2. **Google Gemini (free tier)**: Generous free API with `gemini-2.0-flash` model. No credit card required.

3. **Structured prompts with concrete metrics**: Instead of "write casually," the prompt says "target 11 words/sentence, 35% short sentences, use these specific phrases." This makes results consistent and auditable.

4. **File-based persistence**: Simple JSON files on disk. No database required. Easy to inspect and debug.

5. **Separate frontend/backend**: Frontend on port 3000, backend on port 8000. Clean separation of concerns with CORS enabled.

6. **Vanilla JS frontend**: No build step, no npm install, no framework overhead. Just open and run.

---

## Pricing Context

This product would be priced at:
- **$29/month** (monthly)
- **$24/month** (annual billing)

Billing is not implemented — this is a technical reference.
