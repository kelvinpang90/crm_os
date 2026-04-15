from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    generate_tokens,
    refresh_access_token,
    logout,
)
from app.utils.security import hash_password
from app.utils.response import ok, fail

router = APIRouter()


@router.post("/register")
async def register(body: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    from sqlalchemy import select

    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        return fail("Email already registered", code="EMAIL_EXISTS", status_code=400)

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role="sales",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    tokens = generate_tokens(user)
    user_data = UserResponse.model_validate(user).model_dump(mode="json")
    return ok(
        data={"user": user_data, **tokens},
        message="Registered successfully",
    )


@router.post("/login")
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    user, error = await authenticate_user(body.email, body.password, db)
    if error:
        code = "ACCOUNT_LOCKED" if "locked" in error else "AUTH_FAILED"
        status_code = 423 if "locked" in error else 401
        return fail(error, code=code, status_code=status_code)

    tokens = generate_tokens(user)
    user_data = UserResponse.model_validate(user).model_dump(mode="json")
    return ok(
        data={"user": user_data, **tokens},
        message="Login successful",
    )


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    tokens, error = await refresh_access_token(body.refresh_token, db)
    if error:
        return fail(error, code="TOKEN_ERROR", status_code=401)
    return ok(data=tokens, message="Token refreshed")


@router.post("/logout")
async def logout_route(
    body: RefreshRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
):
    await logout(body.refresh_token)
    return ok(message="Logged out")


@router.get("/me")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    user_data = UserResponse.model_validate(current_user).model_dump(mode="json")
    return ok(data=user_data)
