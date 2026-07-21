---
title: "Change CLI Install Method to uv tool - Plan"
type: refactor
date: 2026-07-22
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
---

# Change CLI Install Method to uv tool - Plan

## Goal Capsule

- **Objective:** Replace `pip install git+...` with `uv tool install git+...` for CLI client installation across all documentation.
- **Authority hierarchy:** User request takes precedence. No origin document.
- **Stop conditions:** All user-facing install instructions use `uv tool install`; README, client skill doc, and server skill doc are consistent.
- **Execution profile:** Lightweight — single atomic change, two files, same replacement.

## Product Contract

### Summary

Change the recommended CLI install method from `pip install` to `uv tool install` across all documentation.

### Requirements

- R1. All user-facing CLI install instructions use `uv tool install git+https://github.com/xiaoquisme/skillhub.git` instead of `pip install git+...`.
- R2. Development install instructions (`pip install -e .`) remain unchanged — those are for local development, not end-user CLI installation.

---

## Planning Contract

### Key Technical Decisions

- KTD1. **Scope boundary:** Only client CLI install instructions change. Server dev installs and Dockerfile `pip install` are out of scope.
- KTD2. **No code changes required.** `pyproject.toml` already defines the `skillhub` entry point via `[project.scripts]`, which `uv tool install` consumes correctly.

### Assumptions

- A1. `uv` is available on user machines or users can install it via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- A2. `uv tool install` from a git URL is a supported and stable feature of `uv`.

---

## Implementation Units

### U1. Update README.md install instructions

- **Goal:** Replace `pip install git+...` with `uv tool install git+...` in the Client CLI section.
- **Requirements:** R1
- **Dependencies:** None
- **Files:** `README.md`
- **Approach:** Single find-and-replace on the install command in the Client CLI section (line 29).
- **Test expectation:** None — documentation change, no runtime behavior.

### U2. Update skillhub-client SKILL.md install instructions

- **Goal:** Replace `pip install git+...` with `uv tool install git+...` in the Installation section.
- **Requirements:** R1
- **Dependencies:** None
- **Files:** `skills/skillhub-client/SKILL.md`
- **Approach:** Single find-and-replace on the install command in the Installation section (line 30).
- **Test expectation:** None — documentation change, no runtime behavior.

---

## Verification Contract

| Gate | Command | Pass criterion |
|------|---------|----------------|
| Documentation consistency | `grep -rn "pip install git+" .` | Zero matches (all replaced) |
| Dev instructions preserved | `grep -n "pip install -e" README.md` | Still present (not changed) |

## Definition of Done

- All `pip install git+...` references in user-facing docs are replaced with `uv tool install git+...`.
- Development install instructions (`pip install -e .`) are unchanged.
- `grep -rn "pip install git+" .` returns zero matches.
