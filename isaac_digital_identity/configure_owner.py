"""Create a NEW private instance config using hidden password input.

Never overwrites an existing file, imports app, or reads/copies .env or Gemini keys.
"""
import argparse
import getpass
import json
import secrets
import uuid
from pathlib import Path

from werkzeug.security import generate_password_hash

def main():
    parser = argparse.ArgumentParser(description="Crear configuracion privada independiente de Portfolio.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--local-http", action="store_true", help="Solo localhost, sin TLS")
    args = parser.parse_args()
    profile = Path(args.profile).resolve()
    owner = json.loads(profile.read_text(encoding="utf-8-sig"))
    if not isinstance(owner, dict) or not owner.get("id") or not owner.get("name"):
        parser.error("Perfil propietario invalido.")
    if not 1024 <= args.port <= 65535:
        parser.error("El puerto debe estar entre 1024 y 65535.")
    output = Path(args.output).resolve()
    if output.exists() or output.name == ".env":
        parser.error("Usa un archivo nuevo distinto de .env. No se sobrescriben archivos.")
    password = getpass.getpass("Nueva contrasena del propietario (minimo 14 caracteres): ")
    confirmation = getpass.getpass("Repite la contrasena: ")
    if len(password) < 14 or len(password) > 256 or password != confirmation:
        parser.error("Las contrasenas deben coincidir y tener entre 14 y 256 caracteres.")
    # Quote path values for python-dotenv; forward slashes avoid Windows escapes.
    def quote(path):
        value = Path(path).resolve().as_posix()
        if any(c in value for c in ('"', '\n', '\r', '\\')):
            parser.error("La ruta contiene caracteres no admitidos.")
        return '"' + value + '"'
    content = (
        "# Archivo privado. No compartir ni subir a Git.\n"
        f"OWNER_PROFILE_PATH={quote(profile)}\n"
        f"DATABASE_PATH={quote(args.database)}\n"
        f"INSTANCE_ID={uuid.uuid4()}\n"
        f"SECRET_KEY={secrets.token_urlsafe(48)}\n"
        f"OWNER_PASSWORD_HASH={generate_password_hash(password, method='scrypt:32768:8:1')}\n"
        f"SESSION_COOKIE_SECURE={'false' if args.local_http else 'true'}\n"
        f"PORT={args.port}\n"
        "GEMINI_API_KEY=\nGEMINI_MODEL=gemini-3.5-flash-lite\nPUBLIC_BASE_URL=\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as file:
        file.write(content)
    print("Configuracion creada. Protege el archivo con los permisos de tu cuenta.")
    print("No se configuro ni se copio ninguna clave de Gemini.")


if __name__ == "__main__":
    main()
