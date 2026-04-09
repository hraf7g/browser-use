from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationDeliveryHistoryItem(BaseModel):
    """Safe notification-delivery history item returned to end users."""

    id: UUID
    delivery_type: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=32)
    attempted_at: datetime
    sent_at: datetime | None = None
    match_count: int | None = Field(default=None, ge=0)
    failure_reason: str | None = Field(default=None, max_length=2000)


class NotificationDeliveryHistoryResponse(BaseModel):
    """Paginated notification-delivery history response."""

    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[NotificationDeliveryHistoryItem]
