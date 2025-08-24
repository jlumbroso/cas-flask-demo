# CAS Flask Demo (python-cas) — fixed QuickCAS mapping

This demo uses `python-cas` and maps your QuickCAS endpoints:
- Login: /index.php/login
- Validate: /serviceValidate.php

## Why this works on Render
- We trust Render's proxy headers via `ProxyFix`, so `url_for()` generates the right https host.
- We set `CAS_SERVER_BASE` to `/cgi-bin/cas/` (no index.php) and override only the login URL.
- CAS 2.0 validation hits `/serviceValidate.php`.

## Deploy
1. Use the included `render.yaml` blueprint.
2. Ensure env vars:
   - `CAS_SERVER_BASE=https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/`
   - `CAS_VERIFY_SSL=true`
   - `SECRET_KEY` is auto-generated.
3. Open the app → sign in via CAS → land on `/profile` with user and attributes.

## Local dev
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export CAS_SERVER_BASE="https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/"
python app.py  # dev server on http://localhost:5000
```
