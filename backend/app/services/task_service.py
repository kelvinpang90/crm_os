import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.contact import Contact
from app.models.user import User


async def list_tasks(
    db: AsyncSession,
    current_user: User,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_before: Optional[date] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(Task)

    # Data permission
    if current_user.role == "sales":
        query = query.where(Task.assigned_to == current_user.id)
    elif current_user.role == "manager":
        team_ids_q = select(User.id).where(User.manager_id == current_user.id)
        team_result = await db.execute(team_ids_q)
        team_ids = [r for r in team_result.scalars().all()]
        team_ids.append(current_user.id)
        query = query.where(Task.assigned_to.in_(team_ids))

    # Filters
    if status == "pending":
        query = query.where(Task.is_done == False)
    elif status == "done":
        query = query.where(Task.is_done == True)
    elif status == "overdue":
        query = query.where(Task.is_done == False, Task.due_date < date.today())
    elif status == "today":
        query = query.where(Task.is_done == False, Task.due_date == date.today())

    if priority:
        query = query.where(Task.priority == priority)
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)
    if due_before:
        query = query.where(Task.due_date <= due_before)
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Task.is_done.asc(), func.isnull(Task.due_date).asc(), Task.due_date.asc(), Task.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Enrich with names
    items = []
    for t in tasks:
        d = _task_to_dict(t)
        if t.contact_id:
            cr = await db.execute(select(Contact.name).where(Contact.id == t.contact_id))
            d["contact_name"] = cr.scalar()
        if t.assigned_to:
            ur = await db.execute(select(User.name).where(User.id == t.assigned_to))
            d["assigned_to_name"] = ur.scalar()
        items.append(d)

    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_task(db: AsyncSession, task_id: str) -> Optional[dict]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None
    d = _task_to_dict(task)
    if task.contact_id:
        cr = await db.execute(select(Contact.name).where(Contact.id == task.contact_id))
        d["contact_name"] = cr.scalar()
    if task.assigned_to:
        ur = await db.execute(select(User.name).where(User.id == task.assigned_to))
        d["assigned_to_name"] = ur.scalar()
    return d


async def create_task(db: AsyncSession, data: dict, current_user: User) -> dict:
    task = Task(
        id=str(uuid.uuid4()),
        title=data["title"],
        contact_id=data.get("contact_id"),
        assigned_to=data.get("assigned_to") or current_user.id,
        priority=data.get("priority", "mid"),
        due_date=data.get("due_date"),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def update_task(db: AsyncSession, task_id: str, data: dict) -> Optional[dict]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None

    for key in ("title", "contact_id", "assigned_to", "priority", "due_date"):
        if key in data and data[key] is not None:
            setattr(task, key, data[key])

    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def toggle_task(db: AsyncSession, task_id: str) -> Optional[dict]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None

    task.is_done = not task.is_done
    task.done_at = datetime.utcnow() if task.is_done else None
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True


def _task_to_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "contact_id": t.contact_id,
        "assigned_to": t.assigned_to,
        "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "is_done": t.is_done,
        "done_at": t.done_at.isoformat() if t.done_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "contact_name": None,
        "assigned_to_name": None,
    }
