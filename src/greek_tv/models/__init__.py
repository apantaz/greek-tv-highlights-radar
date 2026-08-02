from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, Field, computed_field, field_validator


class Broadcast(BaseModel):
    channel: str = Field(min_length=1)
    title: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
    description: str | None = None
    source_url: str = Field(min_length=1)
    retrieved_at: datetime

    @field_validator("channel", "title")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator("starts_at", "ends_at", "retrieved_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return value

    @computed_field
    @property
    def broadcast_id(self) -> str:
        identity = f"{self.channel}|{self.starts_at.isoformat()}|{self.title}|{self.source_url}"
        return sha256(identity.encode()).hexdigest()


class IngestionStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IngestionRun(BaseModel):
    run_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    schedule_date: date
    source_url: str = Field(min_length=1)
    started_at: datetime
    completed_at: datetime | None = None
    status: IngestionStatus
    records_parsed: int = Field(default=0, ge=0)
    snapshot_path: str | None = None
    error_message: str | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def require_run_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return value


__all__ = ["Broadcast", "IngestionRun", "IngestionStatus"]
