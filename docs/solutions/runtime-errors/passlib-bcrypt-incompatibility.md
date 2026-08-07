---
title: "passlib CryptContext fails with bcrypt >= 4.1"
date: 2026-08-07
category: "docs/solutions/runtime-errors"
module: auth
problem_type: runtime_error
component: authentication
severity: high
symptoms:
  - "passlib bcrypt backend raises ValueError: password cannot be longer than 72 bytes during internal wrap_bug detection"
  - "Password hashing or verification crashes when passlib is used with bcrypt >= 4.1.0"
root_cause: wrong_api
resolution_type: dependency_update
tags:
  - passlib
  - bcrypt
  - password-hashing
  - dependency
  - authentication
---

# passlib CryptContext fails with bcrypt >= 4.1

## Problem

passlib's bcrypt backend is incompatible with bcrypt >= 4.1.0. The library is effectively unmaintained (last release 2020) and its internal bug-detection mechanism triggers a `ValueError` on newer bcrypt versions that enforce the 72-byte password limit.

## Symptoms

- `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary` during password hashing
- `AttributeError: module 'bcrypt' has no attribute '__about__'` in passlib's version detection
- All authentication endpoints fail — login, registration, password change

## What Didn't Work

- Using `passlib[bcrypt]` with `CryptContext(schemes=["bcrypt"])` — the standard pattern from older Python projects — triggers the error because passlib's `_finalize_backend_mixin` calls `detect_wrap_bug` which sends a 72-byte test password to `bcrypt.hashpw`
- Pinning bcrypt to an older version works temporarily but blocks security updates

## Solution

Replace passlib's `pwd_context` with direct `bcrypt` library calls:

**Before (broken with bcrypt >= 4.1):**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**After (works with all bcrypt versions):**
```python
import bcrypt

def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )
```

Key differences: (1) no intermediate wrapper — bcrypt used directly, (2) explicit encoding to bytes (bcrypt API requires `bytes`, not `str`), (3) `gensalt()` generates its own salt. The `hashpw` return type is `bytes`, so `.decode("utf-8")` converts back to string for storage.

**Migration for existing passlib projects:**
1. Search for `from passlib` and `pwd_context` across the codebase
2. Replace each usage with direct `bcrypt` equivalents
3. Remove `passlib` from `requirements.txt` / `pyproject.toml`
4. Existing bcrypt hashes (`$2b$...`) verify correctly with `bcrypt.checkpw` — no migration needed
5. Run test suite, paying attention to auth flow tests

## Why This Works

passlib's `_finalize_backend_mixin` calls `detect_wrap_bug` which sends a 72-byte test password to `bcrypt.hashpw`. Newer bcrypt versions raise `ValueError` for passwords exceeding 72 bytes — a legitimate safety check that passlib's internal probing triggers as a false positive. Using bcrypt directly avoids the problematic abstraction layer entirely.

The bcrypt library's public API is three functions (`hashpw`, `checkpw`, `gensalt`). There is no wrapper to go out of sync, no internal bug-detection probing, and no intermediary to debug. The dependency tree shrinks by one package and one potential point of failure.

## Prevention

- Use `bcrypt` directly instead of `passlib` for new projects
- Pin dependency versions in `pyproject.toml` for non-stdlib packages
- Test password hashing with the exact bcrypt version in production
- When choosing wrapper libraries, check maintenance status — passlib has been unmaintained since 2020

## Related Issues

- [pyca/passlib#720](https://github.com/pyca/passlib/issues/720) — passlib 1.7.4 breaks with bcrypt >= 4.1
- `docs/solutions/runtime-errors/auth-token-hash-mismatch.md` — different auth bug (hash comparison logic error, not dependency incompatibility)
- `docs/plans/2026-08-07-001-feat-user-management-plan.md` — the plan that chose bcrypt over passlib
