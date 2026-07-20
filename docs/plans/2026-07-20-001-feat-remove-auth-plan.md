---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
created: 2026-07-20
---

# Remove Token Validation from SkillHub

## Goal

Remove all token-based authentication from SkillHub — the `api_tokens` table, token validation middleware, auth API endpoints, CLI auth commands, and related models. After this change, all API endpoints become publicly accessible without authentication.

## Problem Frame

SkillHub currently requires API tokens for publishing and deleting skills. The user wants to remove this requirement entirely, making all endpoints public. This simplifies the codebase and removes the auth layer that caused the hash-mismatch bug documented in `docs/solutions/runtime-errors/auth-token-hash-mismatch.md`.

## Requirements

1. All API endpoints become publicly accessible (no auth required)
2. The `api_tokens` database table is removed
3. The auth CLI commands (`skillhub auth login`, `skillhub auth status`) are removed
4. The auth API endpoint (`POST /api/auth/tokens`) is removed
5. Token-related models are removed
6. Tests are updated to reflect the removal

## Implementation Units

### U1. Remove Auth Dependencies and Middleware

**Goal:** Remove `get_current_token` and `require_auth` from the dependency injection layer.

**Files:**
- `skillhub/api/deps.py` — remove `get_current_token`, `require_auth`, and `hashlib` import

**Approach:** Delete the two auth functions and the hashlib import. Keep `get_config`, `get_db`, `get_storage` unchanged.

**Test expectation:** none — pure deletion, no new behavior

---

### U2. Remove Auth API Endpoints

**Goal:** Delete the auth router and its endpoints.

**Files:**
- `skillhub/api/auth.py` — delete entire file
- `skillhub/main.py` — remove `auth_router` import and `app.include_router(auth_router)`

**Approach:** Remove the auth module and its registration in the FastAPI app.

**Test expectation:** none — pure deletion

---

### U3. Remove Auth from Skills API

**Goal:** Remove auth requirements from `publish_skill` and `delete_skill` endpoints.

**Files:**
- `skillhub/api/skills.py` — remove `require_auth` import, remove `token: str = Depends(require_auth)` from `publish_skill` and `delete_skill`, remove `published_by=token` from publish_skill calls

**Approach:** The `publish_skill` endpoint currently passes `published_by=token`. After removal, pass `published_by=None` or omit it. The `delete_skill` endpoint checks `published_by` for authorization — remove that check entirely.

**Test expectation:** none — behavior simplification, existing tests verify the endpoints work

---

### U4. Remove Token Database Operations

**Goal:** Remove token-related methods from the Database class and the `api_tokens` table.

**Files:**
- `skillhub/database.py` — remove `api_tokens` table from SCHEMA, remove `create_token`, `validate_token`, `delete_token`, `list_tokens` methods

**Approach:** Delete the table definition and all four token methods.

**Test expectation:** none — pure deletion

---

### U5. Remove Token Models

**Goal:** Remove token-related Pydantic models.

**Files:**
- `skillhub/models.py` — remove `ApiToken`, `ApiTokenCreate`, `ApiTokenResponse` models

**Approach:** Delete the three model classes.

**Test expectation:** none — pure deletion

---

### U6. Remove CLI Auth Commands

**Goal:** Remove the `skillhub auth` command group.

**Files:**
- `skillhub/cli/commands/auth.py` — delete entire file
- `skillhub/cli/main.py` — remove `auth` import and `cli.add_command(auth)`

**Approach:** Delete the auth CLI module and its registration.

**Test expectation:** none — pure deletion

---

### U7. Remove Config Auth Field

**Goal:** Remove `api_token` from the configuration.

**Files:**
- `skillhub/config.py` — remove `api_token: Optional[str] = None` from `AppConfig`

**Approach:** Remove the field. Users with existing configs will have the field silently ignored.

**Test expectation:** none — config change, no behavioral change

---

### U8. Update Tests

**Goal:** Update tests to reflect the removal of auth.

**Files:**
- `tests/test_api.py` — remove `test_auth_required`, remove token creation from other tests, remove `from skillhub.api.auth import hash_token`

**Approach:** The `test_auth_required` test should be deleted. The `test_database_crud` test that creates tokens should be updated to remove token creation. Remove unused imports.

**Test expectation:** all remaining tests pass

---

## Dependency Graph

```
U1 (deps) ─┐
U2 (auth API) ─┤
U3 (skills API) ─┼──▶ U8 (tests)
U4 (database) ─┤
U5 (models) ─┤
U6 (CLI auth) ─┤
U7 (config) ─┘
```

All units U1-U7 are independent (pure deletions) and can be done in any order. U8 depends on all others being complete.

## Verification

After all changes:
1. `pytest tests/ -v` — all tests pass
2. `python3 -m uvicorn skillhub.main:app` — server starts without errors
3. `POST /api/skills` — works without Authorization header
4. `DELETE /api/skills/{id}` — works without Authorization header
5. `skillhub --help` — no `auth` command shown
