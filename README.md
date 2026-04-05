# 🙊 Toxic Language Detector

A production-ready web app that scores any text across **6 toxicity dimensions** and returns a real-time alert level. Built on top of [`unitary/multilingual-toxic-xlm-roberta`](https://huggingface.co/unitary/multilingual-toxic-xlm-roberta) via the [`detoxify`](https://github.com/unitaryai/detoxify) library.

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
│              Detoxify  ·  multilingual model             │
│      unitary/multilingual-toxic-xlm-roberta              │
│      (XLM-RoBERTa fine-tuned on Jigsaw 2020)            │
│                                                         │
│  Output labels:                                         │
│    toxicity · severe_toxicity · obscene                 │
│    threat   · insult          · identity_attack         │
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
| Model       | `unitary/multilingual-toxic-xlm-roberta` (XLM-R) |
| ML library  | `detoxify 0.5`, `torch`, `transformers`          |
| Backend     | `FastAPI` + `Uvicorn`                            |
| Templating  | `Jinja2`                                         |
| Frontend    | Vanilla HTML / CSS / JS (no framework)           |
| Deployment  | Render (free tier) via `render.yaml`             |

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
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** in your browser (works on mobile too — just use your machine's LAN IP, e.g. `http://192.168.x.x:8000`).

---

## ☁️ Deploy to Render (free)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Web Service** → connect your repo.
3. Render auto-detects `render.yaml` and configures everything.
4. Click **Deploy** — you'll get a public URL like `https://toxic-language-detector.onrender.com`.

> ⚠️ Free-tier Render instances spin down after 15 min of inactivity. The first request after a cold start will take ~30–60 s while the model loads.

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
├── Procfile                 # Process declaration (Render / Railway)
├── render.yaml              # Render deployment config
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 📜 License

Apache 2.0 — same as the underlying model.
