---
title: "Add Download Count Tracking - Plan"
type: feat
date: 2026-07-23
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

## Goal Capsule

Add download count tracking to SkillHub so that every time a user installs a skill via the CLI, the server records the download and exposes the count in API responses and CLI output.

**Stop conditions:**
- `download_count` column exists in the skills table with default 0
- Each successful skill file download increments the count
- Search and list CLI commands display download count
- All existing tests pass; new tests cover download count behavior

---

## Product Contract

### Summary

Track how many times each skill has been downloaded. The server stores a per-skill counter that increments on each download, and both the API and CLI expose this metric for visibility and sort-by-popularity.

### Problem Frame

SkillHub currently has no way to measure skill popularity. Adding download counts gives publishers feedback on usage and helps users discover widely-used skills.

### Requirements

- R1. The skills table includes a `download_count` column (integer, default 0).
- R2. Downloading any file for a skill increments that skill's `download_count` by 1.
- R3. API responses for skill list and detail include `download_count`.
- R4. CLI `search` and `list` commands display `download_count`.
- R5. Download count is sortable in the API (via the `sort` query parameter).

### Scope Boundaries

- **Deferred for later:** Download count is per-skill, not per-file or per-user. A per-user download history is out of scope.
- **Outside this product's identity:** Analytics dashboards, trending algorithms, or rate limiting on downloads.

---

## Planning Contract

### Key Technical Decisions

- KTD1. **Column on existing table** — Add `download_count` directly to the `skills` table rather than a separate download-logs table. A simple integer counter is sufficient for the current scale; a separate table would only be warranted if per-user or per-file granularity were needed.

- KTD2. **Increment at file-download time** — The `download_skill_file` endpoint is the single download path for both CLI install and direct file fetch. Incrementing there covers all download sources without duplicating logic.

- KTD3. **Non-blocking increment** — Use `UPDATE skills SET download_count = download_count + 1 WHERE id = ?` as a single SQL statement rather than read-modify-write. This avoids race conditions under concurrent downloads and keeps the operation atomic.

### Assumptions

- The download count is an approximation under concurrency — two near-simultaneous downloads may read the same intermediate value in the API response, but the counter itself will be correct in the database. This is acceptable for a popularity metric.

---

## Implementation Units

### U1. Database schema and download count increment

**Goal:** Add `download_count` column to the skills table and create an atomic increment method. Handle both new databases (column in schema) and existing databases (ALTER TABLE migration).

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- `skillhub/database.py` (modify schema, add migration, add method)

**Approach:**
- Add `download_count INTEGER DEFAULT 0` to the `SCHEMA` SQL string in the skills table definition. This covers new database creation.
- In the `connect()` method, after `executescript(SCHEMA)`, run an `ALTER TABLE skills ADD COLUMN download_count INTEGER DEFAULT 0` wrapped in a try/except to handle the "duplicate column" error for databases that already have it. This is the standard SQLite migration pattern when no formal migration system exists.
- Add `increment_download_count(skill_id: str)` method to the `Database` class. This method executes `UPDATE skills SET download_count = download_count + 1 WHERE id = ?` and commits.
- Add `"download_count"` to the `ALLOWED_SORT_FIELDS` set.

**Test scenarios:**
- Happy path: creating a skill starts with `download_count = 0`
- Happy path: `increment_download_count` increases the count by 1
- Edge case: calling `increment_download_count` twice on the same skill yields count = 2
- Edge case: incrementing a non-existent skill_id is a no-op (no error, no row changed)
- Integration: existing database gets the column added via ALTER TABLE migration

**Verification:** `pytest tests/test_database.py` passes with the new test cases.

---

### U2. API model and endpoint changes

**Goal:** Expose `download_count` in API responses and trigger the increment on file download.

**Requirements:** R3, R5

**Dependencies:** U1

**Files:**
- `skillhub/models.py` (add field to SkillResponse)
- `skillhub/api/skills.py` (update mapper, add increment call)
- `skillhub/database.py` (already modified in U1)

**Approach:**
- Add `download_count: int = 0` to the `SkillResponse` Pydantic model in `skillhub/models.py`. `SkillDetail` inherits from `SkillResponse`, so it gets the field automatically.
- Update `_skill_from_row` in `skillhub/api/skills.py` to pass `download_count=row.get("download_count", 0)`.
- In the `download_skill_file` endpoint, after confirming the skill and file exist, call `await db.increment_download_count(skill_id)` before returning the `FileResponse`.
- Add `"download_count"` to the `ALLOWED_SORT_FIELDS` set in `database.py` (done in U1).

**Test scenarios:**
- Happy path: GET `/api/skills` response includes `download_count: 0` for a newly created skill
- Happy path: downloading a file increments the skill's `download_count` by 1
- Integration: creating a skill, downloading a file, then listing skills shows `download_count: 1`
- Edge case: downloading the same file twice increments the count to 2

**Verification:** `pytest tests/test_api.py` passes with the new test cases.

---

### U3. CLI display and download count tests

**Goal:** Show download count in search and list CLI output, and add comprehensive tests.

**Requirements:** R4

**Dependencies:** U2

**Files:**
- `skillhub/cli/commands/search.py` (add download count display)
- `skillhub/cli/commands/list_cmd.py` (add download count display)
- `tests/test_database.py` (add download count tests)
- `tests/test_api.py` (add download count integration tests)

**Approach:**
- In `skillhub/cli/commands/search.py`, after printing tags, add a line showing `Downloads: {count}` when `download_count > 0`.
- In `skillhub/cli/commands/list_cmd.py`, after printing the skill name and description, add download count info when `download_count > 0`.
- Add test cases in `tests/test_database.py` for `increment_download_count` behavior.
- Add test cases in `tests/test_api.py` for the download count API response and increment-on-download behavior.

**Test scenarios:**
- Search output shows download count for skills with count > 0
- Search output omits download count for skills with count = 0
- List output shows download count for skills with count > 0
- Database tests cover increment, double-increment, and non-existent skill edge cases
- API tests cover response shape and increment-on-download integration

**Verification:** `pytest` passes all tests including new download count scenarios.

---

## Verification Contract

| Gate | Command | Expected |
|------|---------|----------|
| Unit tests | `pytest tests/test_database.py -v` | All pass including new download count tests |
| API tests | `pytest tests/test_api.py -v` | All pass including new download count tests |
| Full suite | `pytest` | All pass, no regressions |

---

## Definition of Done

- [ ] `download_count` column exists in the skills table with default 0
- [ ] Each skill file download atomically increments `download_count`
- [ ] API responses for list and detail include `download_count`
- [ ] `download_count` is sortable via the `sort` query parameter
- [ ] CLI `search` and `list` commands display download count when > 0
- [ ] All existing tests pass with no regressions
- [ ] New tests cover increment behavior, API response shape, and CLI display
