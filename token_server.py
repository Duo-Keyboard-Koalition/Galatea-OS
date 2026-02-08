"""
LiveKit token server for frontend connection.

Run with: uvicorn token_server:app --reload --port 8765

Dev mode (create credentials.json and serve it):
  CREATE_CREDENTIALS_FILE=1 uvicorn token_server:app --port 8765

The frontend calls GET /api/token?room=ROOM&identity=USER to get a JWT, or
GET /api/credentials in dev to use the pre-written credentials file.
Uses LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET from .env.
"""
import json
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from livekit.api.access_token import AccessToken, VideoGrants

load_dotenv()

# Path for dev credentials file (same dir as this script)
CREDENTIALS_FILE = Path(__file__).resolve().parent / "credentials.json"

app = FastAPI(
    title="LiveKit Token API",
    description="Issue LiveKit access tokens for the voice agent frontend.",
)

# Allow frontend (different origin) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend origin in production, e.g. ["https://your-app.netlify.app"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    room: str = "voice-room"
    identity: str = "user"
    name: str | None = None


class TokenResponse(BaseModel):
    token: str
    url: str


def _get_livekit_url() -> str:
    url = os.getenv("LIVEKIT_URL", "").strip()
    if not url:
        raise ValueError("LIVEKIT_URL is not set in environment")
    # Ensure wss:// for frontend
    if url.startswith("https://"):
        url = "wss://" + url.removeprefix("https://")
    elif not url.startswith("wss://"):
        url = "wss://" + url
    return url


def _ensure_credentials_file() -> None:
    """Create credentials.json when CREATE_CREDENTIALS_FILE=1 (dev mode)."""
    if os.getenv("CREATE_CREDENTIALS_FILE", "").strip().lower() not in ("1", "true", "yes"):
        return
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        return
    try:
        livekit_url = _get_livekit_url()
    except ValueError:
        return
    token = (
        AccessToken(api_key=api_key, api_secret=api_secret)
        .with_identity("user")
        .with_grants(VideoGrants(room_join=True, room="voice-room"))
        .with_ttl(timedelta(hours=1))
    )
    payload = {"token": token.to_jwt(), "url": livekit_url}
    CREDENTIALS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@app.on_event("startup")
def _on_startup() -> None:
    _ensure_credentials_file()


@app.get("/api/credentials", response_model=TokenResponse)
def get_credentials():
    """Serve pre-written credentials from credentials.json (dev). Frontend uses this when available."""
    if not CREDENTIALS_FILE.exists():
        raise HTTPException(status_code=404, detail="credentials.json not found (run with CREATE_CREDENTIALS_FILE=1)")
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Invalid credentials file: {e}") from e
    if "token" not in data or "url" not in data:
        raise HTTPException(status_code=500, detail="credentials.json must contain 'token' and 'url'")
    return TokenResponse(token=data["token"], url=data["url"])


@app.get("/api/token", response_model=TokenResponse)
@app.post("/api/token", response_model=TokenResponse)
def get_token(
    room: str = "voice-room",
    identity: str = "user",
    name: str | None = None,
):
    """Issue a LiveKit access token so the frontend can join a room."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit API key/secret not configured (LIVEKIT_API_KEY, LIVEKIT_API_SECRET)",
        )
    try:
        livekit_url = _get_livekit_url()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    token = (
        AccessToken(api_key=api_key, api_secret=api_secret)
        .with_identity(identity)
        .with_grants(VideoGrants(room_join=True, room=room))
        .with_ttl(timedelta(hours=1))
    )
    if name:
        token = token.with_name(name)
    jwt_token = token.to_jwt()

    return TokenResponse(token=jwt_token, url=livekit_url)


@app.post("/api/token/body", response_model=TokenResponse)
def get_token_body(body: TokenRequest):
    """Issue a token from JSON body (room, identity, name)."""
    return get_token(room=body.room, identity=body.identity, name=body.name)


@app.get("/api/health")
def health():
    """Health check; confirms LIVEKIT_URL is set."""
    try:
        url = _get_livekit_url()
        return {"ok": True, "livekit_url_set": bool(url)}
    except ValueError:
        return {"ok": True, "livekit_url_set": False}
