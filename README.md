# CAS Flask Demo (Render-ready)

A tiny Flask app showing CAS login via [`flask-cas-ng`](https://github.com/MasterRoshan/flask-cas-ng).
It pairs perfectly with a lightweight CAS proxy such as **quick-cas** (your Shibboleth-gated CAS shim).

## What it does

- Redirects `GET /` to CAS login (via the extension).
- On success, shows **username** and **attributes** returned by CAS 2.0 (`<cas:attribute>`).
- Includes `/healthz` for container health checks.

## Files

- `app.py` – minimal Flask app using `flask-cas-ng`.
- `requirements.txt` – Flask, flask-cas-ng, gunicorn.
- `Dockerfile` – runs `gunicorn` on `$PORT` (Render-compatible).
- `render.yaml` – **Render Blueprint** for one-click deploy.
- `.dockerignore` – keeps images small.

## One‑click deploy to Render

1. Push this repo to GitHub.
2. In Render, **New → Blueprint** and point at this repo.
3. When prompted, set:
   - `CAS_SERVER` → your CAS proxy base URL (e.g. `https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas`)
   - `CAS_LOGIN_ROUTE` → `/index.php/login` (already default)
   - `CAS_VALIDATE_ROUTE` → `/serviceValidate.php` (already default)
   - `SECRET_KEY` → generated automatically by the Blueprint
4. Deploy. Visit the Render URL → you’ll be redirected to CAS → on return you should see your username and attributes.

> **Important:** In your **quick-cas** config, allow‑list your Render domain (e.g. `https://<app>.onrender.com/`)
> so tickets are accepted by the proxy.

## Local dev (optional)

CAS servers usually require a **public HTTPS** callback. Use ngrok (or similar) if testing locally.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export CAS_SERVER="https://<your-cas-base>"
export CAS_LOGIN_ROUTE="/index.php/login"
export CAS_VALIDATE_ROUTE="/serviceValidate.php"
export SECRET_KEY="dev-please-change"
python app.py
```

Then expose with ngrok:

```bash
ngrok http 5000
```

Visit the ngrok URL → you’ll be redirected to CAS and back.

## Minimal app code (the essence ✨)

```python
from flask import Flask, render_template_string
from flask_cas import CAS, login_required

app = Flask(__name__); app.secret_key = "…"
app.config.update(CAS_SERVER="…", CAS_LOGIN_ROUTE="/index.php/login",
                  CAS_VALIDATE_ROUTE="/serviceValidate.php", CAS_AFTER_LOGIN="home")
cas = CAS(app, "/cas")

@app.get("/")
@login_required
def home():
    return render_template_string("{{u}}<pre>{{a}}</pre>",
                                  u=cas.username, a=cas.attributes)
```
