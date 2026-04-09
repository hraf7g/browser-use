# API Contract: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines the minimum API surface for UAE Tender Watch v1.

The API should support only what the first version needs:

- signup/login
- current user access
- keyword profile read/update
- tenders list page
- operator status page

Do not add extra admin or management endpoints in v1 unless they are clearly required.

---

## 2. Auth Recommendation

Primary recommendation for v1:

- **token-based auth**

Reason:
- simpler than full session management for a small API
- straightforward for API and minimal frontend integration
- good enough for v1

Use a bearer token style contract consistently.

---

## 3. Common API Rules

## Error shape
All API errors should return a simple JSON shape:

```json
{
  "detail": "Human-readable message",
  "code": "error_code"
}