
import os
from flask import Flask, redirect, request, session, url_for, render_template_string
from cas import CASClientV2

class CASClientV2Quick(CASClientV2):
    url_suffix = 'serviceValidate.php'

def external_base_url():
    return os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("PUBLIC_URL") or "http://localhost:10000"

def make_cas_client(service_url: str):
    server_base = os.environ.get("CAS_SERVER_BASE", "https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/index.php/")
    verify_ssl = os.environ.get("CAS_VERIFY_SSL", "true").lower() != "false"
    return CASClientV2Quick(service_url=service_url, server_url=server_base, verify_ssl_certificate=verify_ssl)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-not-secure")

@app.route("/")
def home():
    if "user" in session:
        return render_template_string(
            "<h1>Logged in</h1><p><b>User:</b> {{ user }}</p><p><a href='{{ url_for('profile') }}'>Profile</a> · <a href='{{ url_for('logout') }}'>Logout</a></p>",
            user=session["user"],
        )
    return redirect(url_for("login"))

@app.route("/login")
def login():
    if request.args.get("ticket"):
        return redirect(url_for("callback", **request.args))
    service = external_base_url() + url_for("callback")
    client = make_cas_client(service_url=service)
    return redirect(client.get_login_url())

@app.route("/callback")
def callback():
    ticket = request.args.get("ticket")
    if not ticket:
        return "Missing CAS ticket", 400
    service = external_base_url() + url_for("callback")
    client = make_cas_client(service_url=service)
    user, attrs, pgtiou = client.verify_ticket(ticket)
    if not user:
        return "CAS validation failed", 403
    session["user"] = user
    session["attrs"] = attrs or {}
    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(
        "<h1>Profile</h1><p><b>User:</b> {{ user }}</p><h2>Attributes</h2><pre>{{ attrs|tojson(indent=2) }}</pre><p><a href='{{ url_for('logout') }}'>Logout</a></p>",
        user=session["user"], attrs=session.get("attrs", {}),
    )

@app.route("/logout")
def logout():
    session.clear()
    return "Logged out locally. <a href='/'>Home</a>"
