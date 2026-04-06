# 🙊 Toxic Language Detector

A web app that scores any text across **6 toxicity dimensions** and returns a real-time alert level. Uses the [`unitary/toxic-bert`](https://huggingface.co/unitary/toxic-bert) model via the HuggingFace Inference API — no local model download required.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Browser / Phone)            │
│                  app/templates/index.html               │
│         Mobile-first UI · Fetch API · Score bars        │
└────────────────────────┬────────────────────────────────┘
                         │  POST /analyze  { "text": "…" }
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI  (app/main.py)                  │
│                                                         │
│  GET  /          → serves index.html (Jinja2)           │
│  POST /analyze   → runs inference, returns JSON scores  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│         HuggingFace Inference API                        │
│         unitary/toxic-bert                               │
│         (BERT fine-tuned on Jigsaw dataset)             │
│                                                         │
│  Output labels:                                         │
│    toxic · severe_toxic · obscene                       │
│    threat · insult      · identity_hate                 │
└─────────────────────────────────────────────────────────┘
```

### Alert thresholds

| Max score across all labels | Alert level  |
|-----------------------------|--------------|
| `< 0.30`                    | ✅ Clean      |
| `0.30 – 0.70`               | ⚠️ Warning   |
| `> 0.70`                    | 🚨 High Alert |

### Tech stack

| Layer       | Technology                                      |
|-------------|--------------------------------------------------|
| Model       | `unitary/toxic-bert` via HuggingFace Inference API |
| ML library  | HuggingFace hosted (no local dependencies)         |
| Backend     | `FastAPI` + `Uvicorn`                            |
| Templating  | `Jinja2`                                         |
| Frontend    | Vanilla HTML / CSS / JS (no framework)           |
| Deployment  | Self-hosted via Cloudflare Tunnel (`start.sh`)   |

---

## 🚀 Run locally

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/toxic_language_detector.git
cd toxic_language_detector
```

### 2. Create & activate a virtual environment

```bash
python3 -m venv toxic_language
source toxic_language/bin/activate      # macOS / Linux
# toxic_language\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **First run only:** the model weights (~1 GB) are downloaded from HuggingFace and cached in `~/.cache/huggingface/`.

### 4. Start the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://localhost:8000** in your browser.

---

## ⚙️ Switching inference backends

The app supports two inference backends, controlled by a single line in your `.env` file.

| Backend | How it works | Best for |
|---|---|---|
| `huggingface` | Calls HuggingFace Inference API | Lightweight setup, no GPU needed |
| `local` | Runs model on your machine (MPS → CUDA → CPU) | Speed, no cold starts, no API dependency |

### Switch to HuggingFace API (default)

```
# .env
INFERENCE_BACKEND=huggingface
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxx
```

### Switch to local inference (Mac GPU / MPS)

```
# .env
INFERENCE_BACKEND=local
```

Install the extra dependencies once:

```bash
pip install -r requirements-local.txt
```

Then restart the app. On the first request you'll see the model loading in the terminal:

```
Loading unitary/toxic-bert on mps…
✅ english model ready on mps.
```

### Verify which backend is running

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "backend": "huggingface"}
# or
{"status": "ok", "backend": "local"}
```

The active backend is also shown in the app's subtitle: **☁️ HuggingFace API** or **🖥 Local (MPS)**.

---

## 🌐 Host publicly from your own machine (free)

Use `start.sh` to launch the app and a Cloudflare Tunnel in one command:

```bash
./start.sh
```

It prints a public `https://*.trycloudflare.com` URL you can open from any device. No account or cloud service needed.

See **[SELF_HOSTING.md](SELF_HOSTING.md)** for the full guide, including how to get a stable URL.

---

## 📓 Exploratory Notebook

`eda.ipynb` contains a full prototype walkthrough:

- Loading the multilingual model
- Scoring a diverse set of sample texts (clean → borderline → toxic)
- Score breakdown with a colour-coded DataFrame
- Interactive single-text tester

Select the **Python (toxic_language)** kernel in VS Code to run it.

---

## 📁 Project structure

```
toxic_language_detector/
├── app/
│   ├── main.py              # FastAPI app (routes + inference logic)
│   └── templates/
│       └── index.html       # Mobile-friendly single-page UI
├── eda.ipynb                # Exploratory / prototype notebook
├── start.sh                 # Launch app + Cloudflare tunnel in one command
├── requirements.txt         # Base dependencies (HuggingFace backend)
├── requirements-local.txt   # Extra deps for local inference (torch, transformers)
├── .env.example             # Environment variable template
├── SELF_HOSTING.md          # Step-by-step self-hosting guide
└── README.md
```

---

## 📜 License

Apache 2.0 — same as the underlying model.
