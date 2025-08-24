
# CAS Flask Demo (python-cas)

Minimal Flask demo authenticating against a CAS 2.0 server using `python-cas`.
Works with Flask 2.3/3.x.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export CAS_SERVER_BASE="https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/index.php/"
export FLASK_ENV=development
python app.py  # dev
# or: PORT=10000 gunicorn app:app
```

Open the site, you'll be redirected to CAS and then to `/profile` with your username
and attributes.

## Render deploy

Use the included `render.yaml` to deploy on the free plan.
