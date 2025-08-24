import os
import logging
from urllib.parse import quote
from flask import Flask, redirect, request, session, url_for, Response
import requests
import xml.etree.ElementTree as ET

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
app = Flask(__name__)

# session/secret
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # Render serves HTTPS
)

CAS_BASE = os.environ.get("CAS_BASE", "").rstrip("/")
# Prefer explicit SERVICE_BASE_URL; fall back to request.url_root
SERVICE_BASE_URL = os.environ.get("SERVICE_BASE_URL", "").rstrip("/")
DEBUG_XML = os.environ.get("DEBUG_XML", "false").lower() in {"1", "true", "yes", "on"}

logger = logging.getLogger("cas-demo")
logging.basicConfig(level=logging.INFO)

def external_service_base():
    if SERVICE_BASE_URL:
        return SERVICE_BASE_URL
    # derive from incoming request
    return request.url_root.rstrip("/")

def cas_login_url(service_url: str) -> str:
    # use /login.php on your proxy; no rewrites assumed
    return f"{CAS_BASE}/login.php?service={quote(service_url, safe=':/?&=')}"

def cas_service_validate_url() -> str:
    # use /serviceValidate.php (public)
    return f"{CAS_BASE}/serviceValidate.php"

# ----------------------------------------------------------------------------
# CAS XML parsing (supports both canonical and legacy attribute styles)
# ----------------------------------------------------------------------------
def parse_cas_v2(xml_text: str):
    ns = {"cas": "http://www.yale.edu/tp/cas"}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return None, {}, f"xml parse error: {e}"

    success = root.find("cas:authenticationSuccess", ns)
    if success is None:
        fail = root.find("cas:authenticationFailure", ns)
        msg = (fail.text or "validation failed") if fail is not None else "validation failed"
        return None, {}, msg

    user_el = success.find("cas:user", ns)
    user = (user_el.text or "").strip() if user_el is not None else ""

    attrs = {}
    # Canonical block
    block = success.find("cas:attributes", ns)
    if block is not None:
        for child in list(block):
            key = child.tag.split('}', 1)[1] if '}' in child.tag else child.tag
            val = (child.text or "").strip()
            if key in attrs:
                if isinstance(attrs[key], list):
                    attrs[key].append(val)
                else:
                    attrs[key] = [attrs[key], val]
            else:
                attrs[key] = val

    # Legacy/sibling attributes with name="..."
    for xp in ("cas:attribute", "cas:attributes/cas:attribute"):
        for a in success.findall(xp, ns):
            name = a.attrib.get("name")
            if not name:
                continue
            val = (a.text or "").strip()
            if name in attrs:
                if isinstance(attrs[name], list):
                    attrs[name].append(val)
                else:
                    attrs[name] = [attrs[name], val]
            else:
                attrs[name] = val

    return user, attrs, None

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return "ok", 200, {"Content-Type": "text/plain"}

@app.get("/")
def home():
    if not CAS_BASE:
        return (
            "<h1>CAS demo</h1>"
            "<p><b>Missing env:</b> set <code>CAS_BASE</code> to your proxy base URL.</p>",
            200,
        )
    if "cas_user" in session:
        return redirect(url_for("profile"))
    return (
        "<h1>CAS demo</h1>"
        "<p><a href='/login'>Login</a></p>",
        200,
    )

@app.get("/login")
def login():
    svc = external_service_base() + url_for("callback")
    return redirect(cas_login_url(svc))

@app.get("/callback")
def callback():
    ticket = request.args.get("ticket")
    if not ticket:
        return "Missing ticket", 400

    svc = external_service_base() + url_for("callback")
    params = {"service": svc, "ticket": ticket}

    try:
        r = requests.get(cas_service_validate_url(), params=params, allow_redirects=False, timeout=10)
    except requests.RequestException as e:
        return f"Ticket verify request failed: {e}", 502

    if r.status_code in (301, 302):
        # If you see this, serviceValidate is likely Shib-gated; fix .htaccess on the proxy.
        loc = r.headers.get("Location", "")
        return f"Unexpected redirect during validation: {loc}", 502

    xml = r.text
    if DEBUG_XML:
        logger.info("CAS XML:\n%s", xml)
    user, attrs, err = parse_cas_v2(xml)
    if err or not user:
        return f"<h1>Login failed</h1><pre>{(err or 'unknown error')}</pre><pre>{xml}</pre>", 403

    session["cas_user"] = user
    session["cas_attrs"] = attrs
    return redirect(url_for("profile"))

@app.get("/profile")
def profile():
    if "cas_user" not in session:
        return redirect(url_for("home"))
    user = session.get("cas_user")
    attrs = session.get("cas_attrs", {})
    # pretty, but tiny
    return (
        f"<h1>Profile</h1>"
        f"<p><b>User:</b> {user}</p>"
        f"<h2>Attributes</h2>"
        f"<pre>{attrs}</pre>"
        f"<p><a href='{url_for('logout')}'>Logout</a></p>",
        200,
    )

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ----------------------------------------------------------------------------
# Entrypoint (Render sets $PORT)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
