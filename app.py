import os
from urllib.parse import urlencode
from flask import Flask, redirect, request, session, url_for, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
from cas import CASClientV2

# QuickCAS layout (no rewrites):
#   - LOGIN: /login.php              (Shib-gated)
#   - VALIDATE: /serviceValidate.php (public)
class CASClientV2Quick(CASClientV2):
    url_suffix = 'serviceValidate.php'  # use the PHP validator
    def get_login_url(self, service_url=None, renew=False, gateway=False, extra_params=None):
        if service_url is None:
            service_url = self.service_url
        params = {'service': service_url}
        if renew:   params['renew'] = 'true'
        if gateway: params['gateway'] = 'true'
        if extra_params: params.update(extra_params)
        base = self.server_url.rstrip('/')
        return f"{base}/login.php?{urlencode(params, doseq=True)}"

def make_cas_client(service_url: str):
    server_base = os.environ.get("CAS_SERVER_BASE", "https://alliance.seas.upenn.edu/~lumbroso/cgi-bin/cas/")
    verify_ssl  = os.environ.get("CAS_VERIFY_SSL", "true").lower() != "false"
    return CASClientV2Quick(service_url=service_url, server_url=server_base, verify_ssl_certificate=verify_ssl)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-not-secure")

# Make url_for() honor Render’s X-Forwarded headers (correct https URLs)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

def service_url():
    # Absolute callback URL used for CAS "service"
    return request.url_root.rstrip('/') + url_for("callback")

@app.get("/")
def home():
    if "user" in session:
        return render_template_string(
            "<h1>Logged in</h1><p><b>User:</b> {{ user }}</p>"
            "<p><a href='{{ url_for('profile') }}'>Profile</a> · "
            "<a href='{{ url_for('logout') }}'>Logout</a></p>",
            user=session["user"],
        )
    return redirect(url_for("login"))

@app.get("/login")
def login():
    # If CAS already sent us back with a ticket, bounce to /callback
    if request.args.get("ticket"):
        return redirect(url_for("callback", **request.args))
    client = make_cas_client(service_url=service_url())
    return redirect(client.get_login_url())

@app.get("/callback")
def callback():
    ticket = request.args.get("ticket")
    if not ticket:
        return "Missing CAS ticket", 400
    client = make_cas_client(service_url=service_url())
    user, attrs, pgtiou = client.verify_ticket(ticket)
    if not user:
        return "CAS validation failed", 403
    session["user"]  = user
    session["attrs"] = attrs or {}
    return redirect(url_for("profile"))

@app.get("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(
        "<h1>Profile</h1><p><b>User:</b> {{ user }}</p>"
        "<h2>Attributes</h2><pre>{{ attrs|tojson(indent=2) }}</pre>"
        "<p><a href='{{ url_for('logout') }}'>Logout</a></p>",
        user=session["user"], attrs=session.get("attrs", {}),
    )

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/logout")
def logout():
    session.clear()
    return "Logged out locally. <a href='/'>Home</a>"
