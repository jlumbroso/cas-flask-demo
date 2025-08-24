# CAS Flask Demo (CAS v3 via python-cas)

A minimal Flask app that authenticates with a CAS server using **python-cas** (CAS 3.0 / `p3/serviceValidate`).  
Designed to work with your **Quick CAS Proxy** hosted on Penn SEAS (Alliance).

## How it works

- The app sends users to your proxy's **/login**.
- The CAS server redirects back to `/callback?ticket=...`.
- `python-cas` calls **p3/serviceValidate**, parses the XML, and provides the username and attributes.
- The profile page shows both.

## Configuration

Set the CAS root to your proxy’s **index.php** dispatcher (trailing slash required):

```
CAS_SERVER_ROOT=https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/index.php/
```

Environment variables:

- `SECRET_KEY` – Flask session secret (Render blueprint auto-generates one)
- `CAS_SERVER_ROOT` – Base URL of your CAS (proxy) server; **must end with a `/`**.

## Local dev

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY="dev-secret"
export CAS_SERVER_ROOT="https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/index.php/"
python app.py  # http://127.0.0.1:5000/
```

If you test with ngrok, **open the ngrok HTTPS URL** in your browser so the callback service URL matches what the CAS server will redirect back to.

## Deploy to Render (Blueprint)

1. Push these files to a Git repo.
2. In Render: **New → Blueprint** and select your repo.
3. Render uses `render.yaml` to build and start the service.
4. Ensure `CAS_SERVER_ROOT` is correct in Render’s environment.

## Files

- `app.py` – Flask app using `python-cas` (CAS v3).
- `requirements.txt`
- `render.yaml` – Render Blueprint (Python runtime).
- `Dockerfile` – Optional container-based deploy (not required when using the Python runtime).
