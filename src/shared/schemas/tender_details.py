from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


TenderDetailsTimelineKind = Literal[
    'source_checked',
    'tender_detected',
    'match_created',
    'instant_alert_sent',
    'daily_brief_sent',
]


class TenderDetailsNotificationState(BaseModel):
    """User-specific delivery state for one tender."""

    match_created_at: datetime | None = None
    matched_keywords: list[str] = Field(default_factory=list)
    instant_alert_sent: bool = False
    instant_alert_sent_at: datetime | None = None
    daily_brief_sent: bool = False
    daily_brief_sent_at: datetime | None = None


class TenderDetailsTimelineItem(BaseModel):
    """One tender timeline entry backed by persisted facts."""

    id: str
    kind: TenderDetailsTimelineKind
    status: str
    timestamp: datetime
    title: str
    summary: str | None = None


class TenderDetailsResponse(BaseModel):
    """Authenticated tender details payload for the user-facing detail page."""

    id: UUID
    title: str
    issuing_entity: str
    source_id: UUID
    source_name: str | None = None
    source_url: str
    closing_date: datetime
    opening_date: datetime | None = None
    published_at: datetime | None = None
    tender_ref: str | None = None
    category: str | None = None
    ai_summary: str | None = None
    matched_keywords: list[str] = Field(default_factory=list)
    notification_state: TenderDetailsNotificationState
    activity_timeline: list[TenderDetailsTimelineItem] = Field(default_factory=list)
