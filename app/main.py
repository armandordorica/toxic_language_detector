from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
import os

app = FastAPI(title="Toxic Language Detector")

# ── Config ─────────────────────────────────────────────────────────────────────
HF_API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")

# ── Templates ──────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ── Thresholds ─────────────────────────────────────────────────────────────────
WARNING_THRESHOLD = 0.30
ALERT_THRESHOLD   = 0.70


def get_alert(max_score: float) -> dict:
    if max_score >= ALERT_THRESHOLD:
        return {"level": "HIGH ALERT", "emoji": "🚨", "color": "#e53e3e"}
    elif max_score >= WARNING_THRESHOLD:
        return {"level": "WARNING",    "emoji": "⚠️",  "color": "#dd6b20"}
    else:
        return {"level": "CLEAN",      "emoji": "✅",  "color": "#38a169"}


# ── Request / Response schemas ─────────────────────────────────────────────────
class TextRequest(BaseModel):
    text: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/analyze")
def analyze(body: TextRequest):
    if not body.text.strip():
        return {"error": "Please enter some text."}

    if not HF_API_TOKEN:
        return {"error": "HF_API_TOKEN is not set. See .env.example."}

    try:
        response = requests.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": body.text},
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach HuggingFace API. Check your internet connection."}
    except requests.exceptions.Timeout:
        return {"error": "HuggingFace API timed out. Try again."}

    if response.status_code == 503:
        estimated = response.json().get("estimated_time", "unknown")
        return {"error": f"Model is loading on HuggingFace (~{estimated}s). Try again shortly."}

    if response.status_code == 401:
        return {"error": "Invalid HF_API_TOKEN. Check your token at huggingface.co/settings/tokens."}

    if not response.ok:
        return {"error": f"HuggingFace API error {response.status_code}: {response.text}"}

    # Response: [[{"label": "toxic", "score": 0.95}, ...]]
    raw = response.json()
    scores = {item["label"]: round(item["score"], 4) for item in raw[0]}

    top_label = max(scores, key=scores.get)
    top_score = scores[top_label]
    alert     = get_alert(top_score)

    return {
        "scores":    scores,
        "top_label": top_label,
        "top_score": top_score,
        "alert":     alert,
    }
