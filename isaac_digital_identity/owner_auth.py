"""Owner-only actions with revocable server-side sessions and CSRF tokens."""
import hashlib
import hmac
import ipaddress
import re
import secrets
import time
from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash

owner_api = Blueprint("owner", __name__, url_prefix="/api/owner")


def database():
    return current_app.extensions["portfolio_database"]()


def configured():
    return bool(current_app.config.get("OWNER_AUTH_ENABLED"))


def transport_safe():
    # HTTP is an explicit localhost-only development exception.
    try:
        loopback = ipaddress.ip_address(request.remote_addr or "").is_loopback
    except ValueError:
        loopback = False
    return request.is_secure or (
        not current_app.config["SESSION_COOKIE_SECURE"]
        and loopback
        and request.host.split(":", 1)[0] in ("localhost", "127.0.0.1")
    )


def digest(value):
    return hmac.new(current_app.config["SECRET_KEY"].encode(), value.encode(), hashlib.sha256).hexdigest()


def cookie_name():
    return "portfolio_owner_" + current_app.config["INSTANCE_ID"].replace("-", "")


def auth_session():
    token = request.cookies.get(cookie_name(), "")
    row = None
    if configured() and re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        with database() as db:
            row = db.execute(
                "SELECT sid, csrf, authenticated FROM owner_sessions WHERE sid=? AND expires>? AND credential_version=?",
                (digest(token), time.time(), digest(current_app.config["OWNER_PASSWORD_HASH"])),
            ).fetchone()
    return row


def owner_still_authorized():
    row = auth_session()
    return bool(row and row[2])


def same_origin():
    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        return False
    origin = request.headers.get("Origin")
    expected = current_app.config.get("PUBLIC_BASE_URL") or request.host_url
    def normalized(value):
        p = urlsplit(value)
        return (p.scheme.lower(), p.hostname, p.port or (443 if p.scheme == "https" else 80))
    try:
        return not origin or normalized(origin) == normalized(expected)
    except ValueError:
        return False


def csrf_valid():
    row = auth_session()
    token = request.headers.get("X-CSRF-Token", "")
    return bool(row and same_origin() and len(token) == 43 and hmac.compare_digest(row[1], token))


def owner_required(view):
    @wraps(view)
    def protected(*args, **kwargs):
        if not configured():
            return jsonify(error="El acceso del propietario no esta configurado."), 503
        if not transport_safe():
            return jsonify(error="El acceso privado requiere HTTPS; HTTP solo se admite en localhost."), 403
        row = auth_session()
        if not row or not row[2]:
            return jsonify(error="Inicia sesion como propietario."), 401
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if not csrf_valid():
                return jsonify(error="Token CSRF invalido o procedencia no permitida."), 403
            if not request.is_json:
                return jsonify(error="Se requiere JSON."), 415
        return view(*args, **kwargs)
    return protected


def issue_session(authenticated, old=None):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    now = time.time()
    ttl = 1800 if authenticated else 600
    with database() as db:
        db.execute("DELETE FROM owner_sessions WHERE expires<=?", (now,))
        if old:
            db.execute("DELETE FROM owner_sessions WHERE sid=?", (old[0],))
        db.execute("INSERT INTO owner_sessions VALUES (?,?,?,?,?)", (
            digest(token), csrf, int(authenticated), now + ttl,
            digest(current_app.config["OWNER_PASSWORD_HASH"]),
        ))
    response = jsonify(authenticated=authenticated, configured=True, csrf_token=csrf,
                       expires_in=ttl, mode="local_demo", federation_enabled=False)
    response.set_cookie(cookie_name(), token, max_age=ttl, httponly=True,
                        secure=current_app.config["SESSION_COOKIE_SECURE"], samesite="Strict", path="/")
    return response


@owner_api.get("/session")
def session_state():
    if not same_origin():
        return jsonify(error="Procedencia no permitida."), 403
    if not configured():
        return jsonify(authenticated=False, configured=False, csrf_token=None,
                       mode="local_demo", federation_enabled=False)
    if not transport_safe():
        return jsonify(error="El acceso privado requiere HTTPS; HTTP solo se admite en localhost."), 403
    row = auth_session()
    if row:
        return jsonify(authenticated=bool(row[2]), configured=True, csrf_token=row[1],
                       mode="local_demo", federation_enabled=False)
    # Bound anonymous session creation globally as well as by client address.
    if not reserve_attempt("session", 120, 60):
        return jsonify(error="Demasiadas solicitudes. Intenta mas tarde."), 429
    return issue_session(False)


def reserve_attempt(action, limit, window):
    # Persist across processes/restarts. No trust in client-supplied Forwarded headers.
    now = time.time()
    bucket = int(now // window)
    keys = (action + ":global", action + ":" + (request.remote_addr or "unknown"))
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM owner_attempts WHERE expires<=?", (now,))
        for key in keys:
            count = db.execute("SELECT count FROM owner_attempts WHERE bucket=? AND subject=?", (bucket, key)).fetchone()
            threshold = limit * 5 if key.endswith(":global") else limit
            if count and count[0] >= threshold:
                return False
        for key in keys:
            db.execute("INSERT INTO owner_attempts VALUES (?,?,1,?) ON CONFLICT(bucket,subject) DO UPDATE SET count=count+1",
                       (bucket, key, (bucket + 1) * window))
    return True


@owner_api.post("/login")
def login():
    if not configured():
        return jsonify(error="El acceso del propietario no esta configurado."), 503
    if not transport_safe():
        return jsonify(error="El acceso privado requiere HTTPS; HTTP solo se admite en localhost."), 403
    if not csrf_valid():
        return jsonify(error="Token CSRF invalido o procedencia no permitida."), 403
    if not request.is_json:
        return jsonify(error="Se requiere JSON."), 415
    if not reserve_attempt("login", 5, 300):
        return jsonify(error="Demasiados intentos. Espera cinco minutos."), 429
    data = request.get_json(silent=True)
    password = data.get("password") if isinstance(data, dict) else None
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        return jsonify(error="Credenciales incorrectas."), 401
    if not check_password_hash(current_app.config["OWNER_PASSWORD_HASH"], password):
        return jsonify(error="Credenciales incorrectas."), 401
    return issue_session(True, old=auth_session())


@owner_api.post("/logout")
@owner_required
def logout():
    with database() as db:
        db.execute("DELETE FROM owner_sessions WHERE sid=?", (auth_session()[0],))
    response = jsonify(authenticated=False)
    response.delete_cookie(cookie_name(), path="/", secure=current_app.config["SESSION_COOKIE_SECURE"],
                           httponly=True, samesite="Strict")
    return response


def install_owner_auth(app, db_factory):
    secret = app.config.get("SECRET_KEY")
    password_hash = app.config.get("OWNER_PASSWORD_HASH", "")
    if secret and (not isinstance(secret, str) or len(secret) < 32):
        raise ValueError("SECRET_KEY necesita al menos 32 caracteres aleatorios.")
    if password_hash and not re.fullmatch(r"scrypt:32768:8:1\$[A-Za-z0-9]{16,}\$[0-9a-f]{128}", password_hash):
        raise ValueError("OWNER_PASSWORD_HASH debe generarse con la herramienta de configuracion.")
    app.config["OWNER_AUTH_ENABLED"] = bool(secret and password_hash)
    app.extensions["portfolio_database"] = db_factory
    app.register_blueprint(owner_api)

    @app.after_request
    def private_headers(response):
        if request.path.startswith("/api/owner/") or request.method != "GET":
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
