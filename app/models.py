from enum import StrEnum

from pydantic import BaseModel, Field


class Priority(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Status(StrEnum):
    new = "new"
    investigating = "investigating"
    escalated = "escalated"
    resolved = "resolved"


class CaseCreate(BaseModel):
    title: str = Field(min_length=5, max_length=140)
    service: str = Field(min_length=2, max_length=80)
    category: str = Field(default="Application", min_length=2, max_length=40)
    owner: str = Field(min_length=2, max_length=80)
    priority: Priority
    impact: str = Field(min_length=5, max_length=220)


class CaseUpdate(BaseModel):
    status: Status
    resolution_note: str = Field(min_length=8, max_length=500)


class Case(BaseModel):
    id: int
    external_id: str | None = None
    title: str
    service: str
    category: str = "Application"
    owner: str
    priority: Priority
    status: Status
    impact: str
    opened_at: str
    updated_at: str
    sla_minutes: int
    resolution_note: str | None = None


class EventCreate(BaseModel):
    stage: str = Field(pattern="^(intake|reproduce|analyze|isolate|escalate|validate|document)$")
    detail: str = Field(min_length=8, max_length=500)
