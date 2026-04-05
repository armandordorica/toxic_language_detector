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

- macOS with [Homebrew](https://brew.sh) installed
- Your app runs locally (any language/framework)
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

## Step 2 — Build and Run Your App Locally

For a **FastAPI / Python** app (like this one):

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For other stacks:
```bash
# Node.js / Express
node index.js                        # default port 3000

# Next.js
npm run build && npm start           # default port 3000

# Flask
flask run --host=127.0.0.1 --port=5000

# Rails
rails server -b 127.0.0.1 -p 3000
```

Confirm the app works locally:
```bash
curl http://localhost:8000/health
```

---

## Step 3 — Open a Quick Tunnel (No Account Needed)

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

## Step 4 — Keep Your Mac Awake

The tunnel dies if your Mac sleeps. Prevent sleep for the session:

```bash
# Keep awake until you press Ctrl+C
caffeinate -d
```

Or permanently via System Settings:
> System Settings → Displays → Uncheck "Prevent automatic sleeping when display is off"
> System Settings → Lock Screen → Set "Turn display off" to Never

---

## Step 5 — Get a Stable URL (Free Cloudflare Account)

The quick tunnel URL changes on every restart. For a permanent URL:

### 5a. Create a free Cloudflare account

Go to [cloudflare.com](https://cloudflare.com) and sign up. No credit card required.

### 5b. Log in via CLI

```bash
cloudflared tunnel login
```

This opens a browser window. Authorize cloudflared on your account.

### 5c. Create a named tunnel

```bash
cloudflared tunnel create my-app
```

This creates a tunnel and saves credentials to `~/.cloudflare/`.

### 5d. Create a config file

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

### 5e. Route a hostname to the tunnel

If you own a domain on Cloudflare:
```bash
cloudflared tunnel route dns my-app myapp.yourdomain.com
```

If you don't have a domain, Cloudflare offers free `*.pages.dev` subdomains — or use the quick tunnel URL for proof-of-concept.

### 5f. Run the named tunnel

```bash
cloudflared tunnel run my-app
```

Your app is now at `https://myapp.yourdomain.com` every time.

---

## Step 6 — Run Everything with One Command (Optional)

Create a shell script `start.sh` in your project root:

```bash
#!/bin/bash
set -e

echo "Starting app..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
APP_PID=$!

echo "Opening tunnel..."
cloudflared tunnel --url http://localhost:8000 &
TUNNEL_PID=$!

# Shut both down on Ctrl+C
trap "kill $APP_PID $TUNNEL_PID" EXIT
wait
```

Make it executable and run:
```bash
chmod +x start.sh
./start.sh
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
| Render / Railway / Fly.io | $7–25/month |

---

## Limitations vs. a Cloud Service

- **Your Mac must be on** — if it sleeps or loses power, the app goes down.
- **Home internet upload speed** — typically 10–50 Mbps, fine for personal/demo use.
- **Dynamic home IP** — not an issue since cloudflared handles routing, but be aware.
- **No auto-scaling** — one instance, one machine.

For production apps with real users, a cloud service is worth the cost. For personal projects, demos, and proof-of-concepts, self-hosting like this is completely viable.
