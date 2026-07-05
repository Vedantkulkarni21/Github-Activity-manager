import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rule

# Fallback used only when a repo's owner has configured zero rules at all,
# so the bot does something sensible out of the box. Any user-configured
# rule always takes priority over this.
DEFAULT_FALLBACK_RULE = {
    "event_type": "issues",
    "match_field": "title",
    "match_type": "contains",
    "match_value": "bug",
    "action_add_label": "bug",
    "action_comment_template": "Thanks for the report! This was auto-labeled `bug` by the repo bot.",
    "action_slack_notify": True,
}


def _field_value(payload: dict, event_type: str, field: str) -> str:
    obj_key = "issue" if event_type == "issues" else "pull_request"
    obj = payload.get(obj_key, {}) or {}
    return (obj.get(field) or "") if field in ("title", "body") else ""


def _matches(rule_match_type: str, haystack: str, needle: str) -> bool:
    haystack = (haystack or "").lower()
    needle = (needle or "").lower()
    if rule_match_type == "contains":
        return needle in haystack
    if rule_match_type == "equals":
        return haystack == needle
    return False


async def get_matching_rules(
    db: AsyncSession, *, user_id: uuid.UUID, repo_id: uuid.UUID, event_type: str, payload: dict
) -> list[Rule]:
    result = await db.execute(
        select(Rule).where(
            Rule.user_id == user_id,
            Rule.event_type == event_type,
            Rule.is_active.is_(True),
            or_(Rule.repo_id.is_(None), Rule.repo_id == repo_id),
        )
    )
    candidate_rules = list(result.scalars().all())

    matched = [
        r for r in candidate_rules
        if _matches(r.match_type, _field_value(payload, event_type, r.match_field), r.match_value)
    ]

    if matched:
        return matched

    # No configured rule matched (or none exist) -- fall back to the built-in default,
    # wrapped in a lightweight object so callers can treat it uniformly.
    if event_type == DEFAULT_FALLBACK_RULE["event_type"] and _matches(
        DEFAULT_FALLBACK_RULE["match_type"],
        _field_value(payload, event_type, DEFAULT_FALLBACK_RULE["match_field"]),
        DEFAULT_FALLBACK_RULE["match_value"],
    ):
        return [_FallbackRule()]

    return []


class _FallbackRule:
    """Duck-types the subset of Rule attributes event_processor needs."""
    id = None
    action_add_label = DEFAULT_FALLBACK_RULE["action_add_label"]
    action_comment_template = DEFAULT_FALLBACK_RULE["action_comment_template"]
    action_slack_notify = DEFAULT_FALLBACK_RULE["action_slack_notify"]
