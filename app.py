import os
from flask import Flask, redirect, request, session, url_for, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
from cas import CASClient

# ----- Config -----
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
CAS_SERVER_ROOT = os.environ.get(
    "CAS_SERVER_ROOT",
    "https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/index.php/",
).rstrip("/") + "/"  # ensure trailing slash

app = Flask(__name__)
app.secret_key = SECRET_KEY
# help Flask build correct https URLs behind a proxy (Render/ngrok/etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
    PREFERRED_URL_SCHEME="https",
)

PROFILE_TMPL = """<h1>Profile</h1>
<p><b>User:</b> {{ user }}</p>
<h2>Attributes</h2>
<pre>{{ attrs|tojson(indent=2) }}</pre>
<p><a href='{{ url_for("logout") }}'>Logout</a></p>
"""

@app.route("/healthz")
def healthz():
    return "ok", 200

@app.route("/")
def index():
    if "user" in session:
        return render_template_string(PROFILE_TMPL, user=session["user"], attrs=session.get("attrs", {}))
    return redirect(url_for("login"))

@app.route("/login")
def login():
    service_url = url_for("callback", _external=True)
    client = CASClient(
        version=3,               # CAS 3.0 (p3/serviceValidate)
        server_url=CAS_SERVER_ROOT,
        service_url=service_url,
        verify_ssl_certificate=True,
    )
    return redirect(client.get_login_url())

@app.route("/callback")
def callback():
    ticket = request.args.get("ticket")
    if not ticket:
        return "Missing ticket", 400

    service_url = url_for("callback", _external=True)
    client = CASClient(
        version=3,
        server_url=CAS_SERVER_ROOT,
        service_url=service_url,
        verify_ssl_certificate=True,
    )

    try:
        user, attrs, _ = client.verify_ticket(ticket)
    except Exception as e:
        return f"Ticket verification error: {e}", 500

    if not user:
        return "Authentication failed", 403

    # attributes may be None (library returns None when empty)
    session["user"] = user
    session["attrs"] = attrs or {}
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    # clear local session
    session.clear()
    # optionally, redirect to CAS logout (with service back to '/')
    service_back = url_for("index", _external=True)
    # CAS v3 uses 'service' for logout redirection
    logout_url = f"{CAS_SERVER_ROOT}logout?service={service_back}"
    return redirect(logout_url)

if __name__ == "__main__":
    # local dev only
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
