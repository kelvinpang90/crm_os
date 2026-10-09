from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import access_service, task_service
from app.utils.response import fail, ok

router = APIRouter()


def _not_found(what: str = "Task"):
    # Also the answer for a record that is not yours, so an id's existence is
    # never confirmed to someone who may not see it.
    return fail(f"{what} not found", code="NOT_FOUND", status_code=404)


async def _refuse_links(db: AsyncSession, user: User, data: dict):
    """A task may only point at a customer, and go to a person, within reach."""
    if data.get("contact_id") and not await access_service.may_access_contact(
        db, user, data["contact_id"]
    ):
        return _not_found("Contact")
    if data.get("assigned_to") and not await access_service.may_assign_to(
        db, user, data["assigned_to"]
    ):
        return fail("Permission denied", code="FORBIDDEN", status_code=403)
    return None


@router.get("")
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_before: Optional[date] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    data = await task_service.list_tasks(
        db,
        current_user,
        status=status_filter,
        priority=priority,
        assigned_to=assigned_to,
        due_before=due_before,
        search=search,
        page=page,
        page_size=page_size,
    )
    return ok(data=data)


@router.post("")
async def create_task(
    body: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = body.model_dump()
    if refusal := await _refuse_links(db, current_user, payload):
        return refusal
    data = await task_service.create_task(db, payload, current_user)
    return ok(data=data)


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await access_service.may_access_task(db, current_user, task_id):
        return _not_found()
    data = await task_service.get_task(db, task_id)
    if not data:
        return _not_found()
    return ok(data=data)


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    body: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await access_service.may_access_task(db, current_user, task_id):
        return _not_found()
    current = await task_service.get_task(db, task_id)
    if not current:
        return _not_found()
    payload = body.model_dump(exclude_unset=True)
    # The edit form sends every field back. A task may point at a customer its
    # assignee cannot open (a manager's, say), so only a changed link is checked.
    changed = {k: v for k, v in payload.items() if v != current.get(k)}
    if refusal := await _refuse_links(db, current_user, changed):
        return refusal
    data = await task_service.update_task(db, task_id, payload)
    if not data:
        return _not_found()
    return ok(data=data)


@router.patch("/{task_id}/toggle")
async def toggle_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await access_service.may_access_task(db, current_user, task_id):
        return _not_found()
    data = await task_service.toggle_task(db, task_id)
    if not data:
        return _not_found()
    return ok(data=data)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not await access_service.may_access_task(db, current_user, task_id):
        return _not_found()
    ok_ = await task_service.delete_task(db, task_id)
    if not ok_:
        return _not_found()
    return ok(message="Deleted successfully")
