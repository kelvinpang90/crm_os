import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.activity import Activity
from app.models.user import User


VALID_STATUSES = {"潜在客户", "跟进中", "谈判中", "已成交", "已流失"}
VALID_PRIORITIES = {"高", "中", "低"}


async def list_contacts(
    db: AsyncSession,
    current_user: User,
    search: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict:
    query = select(Contact).where(Contact.deleted_at.is_(None))

    # Data permission
    if current_user.role == "sales":
        query = query.where(Contact.assigned_to == current_user.id)
    elif current_user.role == "manager":
        team_ids_q = select(User.id).where(User.manager_id == current_user.id)
        team_result = await db.execute(team_ids_q)
        team_ids = [r for r in team_result.scalars().all()]
        team_ids.append(current_user.id)
        query = query.where(Contact.assigned_to.in_(team_ids))

    # Filters
    if search:
        query = query.where(
            or_(
                Contact.name.ilike(f"%{search}%"),
                Contact.company.ilike(f"%{search}%"),
            )
        )
    if industry:
        query = query.where(Contact.industry == industry)
    if status:
        query = query.where(Contact.status == status)
    if priority:
        query = query.where(Contact.priority == priority)
    if assigned_to:
        query = query.where(Contact.assigned_to == assigned_to)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sort
    sort_col = getattr(Contact, sort_by, Contact.created_at)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    # Paginate
    page_size = min(page_size, 100)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    contacts = result.scalars().all()

    # Enrich with assigned_to_name
    data = []
    user_cache: dict[str, str] = {}
    for c in contacts:
        d = _contact_to_dict(c)
        if c.assigned_to:
            if c.assigned_to not in user_cache:
                u = await db.execute(select(User.name).where(User.id == c.assigned_to))
                user_cache[c.assigned_to] = u.scalar() or ""
            d["assigned_to_name"] = user_cache[c.assigned_to]
        data.append(d)

    return {"data": data, "total": total, "page": page, "page_size": page_size}


async def get_contact(db: AsyncSession, contact_id: str) -> Optional[dict]:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return None

    d = _contact_to_dict(contact)
    if contact.assigned_to:
        u = await db.execute(select(User.name).where(User.id == contact.assigned_to))
        d["assigned_to_name"] = u.scalar() or ""
    return d


async def create_contact(
    db: AsyncSession, data: dict, current_user: User
) -> dict:
    # Validate assigned_to
    if data.get("assigned_to"):
        await _validate_assigned_user(db, data["assigned_to"])
    elif current_user.role == "sales":
        data["assigned_to"] = current_user.id

    contact = Contact(
        id=str(uuid.uuid4()),
        name=data["name"],
        company=data.get("company"),
        industry=data.get("industry"),
        status=data.get("status", "潜在客户"),
        priority=data.get("priority", "中"),
        deal_value=Decimal(str(data.get("deal_value", "0.00"))),
        email=data.get("email"),
        phone=data.get("phone"),
        address=data.get("address"),
        notes=data.get("notes"),
        assigned_to=data.get("assigned_to"),
        tags=data.get("tags"),
    )
    db.add(contact)
    await db.flush()
    return _contact_to_dict(contact)


async def update_contact(
    db: AsyncSession, contact_id: str, data: dict, current_user: User
) -> Optional[dict]:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return None

    # Validate assigned_to change
    if "assigned_to" in data and data["assigned_to"]:
        await _validate_assigned_user(db, data["assigned_to"])

    old_status = contact.status
    for key, value in data.items():
        if value is not None and hasattr(contact, key):
            setattr(contact, key, value)
    contact.updated_at = datetime.utcnow()

    # Log status change
    if "status" in data and data["status"] != old_status:
        activity = Activity(
            id=str(uuid.uuid4()),
            contact_id=contact_id,
            user_id=current_user.id,
            type="状态变更",
            content=f"状态从「{old_status}」变更为「{data['status']}」",
            follow_date=datetime.utcnow(),
        )
        db.add(activity)

    await db.flush()
    return _contact_to_dict(contact)


async def soft_delete_contact(db: AsyncSession, contact_id: str) -> bool:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return False
    contact.deleted_at = datetime.utcnow()
    await db.flush()
    return True


async def import_contacts(db: AsyncSession, rows: list[dict], current_user: User) -> dict:
    """Process parsed Excel rows. Returns import result summary."""
    from app.models.user import User as UserModel

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    # Cache active users by email
    active_users = {}
    user_result = await db.execute(
        select(UserModel.id, UserModel.email).where(UserModel.is_active == True)
    )
    for uid, uemail in user_result.all():
        active_users[uemail] = uid

    for i, row in enumerate(rows, start=2):  # row 1 is header
        row_errors = []
        name = (row.get("name") or "").strip()
        if not name:
            row_errors.append({"row": i, "field": "name", "message": "姓名不能为空"})

        email = (row.get("email") or "").strip()
        if email and "@" not in email:
            row_errors.append({"row": i, "field": "email", "message": "邮箱格式不正确"})

        status = (row.get("status") or "").strip() or "潜在客户"
        if status not in VALID_STATUSES:
            row_errors.append({"row": i, "field": "status", "message": f"无效状态: {status}"})
            status = "潜在客户"

        priority = (row.get("priority") or "").strip() or "中"
        if priority not in VALID_PRIORITIES:
            priority = "中"

        assigned_email = (row.get("assigned_to_email") or "").strip()
        assigned_user_id = None
        if assigned_email:
            assigned_user_id = active_users.get(assigned_email)
            if not assigned_user_id:
                row_errors.append({"row": i, "field": "assigned_to_email", "message": "销售账号不存在或已停用"})

        if row_errors:
            errors.extend(row_errors)
            skipped += 1
            continue

        deal_value = Decimal(str(row.get("deal_value") or "0"))
        tags_str = (row.get("tags") or "").strip()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        contact_id = (row.get("id") or "").strip()
        if contact_id:
            # Update existing
            existing = await db.execute(
                select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
            )
            contact = existing.scalar_one_or_none()
            if not contact:
                errors.append({"row": i, "field": "id", "message": f"客户ID不存在: {contact_id}"})
                skipped += 1
                continue

            if name:
                contact.name = name
            if row.get("company"):
                contact.company = row["company"]
            if row.get("industry"):
                contact.industry = row["industry"]
            if row.get("status"):
                contact.status = status
            if row.get("priority"):
                contact.priority = priority
            if row.get("deal_value"):
                contact.deal_value = deal_value
            if email:
                contact.email = email
            if row.get("phone"):
                contact.phone = row["phone"]
            if row.get("address"):
                contact.address = row["address"]
            if row.get("notes"):
                contact.notes = row["notes"]
            if tags:
                contact.tags = tags
            if assigned_user_id:
                contact.assigned_to = assigned_user_id
            contact.updated_at = datetime.utcnow()
            updated += 1
        else:
            # Insert new
            contact = Contact(
                id=str(uuid.uuid4()),
                name=name,
                company=row.get("company"),
                industry=row.get("industry"),
                status=status,
                priority=priority,
                deal_value=deal_value,
                email=email or None,
                phone=row.get("phone"),
                address=row.get("address"),
                notes=row.get("notes"),
                tags=tags,
                assigned_to=assigned_user_id or (current_user.id if current_user.role == "sales" else None),
            )
            db.add(contact)
            inserted += 1

    await db.flush()
    return {
        "total": len(rows),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


async def _validate_assigned_user(db: AsyncSession, user_id: str) -> None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="负责销售不存在或已停用")


def _contact_to_dict(contact: Contact) -> dict:
    return {
        "id": contact.id,
        "name": contact.name,
        "company": contact.company,
        "industry": contact.industry,
        "status": contact.status,
        "priority": contact.priority,
        "deal_value": float(contact.deal_value),
        "email": contact.email,
        "phone": contact.phone,
        "address": contact.address,
        "notes": contact.notes,
        "assigned_to": contact.assigned_to,
        "assigned_to_name": None,
        "last_contact": contact.last_contact.isoformat() if contact.last_contact else None,
        "tags": contact.tags,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
        "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
    }
