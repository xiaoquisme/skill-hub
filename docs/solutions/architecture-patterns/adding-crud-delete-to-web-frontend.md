---
title: "Adding CRUD Delete Functionality to a Web Frontend"
date: 2026-07-31
category: architecture-patterns
module: skillhub-web-ui
problem_type: architecture_pattern
component: development_workflow
severity: medium
applies_when:
  - "Backend DELETE endpoint exists but frontend has no way to invoke it"
  - "Adding a destructive CRUD operation to a vanilla JS web UI"
  - "Need confirmation flow, i18n, CSS, and API client wiring in one feature"
tags:
  - crud
  - delete
  - frontend-backend-wiring
  - vanilla-js
  - confirmation-dialog
---

# Adding CRUD Delete Functionality to a Web Frontend

## Context

When a backend already exposes a DELETE endpoint (e.g. `DELETE /api/skills/{id}`) but the frontend has no UI to invoke it, users cannot perform the full CRUD lifecycle from the web interface. The gap is purely a frontend wiring problem — the database layer, storage layer, and API route handler all exist and work. This pattern documents the checklist of frontend concerns that must be addressed to close that gap.

In SkillHub, the `DELETE /api/skills/{skill_id}` endpoint existed in `skillhub/api/skills.py` (lines 153–165) with `Database.delete_skill()` and `SkillStorage.delete_skill()` already implemented. The frontend (`skillhub/static/js/`) had no API client method, no delete button, and no confirmation flow.

## Guidance

Adding delete (or any destructive CRUD operation) to a vanilla JS web frontend requires touching **six concerns** across the codebase. Skipping any one leaves the feature incomplete.

### 1. API Client Method

Add a method to the existing API client object that calls the DELETE endpoint. The method should use the shared `request()` helper so error handling is consistent with other API calls.

```js
// skillhub/static/js/api.js — inside the API object
async deleteSkill(id) {
    return this.request(`/api/skills/${id}`, { method: 'DELETE' });
},
```

**Key detail:** The existing `request()` helper already throws on non-200 responses and returns `null` for 204 responses — exactly what the DELETE endpoint returns. No special-casing needed.

### 2. UI Trigger (Delete Button)

Place the delete button in the appropriate detail view, visually separated from non-destructive actions. Use a CSS class that signals destructive intent.

```html
<!-- Inside the skill detail modal, after the install command section -->
<div class="delete-section">
    <button class="btn btn-danger btn-sm delete-skill-btn">
        ${t('skill.detail.delete')}
    </button>
</div>
```

**Placement rationale:** After the install command block and separated by a top border. This ensures users see the primary action (install) first and must scroll past it to reach the destructive action.

### 3. Confirmation Flow

Use a native `confirm()` dialog before executing the delete. On confirmation, call the API method, close the modal, and refresh the list. On cancel or error, keep the modal open.

```js
window.confirmDeleteSkill = async function(skillId, skillName) {
    var message = t('skill.detail.delete_confirm') + '\n\n' + skillName;
    if (!confirm(message)) return;

    try {
        await API.deleteSkill(skillId);
        modal.classList.add('hidden');
        performSearch();  // refresh the skill list with current filters
    } catch (err) {
        console.error('Failed to delete skill:', err);
        alert(t('skill.detail.delete_error'));
    }
};
```

**Why native `confirm()`:** The project uses vanilla JS with no UI framework. A native dialog is the simplest approach, costs zero dependencies, and is consistent with the minimalist UI style. The skill name is appended to the message so users know exactly what they're deleting.

**Post-delete refresh:** Call the existing search/filter function (e.g. `performSearch()`) rather than reloading the page. This preserves the user's current filter and sort state.

### 4. CSS Styles

Add styles for the delete section and danger button. The delete section gets a top border to visually separate it from the install command above.

```css
/* Delete Button */
.delete-section {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
}

.btn-danger {
    background: #ef4444;
    color: white;
}

.btn-danger:hover {
    background: #dc2626;
}
```

**Color choice:** Red (#ef4444) signals destructive action. The hover state darkens to #dc2626 for feedback.

### 5. i18n Strings

Add localized strings for all three user-facing messages: the button label, the confirmation prompt, and the error alert. Both active locales must be updated simultaneously.

```json
// en.json
"skill.detail.delete": "Delete",
"skill.detail.delete_confirm": "Are you sure you want to delete this skill?",
"skill.detail.delete_error": "Failed to delete the skill. Please try again."

// zh-CN.json
"skill.detail.delete": "删除",
"skill.detail.delete_confirm": "确定要删除此技能吗？",
"skill.detail.delete_error": "删除技能失败，请重试。"
```

**Three strings minimum:** Button label, confirmation message, and error message. Forgetting the error string means a bare `undefined` appears in the alert on API failure.

### 6. API Test Coverage

Add integration tests for the DELETE endpoint if none exist. Test both the happy path and the not-found case.

```python
@pytest.mark.asyncio
async def test_delete_skill():
    """Test DELETE /api/skills/{id} returns 204 and removes the skill."""
    # 1. Create a skill via the database
    # 2. DELETE /api/skills/{id} → assert 204
    # 3. GET /api/skills/{id} → assert 404
    # 4. GET /api/skills → assert deleted skill absent

@pytest.mark.asyncio
async def test_delete_skill_not_found():
    """Test DELETE /api/skills/{nonexistent} returns 404."""
    # DELETE /api/skills/nonexistent-id → assert 404
```

## Why This Matters

A DELETE endpoint without a frontend trigger is dead code from the user's perspective. The six-concern checklist above ensures the feature is actually usable:

- **API client method** — the programmatic bridge between UI and backend
- **UI trigger** — the button the user clicks
- **Confirmation flow** — the safety gate that prevents accidental deletion
- **CSS styles** — visual separation and destructive-action signaling
- **i18n strings** — complete user-facing text in all locales
- **Test coverage** — verification that the endpoint works end-to-end

Missing any one of these creates a partial feature: a button that does nothing (no API method), an API method nobody can call (no button), a destructive action with no safety gate (no confirmation), or an untested endpoint that breaks silently.

## When to Apply

- When a backend CRUD endpoint exists but the frontend has no corresponding UI
- When adding any destructive operation (delete, archive, revoke) to a web UI
- When extending an existing CRUD app with a missing operation
- When wiring up API client methods for new endpoints in a vanilla JS frontend

## Examples

### Before (incomplete CRUD)

```
Backend:  GET /api/skills ✓  POST /api/skills ✓  PUT /api/skills/{id} ✓  DELETE /api/skills/{id} ✓
Frontend: list skills ✓       create skill ✓       edit skill ✓            (missing — no UI)
Test:     list ✓              create ✓              edit ✓                  (missing — no test)
```

### After (complete CRUD)

```
Backend:  GET /api/skills ✓  POST /api/skills ✓  PUT /api/skills/{id} ✓  DELETE /api/skills/{id} ✓
Frontend: list skills ✓       create skill ✓       edit skill ✓            delete skill ✓ (with confirm)
Test:     list ✓              create ✓              edit ✓                  delete ✓ + delete-not-found ✓
```

### Files Changed (SkillHub implementation)

| File | Change |
|------|--------|
| `skillhub/static/js/api.js` | Added `deleteSkill(id)` method |
| `skillhub/static/js/app.js` | Added delete button in modal + `confirmDeleteSkill()` function |
| `skillhub/static/css/style.css` | Added `.delete-section` and `.btn-danger` styles |
| `skillhub/static/locales/en.json` | Added 3 delete-related i18n strings |
| `skillhub/static/locales/zh-CN.json` | Added 3 delete-related i18n strings |
| `tests/test_api.py` | Added `test_delete_skill` and `test_delete_skill_not_found` |

## Related

- Existing solution: `docs/solutions/runtime-errors/auth-token-hash-mismatch.md` — different module but same project area
