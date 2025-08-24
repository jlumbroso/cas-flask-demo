# app.py
import os
from flask import Flask, redirect, request, session, url_for, render_template_string
from cas_client_php import CASClientV3PHP  # subclass above

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

CAS_SERVER_ROOT = os.environ.get(
    "CAS_SERVER_ROOT", "https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/"
)  # IMPORTANT: trailing slash

SERVICE_URL = os.environ.get("SERVICE_URL")  # e.g. your Render callback URL
if not SERVICE_URL:
    # Fallback builds it from request later; on Render you should set SERVICE_URL explicitly.
    pass


def cas_client(service_url):
    return CASClientV3PHP(
        server_url=CAS_SERVER_ROOT,
        service_url=service_url,
        verify_ssl_certificate=True,
    )


@app.get("/healthz")
def healthz():
    return "ok", 200, {"Content-Type": "text/plain"}


@app.route("/")
def home():
    if "user" in session:
        attrs = session.get("attrs") or {}
        return render_template_string(
            "<h1>Profile</h1><p><b>User:</b> {{u}}</p>"
            "<h2>Attributes</h2><pre>{{a}}</pre>"
            "<p><a href='{{url_for('logout')}}'>Logout</a></p>",
            u=session["user"],
            a=attrs,
        )
    return redirect(url_for("login"))


@app.route("/login")
def login():
    svc = SERVICE_URL or (request.url_root.rstrip("/") + url_for("callback"))
    return redirect(cas_client(svc).get_login_url())


@app.route("/callback")
def callback():
    ticket = request.args.get("ticket")
    if not ticket:
        return "Missing ticket", 400
    svc = SERVICE_URL or (request.url_root.rstrip("/") + url_for("callback"))
    client = cas_client(svc)

    user, attrs, _ = client.verify_ticket(ticket)
    if not user:
        return "Ticket verification failed", 403

    session["user"] = user
    session["attrs"] = attrs or {}
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return "Logged out"
