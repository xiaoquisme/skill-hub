---
title: "fix: standardize date display format to YYYY-MM-DD"
date: 2026-07-20
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# fix: standardize date display format to YYYY-MM-DD

## Summary

Change the skill detail modal's "Updated" date from browser-locale-dependent `toLocaleDateString()` to a fixed YYYY-MM-DD format, matching the user's preferred date format.

## Problem Frame

The skill detail modal displays `updated_at` using `new Date(skill.updated_at).toLocaleDateString()`, which produces locale-dependent output (e.g., "7/20/2026" in en-US, "2026/7/20" in zh-CN). The user wants a consistent YYYY-MM-DD format across all locales.

## Requirements

- All date displays in the UI use YYYY-MM-DD format (e.g., 2026-07-20)
- Format is consistent regardless of browser locale

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Date formatting approach | Custom helper function | Simple, no external dependency; `toISOString().slice(0,10)` is the standard JS idiom for YYYY-MM-DD |

## Implementation Units

### U1. Add date formatter and update display

**Goal:** Replace locale-dependent date formatting with fixed YYYY-MM-DD output.

**Files:**
- `skillhub/static/js/app.js`

**Approach:**
1. Add a `formatDate(isoString)` helper function that returns `YYYY-MM-DD`
2. Replace `new Date(skill.updated_at).toLocaleDateString()` with `formatDate(skill.updated_at)`

**Test expectation:** none — pure display formatting change, no behavioral logic

**Verification:** Open skill detail modal, confirm "Updated" field shows date as 2026-07-20 format.

---

## Definition of Done

- [ ] Date displays as YYYY-MM-DD in skill detail modal
- [ ] Format is consistent across English and Chinese locales
