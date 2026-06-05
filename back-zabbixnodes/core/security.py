import base64
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def _get_aes_key() -> bytes:
    raw = settings.ENCRYPTION_KEY.strip()
    # Aceita a ENCRYPTION_KEY em hexadecimal (64 chars) ou base64 (32 bytes).
    try:
        key_bytes = bytes.fromhex(raw)
    except ValueError:
        try:
            key_bytes = base64.b64decode(raw, validate=True)
        except ValueError as exc:
            raise ValueError(
                "ENCRYPTION_KEY inválida: use hexadecimal (64 chars) ou base64 de 32 bytes."
            ) from exc
    # AES-256 needs exactly 32 bytes
    if len(key_bytes) < 32:
        raise ValueError(
            f"ENCRYPTION_KEY precisa de pelo menos 32 bytes para AES-256; "
            f"recebido {len(key_bytes)} byte(s)."
        )
    return key_bytes[:32]


def encrypt_token(plaintext: str) -> bytes:
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct)


def decrypt_token(ciphertext: bytes) -> str:
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(ciphertext)
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
