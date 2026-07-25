import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import autocount_service, autocount_client
from app.utils.response import ok, fail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync")
async def sync_now(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        result = await autocount_service.sync_all(db)
    except autocount_client.AutocountClientError as e:
        return fail(str(e), code="AUTOCOUNT_API_ERROR", status_code=502)
    except httpx.HTTPError as e:
        logger.exception("AutoCount sync: network error reaching the API")
        return fail(f"Could not reach AutoCount API: {e}", code="AUTOCOUNT_NETWORK_ERROR", status_code=502)
    return ok(data=result, message="Sync complete")
