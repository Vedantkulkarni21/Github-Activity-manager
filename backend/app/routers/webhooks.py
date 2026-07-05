from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event, Repo
from app.security import verify_github_signature
from app.services.event_processor import process_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    raw_body = await request.body()

    # 1. Reject forged/tampered requests outright.
    if not verify_github_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not x_github_event or not x_github_delivery:
        raise HTTPException(status_code=400, detail="Missing GitHub event headers")

    payload = await request.json()

    repo_gh_id = (payload.get("repository") or {}).get("id")
    result = await db.execute(select(Repo).where(Repo.github_repo_id == repo_gh_id, Repo.is_active.is_(True)))
    repo = result.scalar_one_or_none()
    if not repo:
        # Not one of our connected/active repos (e.g. webhook left over after disconnect).
        # Ack with 200 so GitHub doesn't keep retrying a delivery we'll never use.
        return {"status": "ignored", "reason": "repo not connected"}

    # 2. Idempotency: if we've already recorded this exact delivery, don't process it twice.
    existing = await db.execute(select(Event).where(Event.delivery_id == x_github_delivery))
    if existing.scalar_one_or_none():
        return {"status": "duplicate", "delivery_id": x_github_delivery}

    event = Event(
        repo_id=repo.id,
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        action=payload.get("action"),
        payload=payload,
        status="received",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # 3. ACK immediately, do the real work (GitHub/Slack calls) after responding,
    # so a slow downstream call can't cause GitHub to time out and retry the delivery.
    background_tasks.add_task(process_event, event.id)

    return {"status": "accepted", "event_id": str(event.id)}
