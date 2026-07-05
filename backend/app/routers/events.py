import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Event, Repo, User
from app.schemas import EventOut
from app.services.event_processor import process_event

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    result = await db.execute(
        select(Event)
        .join(Repo)
        .options(selectinload(Event.actions), selectinload(Event.repo))
        .where(Repo.user_id == current_user.id)
        .order_by(Event.received_at.desc())
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()
    out = []
    for e in events:
        item = EventOut.model_validate(e)
        item.repo_full_name = e.repo.full_name
        out.append(item)
    return out


@router.post("/{event_id}/retry")
async def retry_event(
    event_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).join(Repo).where(Event.id == event_id, Repo.user_id == current_user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    background_tasks.add_task(process_event, event.id)
    return {"status": "retry_scheduled"}
