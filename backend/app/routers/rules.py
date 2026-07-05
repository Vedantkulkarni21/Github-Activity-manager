import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Repo, Rule, User
from app.schemas import RuleIn, RuleOut

router = APIRouter(prefix="/api/rules", tags=["rules"])


async def _assert_owns_repo(db: AsyncSession, user_id: uuid.UUID, repo_id: uuid.UUID | None):
    if repo_id is None:
        return
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.user_id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You don't own that repo")


@router.get("", response_model=list[RuleOut])
async def list_rules(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.user_id == current_user.id).order_by(Rule.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=RuleOut)
async def create_rule(body: RuleIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _assert_owns_repo(db, current_user.id, body.repo_id)
    rule = Rule(user_id=current_user.id, **body.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: uuid.UUID, body: RuleIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id, Rule.user_id == current_user.id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await _assert_owns_repo(db, current_user.id, body.repo_id)

    for field, value in body.model_dump().items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id, Rule.user_id == current_user.id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted"}
