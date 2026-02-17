"""
VoiceStyle API — FastAPI Backend

Main entry point for the VoiceStyle API server.
Runs on port 8000.

Endpoints:
    POST /api/onboard      — Submit writing samples, create style profile
    POST /api/rewrite      — Rewrite draft text in a user's voice
    GET  /api/profiles     — List all style profiles
    GET  /api/profiles/{id} — Get a specific profile
    DELETE /api/profiles/{id} — Delete a profile
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    OnboardRequest,
    RewriteRequest,
    StyleProfile,
    StyleMetrics,
    RewriteResponse,
    ProfileListItem,
)
from style_analyzer import StyleAnalyzer
from rewriter import rewrite_text


# ── Data persistence (file-based for simplicity) ──────────────────────────

DATA_DIR = Path(__file__).parent / "data"
PROFILES_DIR = DATA_DIR / "profiles"


def ensure_dirs():
    """Create data directories if they don't exist."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def save_profile(profile_id: str, profile_data: dict, samples: list[str]):
    """Persist a style profile and original samples to disk."""
    ensure_dirs()
    filepath = PROFILES_DIR / f"{profile_id}.json"
    data = {
        "profile": profile_data,
        "samples": samples,
    }
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_profile(profile_id: str) -> dict | None:
    """Load a style profile from disk."""
    filepath = PROFILES_DIR / f"{profile_id}.json"
    if filepath.exists():
        return json.loads(filepath.read_text(encoding="utf-8"))
    return None


def list_profiles() -> list[dict]:
    """List all saved profiles."""
    ensure_dirs()
    profiles = []
    for filepath in PROFILES_DIR.glob("*.json"):
        data = json.loads(filepath.read_text(encoding="utf-8"))
        profiles.append(data["profile"])
    return profiles


def delete_profile(profile_id: str) -> bool:
    """Delete a profile from disk."""
    filepath = PROFILES_DIR / f"{profile_id}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False


# ── App setup ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup and teardown."""
    ensure_dirs()
    print("✓ VoiceStyle API is ready")
    print(f"  Data directory: {DATA_DIR.absolute()}")
    yield


app = FastAPI(
    title="VoiceStyle API",
    description="Learn a user's writing voice and rewrite text to match it.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend on different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "service": "VoiceStyle API", "version": "1.0.0"}


@app.post("/api/onboard", response_model=StyleProfile)
async def onboard_user(request: OnboardRequest):
    """
    Onboard a new user by analyzing their writing samples.
    
    Accepts 3-10 writing samples and produces a complete style profile
    through programmatic analysis (no LLM used at this stage).
    """
    # Extract texts from samples
    sample_texts = [s.text for s in request.samples]
    
    # Run the style analyzer
    analyzer = StyleAnalyzer(sample_texts)
    analysis = analyzer.analyze()
    
    # Create profile
    profile_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat() + "Z"
    
    profile_data = {
        "id": profile_id,
        "user_name": request.user_name,
        "created_at": now,
        "metrics": analysis["metrics"],
        "signature_phrases": analysis["signature_phrases"],
        "vocabulary_preferences": analysis["vocabulary_preferences"],
        "sentence_starters": analysis["sentence_starters"],
        "transition_words": analysis["transition_words"],
        "formatting_style": analysis["formatting_style"],
        "sample_excerpts": analysis["sample_excerpts"],
        "raw_style_summary": analysis["raw_style_summary"],
    }
    
    # Save to disk
    save_profile(profile_id, profile_data, sample_texts)
    
    return StyleProfile(**profile_data)


@app.post("/api/rewrite", response_model=RewriteResponse)
async def rewrite_draft(request: RewriteRequest):
    """
    Rewrite draft text to match a user's writing voice.
    
    Uses the style profile (from onboarding) to construct a detailed,
    data-driven prompt for the LLM. The prompt includes concrete metrics,
    vocabulary preferences, and example excerpts — not vague instructions.
    """
    # Load the profile
    data = load_profile(request.profile_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Profile '{request.profile_id}' not found")
    
    profile = data["profile"]
    
    # Rewrite using the LLM with structured prompt
    result = await rewrite_text(profile, request.draft_text)
    
    return RewriteResponse(
        original_text=request.draft_text,
        rewritten_text=result["rewritten_text"],
        profile_id=request.profile_id,
        style_notes=result["style_notes"],
    )


@app.get("/api/profiles", response_model=list[ProfileListItem])
async def get_profiles():
    """List all saved style profiles."""
    profiles = list_profiles()
    items = []
    for p in profiles:
        # Count samples from saved data
        data = load_profile(p["id"])
        sample_count = len(data["samples"]) if data else 0
        items.append(ProfileListItem(
            id=p["id"],
            user_name=p["user_name"],
            created_at=p["created_at"],
            sample_count=sample_count,
        ))
    return items


@app.get("/api/profiles/{profile_id}", response_model=StyleProfile)
async def get_profile(profile_id: str):
    """Get a specific style profile with all metrics."""
    data = load_profile(profile_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
    return StyleProfile(**data["profile"])


@app.delete("/api/profiles/{profile_id}")
async def remove_profile(profile_id: str):
    """Delete a style profile."""
    if delete_profile(profile_id):
        return {"status": "deleted", "id": profile_id}
    raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
