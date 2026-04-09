from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.notification_preference import NotificationPreference
from src.shared.schemas.notification_preference import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)


def get_or_create_notification_preference(
    session: Session,
    *,
    user_id: UUID,
) -> NotificationPreferenceResponse:
    """
    Return the user's notification preferences, creating a default row if absent.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - Default row semantics are deterministic and safe.
    """
    preference = _get_or_create_notification_preference_model(
        session=session,
        user_id=user_id,
    )
    return _build_notification_preference_response(preference)


def update_notification_preference(
    session: Session,
    *,
    user_id: UUID,
    payload: NotificationPreferenceUpdateRequest,
) -> NotificationPreferenceResponse:
    """
    Update the user's persisted notification preferences.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - Only explicitly provided fields are updated.
    """
    preference = _get_or_create_notification_preference_model(
        session=session,
        user_id=user_id,
    )

    if "email_enabled" in payload.model_fields_set:
        preference.email_enabled = _require_boolean_value(
            field_name="email_enabled",
            value=payload.email_enabled,
        )

    if "whatsapp_enabled" in payload.model_fields_set:
        preference.whatsapp_enabled = _require_boolean_value(
            field_name="whatsapp_enabled",
            value=payload.whatsapp_enabled,
        )

    if "whatsapp_phone_e164" in payload.model_fields_set:
        preference.whatsapp_phone_e164 = payload.whatsapp_phone_e164

    if "daily_brief_enabled" in payload.model_fields_set:
        preference.daily_brief_enabled = _require_boolean_value(
            field_name="daily_brief_enabled",
            value=payload.daily_brief_enabled,
        )

    if "instant_alert_enabled" in payload.model_fields_set:
        preference.instant_alert_enabled = _require_boolean_value(
            field_name="instant_alert_enabled",
            value=payload.instant_alert_enabled,
        )

    if "preferred_language" in payload.model_fields_set:
        if payload.preferred_language is None:
            preference.preferred_language = "auto"
        else:
            preference.preferred_language = payload.preferred_language

    session.flush()
    return _build_notification_preference_response(preference)


def _get_or_create_notification_preference_model(
    *,
    session: Session,
    user_id: UUID,
) -> NotificationPreference:
    """Load a user's preference row or create a default one."""
    preference = session.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    ).scalar_one_or_none()

    if preference is None:
        preference = NotificationPreference(user_id=user_id)
        session.add(preference)
        session.flush()

    return preference


def _require_boolean_value(
    *,
    field_name: str,
    value: bool | None,
) -> bool:
    """Reject explicit null for boolean preference updates."""
    if value is None:
        raise ValueError(f"{field_name} must not be null")
    return value


def _build_notification_preference_response(
    preference: NotificationPreference,
) -> NotificationPreferenceResponse:
    """Build a normalized response from a notification-preference model."""
    return NotificationPreferenceResponse(
        user_id=preference.user_id,
        email_enabled=preference.email_enabled,
        whatsapp_enabled=preference.whatsapp_enabled,
        whatsapp_phone_e164=preference.whatsapp_phone_e164,
        daily_brief_enabled=preference.daily_brief_enabled,
        instant_alert_enabled=preference.instant_alert_enabled,
        preferred_language=preference.preferred_language,
    )
