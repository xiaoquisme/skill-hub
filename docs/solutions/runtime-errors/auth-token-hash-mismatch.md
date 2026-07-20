---
title: Auth token validation compares raw token against stored hash
date: 2026-07-20
category: docs/solutions/runtime-errors
module: api/auth
problem_type: runtime_error
component: authentication
symptoms:
  - "All authenticated API requests return 401 Unauthorized"
  - "Token created via create_token succeeds but validate_token fails"
root_cause: logic_error
resolution_type: code_fix
severity: critical
tags:
  - authentication
  - token
  - hash
  - sha256
---

# Auth token validation compares raw token against stored hash

## Problem

The API's `get_current_token` dependency passed the raw bearer token to `validate_token()`, but `validate_token()` expected a SHA-256 hash. Since the raw token never matches its own hash, every authenticated request failed with 401.

## Symptoms

- Creating a token via `POST /api/auth/tokens` succeeds and returns the raw token
- Using that token in `Authorization: Bearer <token>` header returns 401
- The server logs show `401 Unauthorized` for every authenticated endpoint

## What Didn't Work

- Verified the token was stored correctly in the database
- Confirmed the hash was computed with SHA-256 during creation
- The mismatch was not obvious because the function signature accepted `token_hash: str` but the caller passed the raw token

## Solution

In `skillhub/api/deps.py`, hash the token before validating:

```python
# Before (broken)
token = authorization[7:]  # Strip "Bearer " prefix
token_record = await db.validate_token(token)

# After (fixed)
token = authorization[7:]  # Strip "Bearer " prefix
token_hash = hashlib.sha256(token.encode()).hexdigest()
token_record = await db.validate_token(token_hash)
```

Also added `import hashlib` at the top of the file.

## Why This Works

Tokens are stored as SHA-256 hashes in the `api_tokens` table. The `validate_token()` method queries by `token_hash`, so it needs the hash, not the raw token. The creation path (`auth.py:hash_token()`) correctly hashes before storing, but the validation path forgot to hash before querying.

## Prevention

- When a function accepts a hash parameter, verify callers pass the hash, not the original value
- Add a type alias like `TokenHash = str` to make the expected format explicit
- Consider hashing inside `validate_token()` rather than at the call site, so the contract is clear

## Related Issues

- None documented yet
