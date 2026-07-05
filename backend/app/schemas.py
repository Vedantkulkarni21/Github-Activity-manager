import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    avatar_url: Optional[str] = None


class RepoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_login: str
    name: str
    full_name: str
    is_active: bool
    created_at: datetime


class RepoConnectIn(BaseModel):
    full_name: str  # e.g. "octocat/hello-world"


class AvailableRepoOut(BaseModel):
    full_name: str
    private: bool
    already_connected: bool


class RuleIn(BaseModel):
    repo_id: Optional[uuid.UUID] = None
    event_type: str  # issues | pull_request
    match_field: str  # title | body
    match_type: str = "contains"
    match_value: str
    action_add_label: Optional[str] = None
    action_comment_template: Optional[str] = None
    action_slack_notify: bool = True
    is_active: bool = True


class RuleOut(RuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime


class ActionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    action_type: str
    status: str
    detail: Optional[str] = None
    attempted_at: datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    action: Optional[str] = None
    status: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    error_detail: Optional[str] = None
    repo_full_name: Optional[str] = None
    actions: list[ActionLogOut] = []
