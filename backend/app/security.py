import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())

SESSION_COOKIE_NAME = "session"
SESSION_TTL = timedelta(days=7)
OAUTH_STATE_COOKIE_NAME = "oauth_state"


def verify_github_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Verifies X-Hub-Signature-256 using constant-time comparison so the
    webhook endpoint can't be fooled by forged or tampered requests."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256
    ).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


def encrypt_secret(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def create_session_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + SESSION_TTL,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SESSION_SECRET, algorithm="HS256")


def decode_session_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
