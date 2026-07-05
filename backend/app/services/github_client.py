import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

GITHUB_API = "https://api.github.com"
_TRANSIENT_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
)


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise ValueError(f"GitHub OAuth exchange failed: {data}")
        return data["access_token"]


async def get_authenticated_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GITHUB_API}/user", headers=_auth_headers(access_token))
        resp.raise_for_status()
        return resp.json()


async def list_user_repos(access_token: str) -> list[dict]:
    """Returns repos where the user has admin rights (needed to create webhooks)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GITHUB_API}/user/repos",
            headers=_auth_headers(access_token),
            params={"per_page": 100, "affiliation": "owner"},
        )
        resp.raise_for_status()
        repos = resp.json()
        return [r for r in repos if r.get("permissions", {}).get("admin")]


@_TRANSIENT_RETRY
async def create_webhook(access_token: str, owner: str, repo: str) -> int:
    hook_url = f"{settings.BACKEND_PUBLIC_URL}/webhooks/github"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/hooks",
            headers=_auth_headers(access_token),
            json={
                "name": "web",
                "active": True,
                "events": ["issues", "pull_request", "push"],
                "config": {
                    "url": hook_url,
                    "content_type": "json",
                    "secret": settings.GITHUB_WEBHOOK_SECRET,
                },
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def delete_webhook(access_token: str, owner: str, repo: str, webhook_id: int) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.delete(
            f"{GITHUB_API}/repos/{owner}/{repo}/hooks/{webhook_id}",
            headers=_auth_headers(access_token),
        )
        # 404 just means it was already removed on GitHub's side; treat as success.
        if resp.status_code not in (204, 404):
            resp.raise_for_status()


@_TRANSIENT_RETRY
async def add_label(access_token: str, owner: str, repo: str, issue_number: int, label: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/labels",
            headers=_auth_headers(access_token),
            json={"labels": [label]},
        )
        resp.raise_for_status()


@_TRANSIENT_RETRY
async def post_comment(access_token: str, owner: str, repo: str, issue_number: int, body: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=_auth_headers(access_token),
            json={"body": body},
        )
        resp.raise_for_status()


def _auth_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
