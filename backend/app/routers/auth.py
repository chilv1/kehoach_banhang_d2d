"""Phase 8 — Auth router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth import (
    create_access_token, get_current_user, hash_password, verify_password,
)

router = APIRouter()


class RegisterPayload(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    email: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    full_name: str | None
    is_admin: bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "Username đã tồn tại")
    is_first = db.query(User).count() == 0
    u = User(username=payload.username, email=payload.email, full_name=payload.full_name,
             hashed_password=hash_password(payload.password), is_admin=is_first)
    db.add(u); db.commit(); db.refresh(u)
    return u


@router.post("/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == form.username).first()
    if not u or not verify_password(form.password, u.hashed_password):
        raise HTTPException(401, "Sai username hoặc mật khẩu")
    return TokenOut(access_token=create_access_token(u.id), user=u)


@router.get("/auth/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
