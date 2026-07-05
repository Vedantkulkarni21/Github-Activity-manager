import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repos: Mapped[list["Repo"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    rules: Mapped[list["Rule"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Repo(Base):
    __tablename__ = "repos"
    __table_args__ = (UniqueConstraint("github_repo_id", name="uq_repo_github_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    github_repo_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    owner_login: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    webhook_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="repos")
    events: Mapped[list["Event"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    rules: Mapped[list["Rule"]] = relationship(back_populates="repo")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("delivery_id", name="uq_event_delivery_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"))
    delivery_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # issues, pull_request, push
    action: Mapped[str] = mapped_column(String, nullable=True)  # opened, closed, synchronize...
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, default="received")  # received, processing, processed, processed_with_errors, failed
    error_detail: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    repo: Mapped["Repo"] = relationship(back_populates="events")
    actions: Mapped[list["ActionLog"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    repo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), nullable=True)  # null = applies to all of the user's repos

    event_type: Mapped[str] = mapped_column(String, nullable=False)  # issues, pull_request
    match_field: Mapped[str] = mapped_column(String, nullable=False)  # title, body
    match_type: Mapped[str] = mapped_column(String, default="contains")  # contains (extend later: equals/regex)
    match_value: Mapped[str] = mapped_column(String, nullable=False)

    action_add_label: Mapped[str] = mapped_column(String, nullable=True)
    action_comment_template: Mapped[str] = mapped_column(Text, nullable=True)
    action_slack_notify: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="rules")
    repo: Mapped["Repo"] = relationship(back_populates="rules")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True)

    action_type: Mapped[str] = mapped_column(String, nullable=False)  # add_label, post_comment, slack_notify
    status: Mapped[str] = mapped_column(String, nullable=False)  # success, failed
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped["Event"] = relationship(back_populates="actions")
