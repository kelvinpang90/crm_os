"""Business logic for the self-contained project tracking module.

Returns plain dicts shaped to match the frontend `Project` type
(services/projects.ts): field `last_updated_at` maps to the DB `updated_at`.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStepHistory
from app.data.project_seed import build_seed_rows, photos_for

MIN_STEP = 1
MAX_STEP = 12


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

async def list_projects(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Project).where(Project.deleted_at.is_(None)).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    if not projects:
        return []

    ids = [p.id for p in projects]
    hist_result = await db.execute(
        select(ProjectStepHistory)
        .where(ProjectStepHistory.project_id.in_(ids))
        .order_by(ProjectStepHistory.step_no.asc())
    )
    history_by_project: dict[str, list[ProjectStepHistory]] = {}
    for h in hist_result.scalars().all():
        history_by_project.setdefault(h.project_id, []).append(h)

    return [_project_to_dict(p, history_by_project.get(p.id, [])) for p in projects]


async def get_project(db: AsyncSession, project_id: str) -> Optional[dict]:
    project = await _get(db, project_id)
    if not project:
        return None
    history = await _load_history(db, project_id)
    return _project_to_dict(project, history)


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

async def create_project(db: AsyncSession, data: dict) -> dict:
    now = datetime.utcnow()
    current_step = data.get("current_step", 1)
    project = Project(
        id=str(uuid.uuid4()),
        customer_name=data["customer_name"],
        address=data.get("address", ""),
        service_type=data.get("service_type", ""),
        project_manager=data.get("project_manager", ""),
        current_step=current_step,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    # Backfill history for steps 1..current_step so the timeline reads sensibly.
    for step in range(MIN_STEP, current_step + 1):
        db.add(_history_entry(project.id, step, project.project_manager, now))
    await db.flush()
    history = await _load_history(db, project.id)
    return _project_to_dict(project, history)


async def update_project(db: AsyncSession, project_id: str, data: dict) -> Optional[dict]:
    project = await _get(db, project_id)
    if not project:
        return None

    old_step = project.current_step
    for key in ("customer_name", "address", "service_type", "project_manager", "current_step"):
        if data.get(key) is not None:
            setattr(project, key, data[key])
    now = datetime.utcnow()
    project.updated_at = now

    # If the step was bumped forward via edit, log the newly-passed steps.
    new_step = project.current_step
    if new_step > old_step:
        for step in range(old_step + 1, new_step + 1):
            db.add(_history_entry(project.id, step, project.project_manager, now))

    await db.flush()
    history = await _load_history(db, project.id)
    return _project_to_dict(project, history)


async def delete_project(db: AsyncSession, project_id: str) -> bool:
    project = await _get(db, project_id)
    if not project:
        return False
    project.deleted_at = datetime.utcnow()
    await db.flush()
    return True


async def advance_step(db: AsyncSession, project_id: str, note: Optional[str] = None) -> Optional[dict]:
    project = await _get(db, project_id)
    if not project:
        return None
    if project.current_step >= MAX_STEP:
        history = await _load_history(db, project_id)
        return _project_to_dict(project, history)

    now = datetime.utcnow()
    next_step = project.current_step + 1
    db.add(_history_entry(project.id, next_step, project.project_manager, now, note))
    project.current_step = next_step
    project.updated_at = now
    await db.flush()
    history = await _load_history(db, project.id)
    return _project_to_dict(project, history)


# ---------------------------------------------------------------------------
# Demo seeding
# ---------------------------------------------------------------------------

async def seed_demo(db: AsyncSession) -> int:
    """Reset both tables and reseed the demo projects relative to now.

    Used by POST /api/projects/seed-demo to refresh the demo before a showing.
    Initial seeding happens in the 007 migration, not here.
    """
    await db.execute(delete(ProjectStepHistory))
    await db.execute(delete(Project))

    project_rows, history_rows = build_seed_rows(datetime.utcnow())
    for row in project_rows:
        db.add(Project(**row))
    for row in history_rows:
        db.add(ProjectStepHistory(**row))
    await db.flush()
    return len(project_rows)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get(db: AsyncSession, project_id: str) -> Optional[Project]:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def _load_history(db: AsyncSession, project_id: str) -> list[ProjectStepHistory]:
    result = await db.execute(
        select(ProjectStepHistory)
        .where(ProjectStepHistory.project_id == project_id)
        .order_by(ProjectStepHistory.step_no.asc())
    )
    return list(result.scalars().all())


def _history_entry(
    project_id: str, step_no: int, updated_by: str, entered_at: datetime, note: Optional[str] = None
) -> ProjectStepHistory:
    return ProjectStepHistory(
        id=str(uuid.uuid4()),
        project_id=project_id,
        step_no=step_no,
        entered_at=entered_at,
        updated_by=updated_by,
        note=note,
        photos=photos_for(step_no),
    )


def _project_to_dict(project: Project, history: list[ProjectStepHistory]) -> dict:
    return {
        "id": project.id,
        "customer_name": project.customer_name,
        "address": project.address,
        "service_type": project.service_type,
        "project_manager": project.project_manager,
        "current_step": project.current_step,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "last_updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "history": [
            {
                "id": h.id,
                "project_id": h.project_id,
                "step_no": h.step_no,
                "entered_at": h.entered_at.isoformat() if h.entered_at else None,
                "updated_by": h.updated_by,
                "note": h.note,
                "photos": h.photos or [],
            }
            for h in history
        ],
    }
