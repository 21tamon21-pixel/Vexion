import secrets
import hashlib

def generate_api_key() -> str:
    return "vex_" + secrets.token_urlsafe(32)

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
