---
title: "Add Install Count Sorting to UI - Plan"
type: feat
date: 2026-07-23
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

## Goal Capsule

Add a "Most Downloads" sort option to the SkillHub web UI, with download count descending as the default sort order.

**Stop conditions:**
- Sort dropdown includes a "Most Downloads" option
- Default sort is `download_count` descending
- i18n strings present for both English and Chinese
- Existing sort options continue to work

---

## Product Contract

### Summary
The skill list UI supports sorting by install count, helping users discover popular skills. This builds on the existing `download_count` backend to surface it as a first-class sort option in the frontend.

### Problem Frame
The backend already tracks download counts and supports `download_count` as a sort field, but the UI only offers "Recently Updated", "Newest", and "Name (A-Z)" sorting. Users cannot discover popular skills by install count from the web interface.

### Requirements
- R1. The sort dropdown includes a "Most Downloads" option with value `download_count`.
- R2. The default sort order is `download_count` descending when the page loads.
- R3. i18n strings for the new sort option are present in `en.json` and `zh-CN.json`.

### Scope Boundaries
- **Deferred for later:** Displaying download count on skill cards (visual badge or count). The user only requested sorting.
- **Outside this product's identity:** Analytics dashboards or trending algorithms.

---

## Planning Contract

### Key Technical Decisions
- KTD1. **Default sort change** — The default sort changes from `updated_at` to `download_count` (descending). The backend already sorts descending for non-name fields, so no API change is needed. This surfaces popular skills immediately on page load.

### Assumptions
- The backend `download_count` column and `ALLOWED_SORT_FIELDS` support are already in place from the prior download-count feature.

---

## Implementation Units

### U1. Add download count sort option to UI

**Goal:** Add "Most Downloads" to the sort dropdown, make it the default, and add i18n strings.

**Requirements:** R1, R2, R3

**Dependencies:** None

**Files:**
- `skillhub/static/index.html` (add option, change default)
- `skillhub/static/js/app.js` (update i18n option index)
- `skillhub/static/locales/en.json` (add translation)
- `skillhub/static/locales/zh-CN.json` (add translation)

**Approach:**
- In `index.html`, add `<option value="download_count">Most Downloads</option>` as the first option in `#sort-filter` and remove the `selected` attribute from the `updated_at` option (or add `selected` to the new option). The API sorts descending by default for non-name fields, so `sort=download_count` returns highest counts first.
- In `app.js`, update `applyI18n()` to map the new option's text: `sortOptions[0]` is now `download_count`, so the index mapping for existing options shifts.
- In `en.json`, add `"filter.sort_downloads": "Most Downloads"`.
- In `zh-CN.json`, add `"filter.sort_downloads": "最多下载"`.

**Test scenarios:**
- Happy path: sort dropdown shows "Most Downloads" as the first option
- Happy path: page loads with download count sorting active (API receives `sort=download_count`)
- Happy path: switching to other sort options still works correctly
- Edge case: skills with equal download counts maintain stable order
- Integration: API response confirms skills are ordered by download_count descending

**Verification:** Open the SkillHub web UI, confirm the sort dropdown has "Most Downloads" as the default, and skills are ordered by install count. Switch to other sort options and verify they still work.

---

## Verification Contract

| Gate | Command | Expected |
|------|---------|----------|
| Visual check | Open `/ui/` in browser | Sort dropdown shows "Most Downloads" as default |
| API check | `curl localhost:8000/api/skills?sort=download_count` | Skills ordered by download_count desc |
| Existing sort | Switch to "Recently Updated" in UI | Skills reorder correctly |

---

## Definition of Done
- [ ] "Most Downloads" sort option appears in the UI dropdown
- [ ] Default sort is `download_count` descending on page load
- [ ] i18n strings present in both English and Chinese
- [ ] All existing sort options continue to function
