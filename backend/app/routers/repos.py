import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Repo, User
from app.schemas import AvailableRepoOut, RepoConnectIn, RepoOut
from app.security import decrypt_secret
from app.services import github_client

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("/available", response_model=list[AvailableRepoOut])
async def available_repos(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Repos the user owns/admins on GitHub, so they can pick one to connect."""
    access_token = decrypt_secret(current_user.access_token_encrypted)
    gh_repos = await github_client.list_user_repos(access_token)

    result = await db.execute(select(Repo.full_name).where(Repo.user_id == current_user.id, Repo.is_active.is_(True)))
    connected = {row[0] for row in result.all()}

    return [
        AvailableRepoOut(full_name=r["full_name"], private=r["private"], already_connected=r["full_name"] in connected)
        for r in gh_repos
    ]


@router.get("", response_model=list[RepoOut])
async def list_connected_repos(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repo).where(Repo.user_id == current_user.id, Repo.is_active.is_(True)))
    return result.scalars().all()


@router.post("", response_model=RepoOut)
async def connect_repo(body: RepoConnectIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if "/" not in body.full_name:
        raise HTTPException(status_code=400, detail="full_name must be 'owner/repo'")
    owner_login, name = body.full_name.split("/", 1)
    access_token = decrypt_secret(current_user.access_token_encrypted)

    gh_repos = await github_client.list_user_repos(access_token)
    match = next((r for r in gh_repos if r["full_name"] == body.full_name), None)
    if not match:
        raise HTTPException(status_code=403, detail="Repo not found or you don't have admin access to it")

    webhook_id = await github_client.create_webhook(access_token, owner_login, name)

    repo = Repo(
        user_id=current_user.id,
        github_repo_id=match["id"],
        owner_login=owner_login,
        name=name,
        full_name=body.full_name,
        webhook_id=webhook_id,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return repo


@router.delete("/{repo_id}")
async def disconnect_repo(repo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repo).where(Repo.id == repo_id, Repo.user_id == current_user.id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    access_token = decrypt_secret(current_user.access_token_encrypted)
    if repo.webhook_id:
        await github_client.delete_webhook(access_token, repo.owner_login, repo.name, repo.webhook_id)

    repo.is_active = False
    await db.commit()
    return {"status": "disconnected"}
