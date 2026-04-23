from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from src.scripts.smoke_validation_dataset import get_smoke_validation_dataset

BASE_URL = 'http://127.0.0.1:8000'

_cookie_jar = http.cookiejar.CookieJar()
_cookie_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cookie_jar)
)


@dataclass(frozen=True)
class CheckResult:
    """One verification check against the smoke-validation dataset."""

    name: str
    passed: bool
    details: str


def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    use_session_cookies: bool = False,
) -> tuple[int, dict[str, Any] | str]:
    request = urllib.request.Request(
        url=f'{BASE_URL}{path}',
        method=method,
        headers={'Content-Type': 'application/json'} if json_body is not None else {},
        data=None if json_body is None else json.dumps(json_body).encode('utf-8'),
    )

    try:
        opener = _cookie_opener if use_session_cookies else urllib.request
        open_request = opener.open if use_session_cookies else opener.urlopen
        with open_request(request) as response:
            body = response.read().decode('utf-8')
            return response.getcode(), _parse_body(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8')
        return exc.code, _parse_body(body)


def _parse_body(body: str) -> dict[str, Any] | str:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def run() -> int:
    """Verify that the smoke-validation dataset supports release-grade checks."""
    dataset = get_smoke_validation_dataset()
    if dataset is None:
        print(
            'verify_smoke_validation_dataset_error='
            'dataset not found; run src.scripts.seed_smoke_validation_data first'
        )
        return 1

    results: list[CheckResult] = []

    login_status, login_body = _request(
        'POST',
        '/auth/login',
        json_body={
            'email': dataset.user_email,
            'password': dataset.user_password,
        },
        use_session_cookies=True,
    )
    results.append(
        CheckResult(
            name='login_smoke_validation_user',
            passed=login_status == 200,
            details='' if login_status == 200 else f'response={login_body}',
        )
    )
    if login_status != 200:
        _print_results(results)
        return 1

    search_query = urllib.parse.quote(dataset.tender_ref)
    tender_list_status, tender_list_body = _request(
        'GET',
        f'/tenders?limit=20&search={search_query}',
        use_session_cookies=True,
    )
    list_passed = False
    list_details = f'response={tender_list_body}'
    if tender_list_status == 200 and isinstance(tender_list_body, dict):
        items = tender_list_body.get('items', [])
        tender_ids = {item.get('id') for item in items if isinstance(item, dict)}
        list_passed = str(dataset.tender_id) in tender_ids
        list_details = (
            f"tender_ids={sorted(tender_ids)} total={tender_list_body.get('total')}"
        )
    results.append(
        CheckResult(
            name='tender_list_contains_smoke_tender',
            passed=list_passed,
            details=list_details,
        )
    )

    tender_details_status, tender_details_body = _request(
        'GET',
        f'/tenders/{dataset.tender_id}',
        use_session_cookies=True,
    )
    details_passed = (
        tender_details_status == 200
        and isinstance(tender_details_body, dict)
        and tender_details_body.get('tender_ref') == dataset.tender_ref
        and tender_details_body.get('title') == dataset.tender_title
    )
    results.append(
        CheckResult(
            name='tender_details_positive_path',
            passed=details_passed,
            details=(
                ''
                if details_passed
                else f'status={tender_details_status} response={tender_details_body}'
            ),
        )
    )

    activity_status, activity_body = _request(
        'GET',
        '/me/activity-overview',
        use_session_cookies=True,
    )
    activity_passed = False
    activity_details = f'response={activity_body}'
    if activity_status == 200 and isinstance(activity_body, dict):
        activity_items = activity_body.get('activity_items', [])
        kinds = {
            item.get('kind')
            for item in activity_items
            if isinstance(item, dict) and item.get('tender_id') == str(dataset.tender_id)
        }
        activity_passed = 'match_created' in kinds
        activity_details = f'kinds={sorted(kinds)}'
    results.append(
        CheckResult(
            name='activity_overview_has_smoke_match',
            passed=activity_passed,
            details=activity_details,
        )
    )

    notification_status, notification_body = _request(
        'GET',
        '/me/notification-preferences',
        use_session_cookies=True,
    )
    notification_passed = (
        notification_status == 200
        and isinstance(notification_body, dict)
        and notification_body.get('email_enabled') is True
        and notification_body.get('instant_alert_enabled') is True
        and notification_body.get('daily_brief_enabled') is True
    )
    results.append(
        CheckResult(
            name='notification_preferences_seeded',
            passed=notification_passed,
            details=(
                ''
                if notification_passed
                else f'status={notification_status} response={notification_body}'
            ),
        )
    )

    profile_status, profile_body = _request(
        'GET',
        '/me/keyword-profile',
        use_session_cookies=True,
    )
    profile_passed = (
        profile_status == 200
        and isinstance(profile_body, dict)
        and sorted(profile_body.get('keywords', [])) == sorted(dataset.matched_keywords)
    )
    results.append(
        CheckResult(
            name='keyword_profile_seeded',
            passed=profile_passed,
            details=(
                ''
                if profile_passed
                else f'status={profile_status} response={profile_body}'
            ),
        )
    )

    _print_results(results)
    return 0 if all(result.passed for result in results) else 1


def _print_results(results: list[CheckResult]) -> None:
    """Print verification results in a stable machine-readable format."""
    for result in results:
        print(f'verify_smoke_validation_{result.name}={result.passed}')
        if result.details:
            print(
                f'verify_smoke_validation_{result.name}_details='
                f'{result.details}'
            )


if __name__ == '__main__':
    raise SystemExit(run())
