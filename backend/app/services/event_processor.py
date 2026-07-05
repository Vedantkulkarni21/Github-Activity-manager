import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import Event, Repo, User, ActionLog
from app.security import decrypt_secret
from app.services import github_client, slack_client
from app.services.rule_engine import get_matching_rules


def _issue_number(payload: dict, event_type: str) -> int | None:
    key = "issue" if event_type == "issues" else "pull_request"
    obj = payload.get(key) or {}
    return obj.get("number")


async def process_event(event_id: uuid.UUID) -> None:
    """Runs in a background task so the webhook endpoint can ACK GitHub
    immediately (avoids delivery timeouts/retries piling up). Each action is
    isolated in its own try/except so a single failure (e.g. Slack down)
    doesn't stop the other actions or corrupt the event's overall status."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Event).options(selectinload(Event.repo).selectinload(Repo.owner)).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            return

        event.status = "processing"
        await db.commit()

        repo = event.repo
        user: User = repo.owner
        had_failure = False

        try:
            access_token = decrypt_secret(user.access_token_encrypted)
            rules = await get_matching_rules(
                db,
                user_id=user.id,
                repo_id=repo.id,
                event_type=event.event_type,
                payload=event.payload,
            )
            issue_number = _issue_number(event.payload, event.event_type)

            for rule in rules:
                if rule.action_add_label and issue_number is not None:
                    had_failure |= not await _run_action(
                        db, event.id, getattr(rule, "id", None), "add_label",
                        github_client.add_label(access_token, repo.owner_login, repo.name, issue_number, rule.action_add_label),
                    )

                if rule.action_comment_template and issue_number is not None:
                    had_failure |= not await _run_action(
                        db, event.id, getattr(rule, "id", None), "post_comment",
                        github_client.post_comment(access_token, repo.owner_login, repo.name, issue_number, rule.action_comment_template),
                    )

                if rule.action_slack_notify:
                    title = (event.payload.get("issue") or event.payload.get("pull_request") or {}).get("title", "")
                    text = f":robot_face: *{repo.full_name}* — {event.event_type}.{event.action}: _{title}_"
                    had_failure |= not await _run_action(
                        db, event.id, getattr(rule, "id", None), "slack_notify",
                        slack_client.send_notification(text),
                    )

            event.status = "processed_with_errors" if had_failure else "processed"
        except Exception as exc:  # noqa: BLE001 - top-level safety net, never lose the event silently
            event.status = "failed"
            event.error_detail = str(exc)[:2000]
        finally:
            event.processed_at = datetime.now(timezone.utc)
            await db.commit()


async def _run_action(db, event_id: uuid.UUID, rule_id, action_type: str, coro) -> bool:
    """Executes one action coroutine, logs the outcome, and swallows the
    exception so sibling actions still run. Returns True on success."""
    try:
        await coro
        db.add(ActionLog(event_id=event_id, rule_id=rule_id, action_type=action_type, status="success"))
        return True
    except Exception as exc:  # noqa: BLE001
        db.add(ActionLog(event_id=event_id, rule_id=rule_id, action_type=action_type, status="failed", detail=str(exc)[:2000]))
        return False
