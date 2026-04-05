from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from detoxify import Detoxify
import os

app = FastAPI(title="Toxic Language Detector")

# ── Lazy model loader ──────────────────────────────────────────────────────────
# Model is loaded on first /analyze request, not at startup.
# This lets Render bind the port before the heavy model download begins.
_model: Detoxify | None = None

def get_model() -> Detoxify:
    global _model
    if _model is None:
        print("Loading model…")
        # "original" = unitary/toxic-bert  (~250 MB RAM, fits in 512 MB free tier)
        _model = Detoxify("original")
        print("✅ Model ready.")
    return _model

# ── Templates ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
templates  = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

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
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/analyze")
async def analyze(body: TextRequest):
    if not body.text.strip():
        return {"error": "Please enter some text."}

    raw = get_model().predict(body.text)
    # raw is dict[label, float] for a single string
    scores = {k: round(float(v), 4) for k, v in raw.items()}

    top_label = max(scores, key=scores.get)
    top_score = scores[top_label]
    alert     = get_alert(top_score)

    return {
        "scores":    scores,
        "top_label": top_label,
        "top_score": top_score,
        "alert":     alert,
    }
