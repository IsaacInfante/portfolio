"""Per-instance configuration. Never mutates or prints the user's environment."""
import json
import os
import re
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent


def rooted(value):
    path = Path(value).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def load_settings(env_file=None):
    selected = env_file or os.environ.get("PORTFOLIO_ENV_FILE")
    path = rooted(selected) if selected else ROOT / ".env"
    if selected and not path.is_file():
        raise ValueError("El archivo de configuracion seleccionado no existe.")
    # Disable interpolation so hash/secret contents remain literal. Process wins.
    values = {**dotenv_values(path, encoding="utf-8-sig", interpolate=False), **os.environ}
    profile_path = rooted(values.get("OWNER_PROFILE_PATH") or "data/isaac.json")
    owner = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    if not isinstance(owner, dict) or not re.fullmatch(r"[a-z0-9-]{1,42}", str(owner.get("id", ""))):
        raise ValueError("El perfil propietario necesita un id publico valido.")
    if not all(isinstance(owner.get(key), str) and owner[key].strip() for key in ("name", "role")):
        raise ValueError("El perfil propietario necesita nombre y especialidad.")
    secure_cookie = (values.get("SESSION_COOKIE_SECURE") or "true").lower()
    if secure_cookie not in ("true", "false"):
        raise ValueError("SESSION_COOKIE_SECURE debe ser true o false.")
    return {
        "OWNER": owner, "OWNER_PROFILE_PATH": profile_path,
        "DATABASE_PATH": rooted(values.get("DATABASE_PATH") or "data/profiles.db"),
        "INSTANCE_ID": (values.get("INSTANCE_ID") or "").strip(),
        "GEMINI_API_KEY": (values.get("GEMINI_API_KEY") or "").strip(),
        "GEMINI_MODEL": (values.get("GEMINI_MODEL") or "gemini-3.5-flash-lite").strip(),
        "PUBLIC_BASE_URL": (values.get("PUBLIC_BASE_URL") or "").rstrip("/"),
        "SECRET_KEY": values.get("SECRET_KEY") or None,
        "OWNER_PASSWORD_HASH": values.get("OWNER_PASSWORD_HASH") or "",
        "SESSION_COOKIE_SECURE": secure_cookie == "true",
        "PORT": int(values.get("PORT") or 5000),
    }
