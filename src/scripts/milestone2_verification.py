from __future__ import annotations

import http.cookiejar
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = f"milestone2_verify_{uuid4().hex}@example.com"
TEST_PASSWORD = "StrongPass123!"
INVALID_TOKEN = "invalid.token.value"
COOKIE_NAME = "utw_access_token"

_cookie_jar = http.cookiejar.CookieJar()
_cookie_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cookie_jar))


@dataclass(frozen=True)
class CheckResult:
    name: str
    expected_status: int
    actual_status: int
    passed: bool
    details: str = ""


def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    bearer_token: str | None = None,
    use_session_cookies: bool = False,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    url = f"{BASE_URL}{path}"
    headers: dict[str, str] = {}

    data: bytes | None = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode("utf-8")

    if bearer_token is not None:
        headers["Authorization"] = f"Bearer {bearer_token}"

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        if use_session_cookies:
            response_context = _cookie_opener.open(request)
        else:
            response_context = urllib.request.urlopen(request)

        with response_context as response:
            body = response.read().decode("utf-8")
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return response.getcode(), _parse_body(body), response_headers
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        response_headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, _parse_body(body), response_headers


def _parse_body(body: str) -> dict[str, Any] | str:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def _run_check(
    name: str,
    expected_status: int,
    *,
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    bearer_token: str | None = None,
    use_session_cookies: bool = False,
) -> CheckResult:
    actual_status, response_body, _ = _request(
        method,
        path,
        json_body=json_body,
        bearer_token=bearer_token,
        use_session_cookies=use_session_cookies,
    )
    passed = actual_status == expected_status
    details = ""
    if not passed:
        details = f"response={response_body}"
    return CheckResult(
        name=name,
        expected_status=expected_status,
        actual_status=actual_status,
        passed=passed,
        details=details,
    )


def _assert_login_response_is_cookie_only(login_body: dict[str, Any] | str) -> CheckResult:
    if not isinstance(login_body, dict):
        return CheckResult(
            name="login_response_is_cookie_only",
            expected_status=200,
            actual_status=500,
            passed=False,
            details=f"response={login_body}",
        )

    if "access_token" in login_body or "token_type" in login_body:
        return CheckResult(
            name="login_response_is_cookie_only",
            expected_status=200,
            actual_status=500,
            passed=False,
            details=f"response={login_body}",
        )

    return CheckResult(
        name="login_response_is_cookie_only",
        expected_status=200,
        actual_status=200,
        passed=True,
    )


def main() -> int:
    results: list[CheckResult] = []

    results.append(
        _run_check(
            "health_check",
            200,
            method="GET",
            path="/health",
        )
    )

    signup_status, signup_body, _ = _request(
        "POST",
        "/auth/signup",
        json_body={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    results.append(
        CheckResult(
            name="signup_first_attempt",
            expected_status=201,
            actual_status=signup_status,
            passed=signup_status == 201,
            details="" if signup_status == 201 else f"response={signup_body}",
        )
    )

    duplicate_signup_status, duplicate_signup_body, _ = _request(
        "POST",
        "/auth/signup",
        json_body={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    results.append(
        CheckResult(
            name="signup_duplicate_attempt",
            expected_status=409,
            actual_status=duplicate_signup_status,
            passed=duplicate_signup_status == 409,
            details=(
                ""
                if duplicate_signup_status == 409
                else f"response={duplicate_signup_body}"
            ),
        )
    )

    wrong_login_status, wrong_login_body, _ = _request(
        "POST",
        "/auth/login",
        json_body={
            "email": TEST_EMAIL,
            "password": "WrongPass123!",
        },
    )
    results.append(
        CheckResult(
            name="login_wrong_password",
            expected_status=401,
            actual_status=wrong_login_status,
            passed=wrong_login_status == 401,
            details="" if wrong_login_status == 401 else f"response={wrong_login_body}",
        )
    )

    login_status, login_body, login_headers = _request(
        "POST",
        "/auth/login",
        json_body={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
        use_session_cookies=True,
    )
    results.append(
        CheckResult(
            name="login_success",
            expected_status=200,
            actual_status=login_status,
            passed=login_status == 200,
            details="" if login_status == 200 else f"response={login_body}",
        )
    )

    if login_status == 200:
        results.append(_assert_login_response_is_cookie_only(login_body))

        login_cookie_header = login_headers.get("set-cookie", "")
        cookie_present = COOKIE_NAME in login_cookie_header
        results.append(
            CheckResult(
                name="login_sets_cookie",
                expected_status=200,
                actual_status=200 if cookie_present else 500,
                passed=cookie_present,
                details="" if cookie_present else f"set-cookie={login_cookie_header}",
            )
        )

    results.append(
        _run_check(
            "me_missing_token",
            401,
            method="GET",
            path="/me",
        )
    )

    results.append(
        _run_check(
            "me_invalid_token",
            401,
            method="GET",
            path="/me",
            bearer_token=INVALID_TOKEN,
        )
    )

    results.append(
        _run_check(
            "me_authenticated_cookie",
            200,
            method="GET",
            path="/me",
            use_session_cookies=True,
        )
    )

    results.append(
        _run_check(
            "keyword_profile_get_default",
            200,
            method="GET",
            path="/me/keyword-profile",
            use_session_cookies=True,
        )
    )

    results.append(
        _run_check(
            "keyword_profile_put_valid",
            200,
            method="PUT",
            path="/me/keyword-profile",
            use_session_cookies=True,
            json_body={
                "keywords": ["IT", "Security", "Facilities"],
                "alert_enabled": True,
                "industry_label": "Technology",
            },
        )
    )

    results.append(
        _run_check(
            "keyword_profile_put_invalid_keywords_type",
            422,
            method="PUT",
            path="/me/keyword-profile",
            use_session_cookies=True,
            json_body={
                "keywords": "not-a-list",
                "alert_enabled": True,
                "industry_label": "Technology",
            },
        )
    )

    results.append(
        _run_check(
            "keyword_profile_put_duplicate_keywords",
            200,
            method="PUT",
            path="/me/keyword-profile",
            use_session_cookies=True,
            json_body={
                "keywords": ["IT", "it", " Security ", "Security"],
                "alert_enabled": True,
                "industry_label": "Technology",
            },
        )
    )

    oversized_keywords = [f"KW{i}" for i in range(51)]
    results.append(
        _run_check(
            "keyword_profile_put_too_many_keywords",
            422,
            method="PUT",
            path="/me/keyword-profile",
            use_session_cookies=True,
            json_body={
                "keywords": oversized_keywords,
                "alert_enabled": True,
                "industry_label": "Technology",
            },
        )
    )

    results.append(
        _run_check(
            "tenders_success",
            200,
            method="GET",
            path="/tenders",
            use_session_cookies=True,
        )
    )

    results.append(
        _run_check(
            "tenders_invalid_uuid",
            422,
            method="GET",
            path="/tenders?source_id=not-a-uuid",
            use_session_cookies=True,
        )
    )

    results.append(
        _run_check(
            "tenders_invalid_limit",
            422,
            method="GET",
            path="/tenders?limit=1000",
            use_session_cookies=True,
        )
    )

    for index in range(3):
        results.append(
            _run_check(
                f"repeated_login_cycle_{index + 1}",
                200,
                method="POST",
                path="/auth/login",
                json_body={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                },
                use_session_cookies=True,
            )
        )

    for index in range(3):
        results.append(
            _run_check(
                f"repeated_me_read_{index + 1}",
                200,
                method="GET",
                path="/me",
                use_session_cookies=True,
            )
        )

    passed_count = sum(1 for result in results if result.passed)
    total_count = len(results)

    print("=== Milestone 2 Verification Report ===")
    print(f"Verification email: {TEST_EMAIL}")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"[{status}] {result.name}: expected={result.expected_status} "
            f"actual={result.actual_status}"
        )
        if result.details:
            print(f"        {result.details}")

    print(f"\nSummary: {passed_count}/{total_count} checks passed")

    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
