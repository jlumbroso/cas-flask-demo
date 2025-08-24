import os
from flask import Flask, render_template_string
from flask_cas import CAS, login_required  # provided by flask-cas-ng

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-not-secret")

# Configure CAS client from environment (works with quick-cas proxy)
app.config.update(
    # Base URL of your CAS server (must be https)
    # e.g. https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas
    CAS_SERVER=os.environ["CAS_SERVER"],

    # quick-cas routes (override Apereo defaults)
    CAS_LOGIN_ROUTE=os.environ.get("CAS_LOGIN_ROUTE", "/index.php/login"),
    CAS_VALIDATE_ROUTE=os.environ.get("CAS_VALIDATE_ROUTE", "/serviceValidate.php"),

    # where to go after successful login (endpoint name)
    CAS_AFTER_LOGIN="home",
)

# Mount the extension; it auto-creates /cas/login and /cas/logout
cas = CAS(app, "/cas")

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
@login_required
def home():
    # cas.username -> 'lumbroso', cas.attributes -> dict (from CAS 2.0)
    return render_template_string(
        '''
        <h1>✅ CAS Login Successful</h1>
        <p><b>Username:</b> {{ u }}</p>
        <h2>Attributes</h2>
        <pre>{{ attrs|tojson(indent=2) }}</pre>
        <p><a href="/cas/logout">Logout</a></p>
        ''',
        u=cas.username,
        attrs=cas.attributes or {},
    )

if __name__ == "__main__":
    # For local quick tests; Render uses gunicorn via Dockerfile
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
