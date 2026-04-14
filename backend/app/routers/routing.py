from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.routing import RoutingRuleCreate, RoutingRuleUpdate, ReorderRequest
from app.services import routing_service
from app.utils.response import ok, fail

router = APIRouter()


@router.get("")
async def list_rules(
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await routing_service.list_rules(db)
    return ok(data=data)


@router.post("")
async def create_rule(
    body: RoutingRuleCreate,
    admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await routing_service.create_rule(db, body.model_dump(), admin.id)
    return ok(data=data)


@router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    body: RoutingRuleUpdate,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await routing_service.update_rule(
        db, rule_id, body.model_dump(exclude_unset=True)
    )
    if not data:
        return fail(message="规则不存在", code=404)
    return ok(data=data)


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await routing_service.delete_rule(db, rule_id)
    if not success:
        return fail(message="规则不存在", code=404)
    return ok(message="删除成功")


@router.patch("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: str,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await routing_service.toggle_rule(db, rule_id)
    if not data:
        return fail(message="规则不存在", code=404)
    return ok(data=data)


@router.patch("/reorder")
async def reorder_rules(
    body: ReorderRequest,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await routing_service.reorder_rules(
        db, [item.model_dump() for item in body.rules]
    )
    return ok(data=data)
