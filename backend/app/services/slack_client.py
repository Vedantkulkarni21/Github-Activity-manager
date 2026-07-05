import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

_TRANSIENT_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
)


@_TRANSIENT_RETRY
async def send_notification(text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": text})
        resp.raise_for_status()
