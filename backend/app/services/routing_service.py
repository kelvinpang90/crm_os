import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.routing_rule import RoutingRule
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.user import User


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def list_rules(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(RoutingRule).order_by(RoutingRule.priority.asc())
    )
    return [_rule_to_dict(r) for r in result.scalars().all()]


async def create_rule(db: AsyncSession, data: dict, created_by: str) -> dict:
    rule = RoutingRule(
        id=str(uuid.uuid4()),
        name=data["name"],
        strategy=data["strategy"],
        conditions=data.get("conditions"),
        target_users=data.get("target_users", []),
        priority=data.get("priority", 0),
        is_active=data.get("is_active", True),
        created_by=created_by,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return _rule_to_dict(rule)


async def update_rule(db: AsyncSession, rule_id: str, data: dict) -> Optional[dict]:
    result = await db.execute(select(RoutingRule).where(RoutingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return None

    for key in ("name", "strategy", "conditions", "target_users", "priority", "is_active"):
        if key in data and data[key] is not None:
            setattr(rule, key, data[key])

    await db.commit()
    await db.refresh(rule)
    return _rule_to_dict(rule)


async def delete_rule(db: AsyncSession, rule_id: str) -> bool:
    result = await db.execute(select(RoutingRule).where(RoutingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return False
    await db.delete(rule)
    await db.commit()
    return True


async def toggle_rule(db: AsyncSession, rule_id: str) -> Optional[dict]:
    result = await db.execute(select(RoutingRule).where(RoutingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return None
    rule.is_active = not rule.is_active
    await db.commit()
    await db.refresh(rule)
    return _rule_to_dict(rule)


async def reorder_rules(db: AsyncSession, items: list[dict]) -> list[dict]:
    for item in items:
        result = await db.execute(
            select(RoutingRule).where(RoutingRule.id == item["id"])
        )
        rule = result.scalar_one_or_none()
        if rule:
            rule.priority = item["priority"]
    await db.commit()
    return await list_rules(db)


# ---------------------------------------------------------------------------
# Auto-assignment
# ---------------------------------------------------------------------------

async def assign_contact(db: AsyncSession, contact: Contact) -> Optional[str]:
    """Determine the best sales rep to assign a contact to.
    Returns user_id or None."""

    rules = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.is_active == True)
        .order_by(RoutingRule.priority.asc())
    )

    for rule in rules.scalars().all():
        target_ids = rule.target_users or []
        if not target_ids:
            continue

        # Filter to active users only
        active_result = await db.execute(
            select(User.id).where(
                User.id.in_(target_ids),
                User.is_active == True,
                User.role == "sales",
            )
        )
        eligible = [r for r in active_result.scalars().all()]
        if not eligible:
            continue

        if rule.strategy == "workload":
            user_id = await _strategy_workload(db, eligible)
        elif rule.strategy == "region":
            user_id = await _strategy_region(db, contact, rule.conditions, eligible)
        elif rule.strategy == "win_rate":
            user_id = await _strategy_win_rate(db, eligible)
        else:
            continue

        if user_id:
            return user_id

    # Fallback: first active sales
    fallback = await db.execute(
        select(User.id)
        .where(User.is_active == True, User.role == "sales")
        .order_by(User.created_at.asc())
        .limit(1)
    )
    return fallback.scalar_one_or_none()


async def _strategy_workload(db: AsyncSession, eligible: list[str]) -> Optional[str]:
    """Assign to sales with fewest active contacts."""
    result = await db.execute(
        select(
            User.id,
            func.count(Contact.id).label("cnt"),
        )
        .outerjoin(
            Contact,
            (Contact.assigned_to == User.id) & Contact.deleted_at.is_(None),
        )
        .where(User.id.in_(eligible))
        .group_by(User.id)
        .order_by(func.count(Contact.id).asc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


async def _strategy_region(
    db: AsyncSession,
    contact: Contact,
    conditions: Optional[dict],
    eligible: list[str],
) -> Optional[str]:
    """Match contact address/company to region keywords."""
    if not conditions:
        return None

    keywords = conditions.get("keywords", [])
    if not keywords:
        return None

    # Check if contact's address or company matches any keyword
    text_to_match = " ".join(
        filter(None, [contact.address, contact.company, contact.name])
    )

    for kw in keywords:
        if kw in text_to_match:
            # Region matches — use workload among eligible
            return await _strategy_workload(db, eligible)

    return None


async def _strategy_win_rate(db: AsyncSession, eligible: list[str]) -> Optional[str]:
    """Assign to sales with highest win rate in last 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(
            Deal.assigned_to,
            func.count(case((Deal.status == "won", 1))).label("won"),
            func.count(Deal.id).label("total"),
        )
        .where(
            Deal.deleted_at.is_(None),
            Deal.assigned_to.in_(eligible),
            Deal.created_at >= cutoff,
        )
        .group_by(Deal.assigned_to)
    )
    rows = result.all()

    best_id = None
    best_rate = -1.0
    for uid, won, total in rows:
        rate = won / total if total > 0 else 0
        if rate > best_rate:
            best_rate = rate
            best_id = uid

    # Users with no deals yet — give them a chance
    if best_id is None and eligible:
        return eligible[0]

    return best_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rule_to_dict(r: RoutingRule) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "is_active": r.is_active,
        "priority": r.priority,
        "strategy": r.strategy,
        "conditions": r.conditions,
        "target_users": r.target_users,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
