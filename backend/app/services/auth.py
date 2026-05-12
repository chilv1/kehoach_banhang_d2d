"""Phase 8 — Auth service.

Tự cài JWT (HS256) bằng `hmac`+`hashlib` để tránh phụ thuộc cryptography.
Password hash dùng pbkdf2_hmac (stdlib).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me-in-production-x9f3k")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MIN = 60 * 24 * 7  # 7 days
PWD_ITERATIONS = 200_000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ---------- JWT (HS256, no external lib) ----------

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(msg: bytes) -> bytes:
    return hmac.new(JWT_SECRET.encode(), msg, hashlib.sha256).digest()


def jwt_encode(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url(_sign(f"{h}.{p}".encode()))
    return f"{h}.{p}.{sig}"


def jwt_decode(token: str) -> dict:
    try:
        h, p, sig = token.split(".")
    except ValueError as exc:
        raise ValueError("Token sai định dạng") from exc
    expected = _b64url(_sign(f"{h}.{p}".encode()))
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Sai chữ ký")
    payload = json.loads(_b64url_decode(p))
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        raise ValueError("Token hết hạn")
    return payload


# ---------- Password hash (pbkdf2_hmac, stdlib) ----------

def hash_password(plain: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, PWD_ITERATIONS)
    return f"pbkdf2_sha256${PWD_ITERATIONS}${_b64url(salt)}${_b64url(dk)}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        algo, iters, salt_b64, dk_b64 = hashed.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    salt = _b64url_decode(salt_b64)
    expected = _b64url_decode(dk_b64)
    test = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, int(iters))
    return hmac.compare_digest(test, expected)


# ---------- Token helpers ----------

def create_access_token(user_id: int, extra: Optional[dict] = None) -> str:
    payload = {
        "sub": str(user_id),
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MIN)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt_encode(payload)


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt_decode(token)
        uid = int(payload.get("sub", "0"))
    except (ValueError, KeyError):
        return None
    return db.get(User, uid)


def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cần đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
