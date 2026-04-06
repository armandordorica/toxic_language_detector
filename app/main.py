from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os

app = FastAPI(title="Toxic Language Detector")

# ── Config ─────────────────────────────────────────────────────────────────────
INFERENCE_BACKEND = os.environ.get("INFERENCE_BACKEND", "huggingface")  # "huggingface" | "local"
HF_API_TOKEN      = os.environ.get("HF_API_TOKEN", "")

HF_API_URLS = {
    "english":      "https://router.huggingface.co/hf-inference/models/unitary/toxic-bert",
    "multilingual": "https://router.huggingface.co/hf-inference/models/unitary/multilingual-toxic-xlm-roberta",
}

LOCAL_MODEL_IDS = {
    "english":      "unitary/toxic-bert",
    "multilingual": "unitary/multilingual-toxic-xlm-roberta",
}

# ── Local model loader (lazy — loaded on first use) ────────────────────────────
_local_pipelines: dict = {}

def get_local_pipeline(model_key: str):
    if model_key not in _local_pipelines:
        try:
            import torch
            from transformers import pipeline as hf_pipeline
        except ImportError:
            raise RuntimeError(
                "torch and transformers are required for local inference. "
                "Run: pip install -r requirements-local.txt"
            )

        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

        model_id = LOCAL_MODEL_IDS[model_key]
        print(f"Loading {model_id} on {device}…")
        _local_pipelines[model_key] = hf_pipeline(
            "text-classification",
            model=model_id,
            device=device,
            top_k=None,   # return all labels, not just top-1
        )
        print(f"✅ {model_key} model ready on {device}.")

    return _local_pipelines[model_key]


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
    text:  str
    model: str = "english"


# ── Inference helpers ──────────────────────────────────────────────────────────
def run_local(text: str, model_key: str) -> dict:
    try:
        pipe = get_local_pipeline(model_key)
    except RuntimeError as e:
        return {"error": str(e)}

    raw    = pipe(text)
    scores = {item["label"]: round(item["score"], 4) for item in raw[0]}
    return scores


def run_huggingface(text: str, model_key: str) -> dict | str:
    """Returns scores dict on success, or an error string on failure."""
    import requests as req

    if not HF_API_TOKEN:
        return "HF_API_TOKEN is not set. See .env.example."

    try:
        response = req.post(
            HF_API_URLS.get(model_key, HF_API_URLS["english"]),
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": text},
            timeout=30,
        )
    except req.exceptions.ConnectionError:
        return "Could not reach HuggingFace API. Check your internet connection."
    except req.exceptions.Timeout:
        return "HuggingFace API timed out. Try again."

    if response.status_code == 503:
        estimated = response.json().get("estimated_time", "unknown")
        return f"Model is loading on HuggingFace (~{estimated}s). Try again shortly."
    if response.status_code == 401:
        return "Invalid HF_API_TOKEN. Check your token at huggingface.co/settings/tokens."
    if not response.ok:
        return f"HuggingFace API error {response.status_code}: {response.text}"

    raw    = response.json()
    scores = {item["label"]: round(item["score"], 4) for item in raw[0]}
    return scores


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "backend": INFERENCE_BACKEND}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"backend": INFERENCE_BACKEND},
    )


@app.post("/analyze")
def analyze(body: TextRequest):
    if not body.text.strip():
        return {"error": "Please enter some text."}

    model_key = body.model if body.model in LOCAL_MODEL_IDS else "english"

    if INFERENCE_BACKEND == "local":
        result = run_local(body.text, model_key)
        if isinstance(result, dict) and "error" in result:
            return result
        scores = result
    else:
        result = run_huggingface(body.text, model_key)
        if isinstance(result, str):
            return {"error": result}
        scores = result

    top_label = max(scores, key=scores.get)
    top_score = scores[top_label]

    return {
        "scores":    scores,
        "top_label": top_label,
        "top_score": top_score,
        "alert":     get_alert(top_score),
        "backend":   INFERENCE_BACKEND,
    }
