from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from src.api.services.auth_service import register_user
from src.db.models.notification_preference import NotificationPreference
from src.db.session import get_session_factory
from src.jobs.verify_match_recent_tenders_job import TEST_PASSWORD
from src.notifications.notification_preference_service import (
    get_or_create_notification_preference,
    update_notification_preference,
)
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.notification_preference import (
    NotificationPreferenceUpdateRequest,
)


def run() -> None:
    """
    Perform a persisted verification of the notification-preference service.

    This script verifies:
        - default row creation works
        - updates persist correctly
        - preferred_language persists correctly
        - WhatsApp fields persist correctly
    """
    session_factory = get_session_factory()
    unique_marker = f"utw-pref-{uuid4().hex}"
    unique_email = f"{unique_marker}@example.com"

    with session_factory() as session:
        user = register_user(
            session=session,
            payload=SignupRequest(
                email=unique_email,
                password=TEST_PASSWORD,
            ),
        )

        created_preference = get_or_create_notification_preference(
            session,
            user_id=user.id,
        )

        updated_preference = update_notification_preference(
            session,
            user_id=user.id,
            payload=NotificationPreferenceUpdateRequest(
                email_enabled=False,
                whatsapp_enabled=True,
                whatsapp_phone_e164="+971501234567",
                daily_brief_enabled=False,
                instant_alert_enabled=True,
                preferred_language="ar",
            ),
        )
        session.commit()

    with session_factory() as session:
        persisted_preference = session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user.id)
        ).scalar_one_or_none()

    if persisted_preference is None:
        raise ValueError("expected notification preference row to persist")

    if created_preference.email_enabled is not True:
        raise ValueError("expected default email_enabled=True")

    if created_preference.whatsapp_enabled is not False:
        raise ValueError("expected default whatsapp_enabled=False")

    if created_preference.daily_brief_enabled is not True:
        raise ValueError("expected default daily_brief_enabled=True")

    if created_preference.preferred_language != "auto":
        raise ValueError("expected default preferred_language='auto'")

    if updated_preference.email_enabled is not False:
        raise ValueError("expected email_enabled=False after update")

    if updated_preference.whatsapp_enabled is not True:
        raise ValueError("expected whatsapp_enabled=True after update")

    if updated_preference.whatsapp_phone_e164 != "+971501234567":
        raise ValueError("expected whatsapp_phone_e164 to persist correctly")

    if updated_preference.daily_brief_enabled is not False:
        raise ValueError("expected daily_brief_enabled=False after update")

    if updated_preference.instant_alert_enabled is not True:
        raise ValueError("expected instant_alert_enabled=True after update")

    if updated_preference.preferred_language != "ar":
        raise ValueError("expected preferred_language='ar' after update")

    if persisted_preference.email_enabled is not False:
        raise ValueError("expected persisted email_enabled=False after update")

    if persisted_preference.whatsapp_enabled is not True:
        raise ValueError("expected persisted whatsapp_enabled=True after update")

    if persisted_preference.whatsapp_phone_e164 != "+971501234567":
        raise ValueError("expected persisted whatsapp_phone_e164 to match update")

    if persisted_preference.daily_brief_enabled is not False:
        raise ValueError("expected persisted daily_brief_enabled=False after update")

    if persisted_preference.instant_alert_enabled is not True:
        raise ValueError("expected persisted instant_alert_enabled=True after update")

    if persisted_preference.preferred_language != "ar":
        raise ValueError("expected persisted preferred_language='ar' after update")

    print(f"verify_notification_preference_user_email={unique_email}")
    print(
        "verify_notification_preference_default_email_enabled="
        f"{created_preference.email_enabled}"
    )
    print(
        "verify_notification_preference_default_whatsapp_enabled="
        f"{created_preference.whatsapp_enabled}"
    )
    print(
        "verify_notification_preference_default_daily_brief_enabled="
        f"{created_preference.daily_brief_enabled}"
    )
    print(
        "verify_notification_preference_default_preferred_language="
        f"{created_preference.preferred_language}"
    )
    print(
        "verify_notification_preference_updated_email_enabled="
        f"{updated_preference.email_enabled}"
    )
    print(
        "verify_notification_preference_updated_whatsapp_enabled="
        f"{updated_preference.whatsapp_enabled}"
    )
    print(
        "verify_notification_preference_updated_whatsapp_phone_e164="
        f"{updated_preference.whatsapp_phone_e164}"
    )
    print(
        "verify_notification_preference_updated_daily_brief_enabled="
        f"{updated_preference.daily_brief_enabled}"
    )
    print(
        "verify_notification_preference_updated_instant_alert_enabled="
        f"{updated_preference.instant_alert_enabled}"
    )
    print(
        "verify_notification_preference_updated_preferred_language="
        f"{updated_preference.preferred_language}"
    )


if __name__ == "__main__":
    run()
