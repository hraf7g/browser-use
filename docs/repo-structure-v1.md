# Repo Structure: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines where new product code should live inside the existing repository.

Rule:

- all UTW product code must live outside `browser_use/`
- the core `browser_use/` library should remain untouched

This keeps product code maintainable and reduces risk when updating upstream browser-use code.

---

## 2. Top-Level Application Folder

Create a top-level `src/` directory for all UTW-specific application code.

Recommended structure:

```text
src/
  api/
  frontend/
  crawler/
    portals/
    configs/
    runner/
  ingestion/
  matching/
  email/
  scheduler/
  db/
    migrations/
    models/
  shared/
    schemas/
    config/
    logging/
  tests/
    fixtures/