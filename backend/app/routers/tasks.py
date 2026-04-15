from typing import Annotated, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import task_service
from app.utils.response import ok, fail

router = APIRouter()


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
        db, current_user,
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
    data = await task_service.create_task(db, body.model_dump(), current_user)
    return ok(data=data)


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await task_service.get_task(db, task_id)
    if not data:
        return fail(message="Task not found", code=404)
    return ok(data=data)


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    body: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await task_service.update_task(
        db, task_id, body.model_dump(exclude_unset=True)
    )
    if not data:
        return fail(message="Task not found", code=404)
    return ok(data=data)


@router.patch("/{task_id}/toggle")
async def toggle_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await task_service.toggle_task(db, task_id)
    if not data:
        return fail(message="Task not found", code=404)
    return ok(data=data)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ok_ = await task_service.delete_task(db, task_id)
    if not ok_:
        return fail(message="Task not found", code=404)
    return ok(message="Deleted successfully")
