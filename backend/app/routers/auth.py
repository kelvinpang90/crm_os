from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    generate_tokens,
    logout,
    refresh_access_token,
)
from app.utils.response import fail, ok

router = APIRouter()

# There is deliberately no /register: accounts are created by an admin through
# POST /api/users. A self-registered rep was handed new leads by the routing
# engine, being the least-loaded active sales user.


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
