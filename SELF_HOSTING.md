# Self-Hosting a Web App with Cloudflare Tunnel

Host any web app on your own computer and access it from anywhere — no paid cloud services required.

---

## How It Works

```
Your Phone
    │
    │  HTTPS request
    ▼
Cloudflare's Edge (public internet)
    │
    │  Encrypted tunnel
    ▼
cloudflared (running on your Mac)
    │
    │  localhost
    ▼
Your App (e.g. uvicorn on port 8000)
```

Cloudflare acts as the public-facing proxy. Your Mac never needs a public IP or open ports — the tunnel is outbound-only.

---

## Prerequisites

- macOS with [Homebrew](https://brew.sh) installed (or a GL.iNet Flint 3 — see [Hosting on the Flint 3](#hosting-on-the-flint-3-always-on-no-mac-needed))
- A free HuggingFace account and API token — [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- Mac stays awake while you need access (System Settings → Displays → Prevent display from sleeping, or use `caffeinate`)

---

## Step 1 — Install cloudflared

```bash
brew install cloudflare/cloudflare/cloudflared
```

Verify:
```bash
cloudflared --version
```

---

## Step 2 — Set Your HuggingFace Token

The app calls the HuggingFace Inference API instead of loading the model locally. You need a free token.

1. Sign up at [huggingface.co](https://huggingface.co) (free)
2. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → **New token** → Read access
3. Copy the token, then in the project root:

```bash
cp .env.example .env
# Edit .env and paste your token:
# HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 3 — Build and Run Your App Locally

```bash
# Install dependencies (fast — no torch/transformers)
pip install -r requirements.txt

# Start app + tunnel in one command
./start.sh
```

Or manually in two tabs:
```bash
# Tab 1
HF_API_TOKEN=hf_xxx uvicorn app.main:app --host 127.0.0.1 --port 8000

# Tab 2
cloudflared tunnel --url http://localhost:8000
```

Confirm the app works:
```bash
curl http://localhost:8000/health
```

---

## Step 4 — Open a Quick Tunnel (No Account Needed)

In a **new terminal tab**, run:

```bash
cloudflared tunnel --url http://localhost:8000
```

After a few seconds you'll see:

```
Your quick Tunnel has been created! Visit it at:
https://some-random-words.trycloudflare.com
```

That URL is now publicly accessible from any device. Share it or open it on your phone.

> **Note:** The URL is random and changes every time you restart the tunnel. See Step 5 for a stable URL.

---

## Step 5 — Keep Your Mac Awake

The tunnel dies if your Mac sleeps. Prevent sleep for the session:

```bash
# Keep awake until you press Ctrl+C
caffeinate -d
```

Or permanently via System Settings:
> System Settings → Displays → Uncheck "Prevent automatic sleeping when display is off"
> System Settings → Lock Screen → Set "Turn display off" to Never

---

## Step 6 — Get a Stable URL (Free Cloudflare Account)

The quick tunnel URL changes on every restart. For a permanent URL:

### 6a. Create a free Cloudflare account

Go to [cloudflare.com](https://cloudflare.com) and sign up. No credit card required.

### 6b. Log in via CLI

```bash
cloudflared tunnel login
```

This opens a browser window. Authorize cloudflared on your account.

### 6c. Create a named tunnel

```bash
cloudflared tunnel create my-app
```

This creates a tunnel and saves credentials to `~/.cloudflare/`.

### 6d. Create a config file

```bash
mkdir -p ~/.cloudflared
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: my-app
credentials-file: /Users/YOUR_USERNAME/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: myapp.yourdomain.com   # or use a pages.dev subdomain
    service: http://localhost:8000
  - service: http_status:404
```

### 6e. Route a hostname to the tunnel

If you own a domain on Cloudflare:
```bash
cloudflared tunnel route dns my-app myapp.yourdomain.com
```

If you don't have a domain, Cloudflare offers free `*.pages.dev` subdomains — or use the quick tunnel URL for proof-of-concept.

### 6f. Run the named tunnel

```bash
cloudflared tunnel run my-app
```

Your app is now at `https://myapp.yourdomain.com` every time.

---

## Step 7 — Run Everything with One Command (Optional)

This repo includes a `start.sh` that launches the app and tunnel together:

```bash
./start.sh
```

It starts `uvicorn` on port 8000, opens the Cloudflare tunnel, and shuts both down cleanly on `Ctrl+C`. You can override the port:

```bash
PORT=9000 ./start.sh
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Tunnel URL times out | App not running on expected port | Confirm with `curl http://localhost:8000` |
| `cloudflared: command not found` | Not installed | `brew install cloudflare/cloudflare/cloudflared` |
| URL works but app crashes on first use | Not enough RAM for model load | Check app logs; consider lazy loading |
| Tunnel disconnects randomly | Mac went to sleep | Use `caffeinate -d` |
| `bind: address already in use` | Port 8000 taken | Change port or kill the existing process: `lsof -ti:8000 \| xargs kill` |

---

## Cost

| Service | Cost |
|---|---|
| cloudflared (quick tunnel) | Free, no account |
| cloudflared (named tunnel) | Free, Cloudflare account required |
| Your electricity | ~$0.01–0.05/day for a MacBook |

---

## Limitations vs. a Cloud Service

- **Your Mac must be on** — if it sleeps or loses power, the app goes down.
- **Home internet upload speed** — typically 10–50 Mbps, fine for personal/demo use.
- **Dynamic home IP** — not an issue since cloudflared handles routing, but be aware.
- **No auto-scaling** — one instance, one machine.

For production apps with real users, a cloud service is worth the cost. For personal projects, demos, and proof-of-concepts, self-hosting like this is completely viable.

---

## Hosting on the Flint 3 (Always On, No Mac Needed)

The GL.iNet Flint 3 runs 24/7 and is powerful enough to host this app (the model runs on HuggingFace, so the router only needs to serve the FastAPI frontend — very lightweight).

### What the Flint 3 handles
- Running the FastAPI app (Python, ~30 MB RAM)
- Running the Cloudflare Tunnel (cloudflared, ~20 MB RAM)

### What HuggingFace handles
- All ML inference (no model weights on the router)

---

### Step 1 — SSH into the Flint 3

```bash
ssh root@192.168.8.1
```

Default password is on the router label. Change it on first login if you haven't.

---

### Step 2 — Install Python and dependencies

```bash
opkg update
opkg install python3 python3-pip
pip3 install fastapi uvicorn jinja2 pydantic requests
```

> If `opkg` can't find `python3-pip`, install it manually:
> ```bash
> opkg install python3-pip || curl https://bootstrap.pypa.io/get-pip.py | python3
> ```

---

### Step 3 — Copy the app to the router

From your Mac (not the router SSH session):

```bash
scp -r app/ root@192.168.8.1:/root/toxic_detector/
```

---

### Step 4 — Install cloudflared on the Flint 3

GL.iNet routers support cloudflared via their admin panel:

1. Open **http://192.168.8.1** in your browser
2. Go to **Applications → Plug-ins**
3. Search for **cloudflared** and install it
4. Go to **Applications → Cloudflare Tunnel**
5. Paste your tunnel token (from the Cloudflare dashboard) and enable it

If the plugin isn't available, install manually via SSH:

```bash
# Download the ARM64 binary
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 \
  -o /usr/bin/cloudflared
chmod +x /usr/bin/cloudflared
```

---

### Step 5 — Set the HuggingFace token

```bash
echo "export HF_API_TOKEN=hf_xxxxxxxxxxxxxxxx" >> /etc/profile
source /etc/profile
```

---

### Step 6 — Start the app

```bash
cd /root/toxic_detector
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
```

And start the tunnel (if using the CLI instead of the admin plugin):

```bash
cloudflared tunnel --url http://localhost:8000
```

---

### Step 7 — Auto-start on router reboot

Create `/etc/init.d/toxic_detector`:

```bash
cat > /etc/init.d/toxic_detector << 'EOF'
#!/bin/sh /etc/rc.common
START=99
STOP=10

start() {
    export HF_API_TOKEN=hf_xxxxxxxxxxxxxxxx
    cd /root/toxic_detector
    uvicorn app.main:app --host 127.0.0.1 --port 8000 &
}

stop() {
    kill $(pgrep -f "uvicorn app.main") 2>/dev/null
}
EOF

chmod +x /etc/init.d/toxic_detector
/etc/init.d/toxic_detector enable
```

The app now starts automatically whenever the router boots.
