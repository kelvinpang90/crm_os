from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectAdvance
from app.services import project_service
from app.utils.response import ok, fail

router = APIRouter()


@router.get("")
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    projects = await project_service.list_projects(db)
    return ok(data=projects)


@router.post("")
async def create_project(
    body: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    project = await project_service.create_project(db, body.model_dump())
    await db.commit()
    return ok(data=project, message="Project created", status_code=201)


@router.post("/seed-demo")
async def seed_demo(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    count = await project_service.seed_demo(db)
    await db.commit()
    return ok(data={"seeded": count}, message="Demo data reseeded")


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    project = await project_service.get_project(db, project_id)
    if not project:
        return fail("Project not found", code="NOT_FOUND", status_code=404)
    return ok(data=project)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    project = await project_service.update_project(db, project_id, body.model_dump())
    if not project:
        return fail("Project not found", code="NOT_FOUND", status_code=404)
    await db.commit()
    return ok(data=project, message="Updated successfully")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await project_service.delete_project(db, project_id)
    if not deleted:
        return fail("Project not found", code="NOT_FOUND", status_code=404)
    await db.commit()
    return ok(message="Deleted successfully")


@router.post("/{project_id}/advance")
async def advance_project(
    project_id: str,
    body: ProjectAdvance,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    project = await project_service.advance_step(db, project_id, body.note)
    if not project:
        return fail("Project not found", code="NOT_FOUND", status_code=404)
    await db.commit()
    return ok(data=project, message="Advanced to next step")