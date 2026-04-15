from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.utils.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

# Redis connection (lazy init)
_redis: Optional[aioredis.Redis] = None

LOGIN_ATTEMPT_PREFIX = "login_attempts:"
LOGIN_LOCK_PREFIX = "login_lock:"
TOKEN_BLACKLIST_PREFIX = "token_blacklist:"
MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_SECONDS = 600  # 10 minutes


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def is_account_locked(email: str) -> bool:
    r = await get_redis()
    return await r.exists(f"{LOGIN_LOCK_PREFIX}{email}") > 0


async def increment_login_attempts(email: str) -> int:
    r = await get_redis()
    key = f"{LOGIN_ATTEMPT_PREFIX}{email}"
    attempts = await r.incr(key)
    await r.expire(key, LOCK_DURATION_SECONDS)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        await r.setex(f"{LOGIN_LOCK_PREFIX}{email}", LOCK_DURATION_SECONDS, "1")
        await r.delete(key)
    return attempts


async def reset_login_attempts(email: str) -> None:
    r = await get_redis()
    await r.delete(f"{LOGIN_ATTEMPT_PREFIX}{email}")


async def add_token_to_blacklist(token: str, expire_seconds: int = 604800) -> None:
    r = await get_redis()
    await r.setex(f"{TOKEN_BLACKLIST_PREFIX}{token}", expire_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    r = await get_redis()
    return await r.exists(f"{TOKEN_BLACKLIST_PREFIX}{token}") > 0


async def authenticate_user(
    email: str, password: str, db: AsyncSession
) -> tuple[Optional[User], Optional[str]]:
    """
    Returns (user, error_message).
    user is None on failure, error_message explains why.
    """
    # Check lock
    if await is_account_locked(email):
        return None, "Account locked, please retry in 10 minutes"

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        return None, "Account not found"

    if not user.is_active:
        return None, "Account is disabled"

    if not verify_password(password, user.password_hash):
        attempts = await increment_login_attempts(email)
        remaining = MAX_LOGIN_ATTEMPTS - attempts
        if remaining <= 0:
            return None, "Too many failed attempts, account locked for 10 minutes"
        return None, f"Incorrect password, {remaining} attempt(s) remaining"

    # Success
    await reset_login_attempts(email)
    return user, None


def generate_tokens(user: User) -> dict:
    payload = {"sub": user.id, "email": user.email, "role": user.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(
    refresh_token: str, db: AsyncSession
) -> tuple[Optional[dict], Optional[str]]:
    """
    Returns (new_tokens, error_message).
    """
    if await is_token_blacklisted(refresh_token):
        return None, "Token expired, please log in again"

    payload = decode_token(refresh_token)
    if payload is None:
        return None, "Invalid token"

    if payload.get("type") != "refresh":
        return None, "Invalid token type"

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None, "User not found or inactive"

    tokens = generate_tokens(user)
    return tokens, None


async def logout(refresh_token: str) -> None:
    await add_token_to_blacklist(refresh_token)
