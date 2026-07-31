---
title: "Add Skill Delete Functionality - Plan"
type: feat
date: 2026-07-31
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

## Goal Capsule

Add delete functionality to the SkillHub web UI — when a user opens a skill detail modal, they can delete it with a confirmation dialog. The backend DELETE endpoint already exists; this plan covers the frontend wiring and a missing API test.

**Stop conditions:**
- Delete button appears in the skill detail modal
- Clicking delete shows a confirmation dialog
- On confirm, the skill is deleted via `DELETE /api/skills/{id}` and the modal closes
- The skill list refreshes without the deleted skill
- i18n strings present for both English and Chinese
- API endpoint has a test coverage

---

## Product Contract

### Summary
Users can delete skills directly from the skill detail view. This completes the CRUD lifecycle for skills in the web UI.

### Problem Frame
The backend already supports `DELETE /api/skills/{skill_id}` (in `skillhub/api/skills.py` lines 153–165), and both `Database.delete_skill()` and `SkillStorage.delete_skill()` are implemented. However, the frontend has no way to invoke this endpoint — no delete button, no API client method, and no confirmation flow. Additionally, there is no test covering the DELETE endpoint.

### Requirements
- R1. The `API` client object exposes a `deleteSkill(id)` method that calls `DELETE /api/skills/{id}`.
- R2. A delete button appears in the skill detail modal (below the install command section).
- R3. Clicking the delete button shows a native browser `confirm()` dialog with a localized message.
- R4. On confirmation, the skill is deleted, the modal closes, and the skill list refreshes.
- R5. On cancel or API error, the modal stays open and the user sees no destructive effect.
- R6. i18n strings for delete UI are present in `en.json` and `zh-CN.json`.
- R7. The DELETE endpoint has at least one integration test in `tests/test_api.py`.

### Scope Boundaries
- **Deferred:** Bulk delete from the list view, soft delete, undo/restore.
- **Outside scope:** Authorization/permission checks on delete (auth was previously removed per `2026-07-20-001`).

---

## Planning Contract

### Key Technical Decisions
- KTD1. **Native `confirm()` for confirmation** — The project uses vanilla JS with no UI framework. A native `confirm()` dialog is the simplest, consistent approach (no new dependencies). Matches the minimalist UI style.
- KTD2. **Delete button placement** — Placed after the install command block in the skill detail modal, styled as a danger-red secondary button to visually distinguish it from other actions.
- KTD3. **Post-delete refresh** — After successful delete, close modal and call `loadSkills()` with current filter/sort params to refresh the list. This avoids stale state.
- KTD4. **No backend changes needed** — The DELETE endpoint, database method, and storage method all exist. Only frontend code and tests are needed.

### Assumptions
- The `DELETE /api/skills/{skill_id}` endpoint is functional (already implemented in `skillhub/api/skills.py`).
- `Database.delete_skill()` handles foreign key cascades (skill_files reference `ON DELETE CASCADE` in schema).
- `SkillStorage.delete_skill()` removes the entire skill directory via `shutil.rmtree`.

---

## Implementation Units

### U1. Add `deleteSkill()` to API client

**Goal:** Extend the `API` object with a method to delete skills.

**Requirements:** R1

**Dependencies:** None

**Files:**
- `skillhub/static/js/api.js`

**Approach:**
Add a `deleteSkill(id)` method to the `API` object that calls `DELETE /api/skills/${id}`. The existing `request()` helper already handles non-200 responses by throwing. For 204 responses it returns `null` — which is exactly what the DELETE endpoint returns. So the implementation is:

```js
async deleteSkill(id) {
    return this.request(`/api/skills/${id}`, { method: 'DELETE' });
},
```

**Test scenarios:**
- Happy path: `API.deleteSkill(validId)` resolves to `null`
- Error path: `API.deleteSkill(nonExistentId)` throws an error

---

### U2. Add delete button to skill detail modal

**Goal:** Show a delete button in the skill detail modal with confirmation and post-delete behavior.

**Requirements:** R2, R3, R4, R5

**Dependencies:** U1

**Files:**
- `skillhub/static/js/app.js`

**Approach:**
In the `showSkillDetail()` function, append a delete button block after the install command section. The button calls a new `deleteSkill(skillId)` function defined at module scope:

1. Add delete button HTML to the `skillDetail.innerHTML` assignment, after the `.install-command` div:
```html
<div class="delete-section">
    <button class="btn btn-danger btn-sm delete-skill-btn">${t('skill.detail.delete')}</button>
</div>
```

2. Add event listener on the delete button (after `skillDetail.innerHTML` is set):
```js
var deleteBtn = skillDetail.querySelector('.delete-skill-btn');
if (deleteBtn) {
    deleteBtn.addEventListener('click', function() {
        window.confirmDeleteSkill(skill.id, skill.display_name || skill.name);
    });
}
```

3. Define `window.confirmDeleteSkill` at module scope (alongside `copyInstallCommand`):
```js
window.confirmDeleteSkill = async function(skillId, skillName) {
    var message = t('skill.detail.delete_confirm') + '\n\n' + skillName;
    if (!confirm(message)) return;
    
    try {
        await API.deleteSkill(skillId);
        modal.classList.add('hidden');
        loadSkills(
            searchInput.value.trim() || undefined,
            categoryFilter.value || undefined,
            sortFilter.value
        );
    } catch (err) {
        console.error('Failed to delete skill:', err);
        alert(t('skill.detail.delete_error'));
    }
};
```

**Test scenarios:**
- Happy path: Click delete → confirm → modal closes, list refreshes without deleted skill
- Cancel path: Click delete → cancel → modal stays open, nothing happens
- Error path: API error → alert shown, modal stays open
- Edge case: Delete button is not shown for skills that don't exist (defensive check)

---

### U3. Add delete button CSS styles

**Goal:** Style the delete button with a danger/red appearance.

**Requirements:** R2

**Dependencies:** None

**Files:**
- `skillhub/static/css/style.css`

**Approach:**
Add styles at the end of the CSS file:

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

The `delete-section` gets a top border to visually separate it from the install command. The button uses red to signal destructive action.

---

### U4. Add i18n strings for delete UI

**Goal:** Add localized strings for the delete button, confirmation, and error.

**Requirements:** R6

**Dependencies:** None

**Files:**
- `skillhub/static/locales/en.json`
- `skillhub/static/locales/zh-CN.json`

**Approach:**

Add to `en.json`:
```json
"skill.detail.delete": "Delete",
"skill.detail.delete_confirm": "Are you sure you want to delete this skill?",
"skill.detail.delete_error": "Failed to delete the skill. Please try again."
```

Add to `zh-CN.json`:
```json
"skill.detail.delete": "删除",
"skill.detail.delete_confirm": "确定要删除此技能吗？",
"skill.detail.delete_error": "删除技能失败，请重试。"
```

---

### U5. Add DELETE endpoint API test

**Goal:** Add test coverage for the DELETE API endpoint.

**Requirements:** R7

**Dependencies:** None

**Files:**
- `tests/test_api.py`

**Approach:**
Add a new test function `test_delete_skill` that:
1. Creates a temporary database and storage (same pattern as existing tests)
2. Creates a skill via the database
3. Calls `DELETE /api/skills/{id}` and asserts 204 response
4. Calls `GET /api/skills/{id}` and asserts 404
5. Calls `GET /api/skills` and asserts the deleted skill is absent

Also add `test_delete_skill_not_found` that:
1. Calls `DELETE /api/skills/nonexistent-id` and asserts 404 response

---

## Verification Contract

| Gate | Command | Expected |
|------|---------|----------|
| Unit test | `cd skillhub && python -m pytest tests/test_api.py -v -k delete` | Both delete tests pass |
| Full test suite | `cd skillhub && python -m pytest tests/` | All tests pass |
| Visual check | Open `/ui/`, click a skill, scroll to bottom | Red "Delete" button visible |
| Delete flow | Click Delete → confirm → modal closes, list refreshes | Skill removed from list |
| Cancel flow | Click Delete → cancel → modal stays open | No change |
| i18n | Switch browser to Chinese, open skill detail | Delete button and confirm dialog show Chinese text |

---

## Definition of Done
- [ ] `API.deleteSkill(id)` method exists in `api.js`
- [ ] Delete button appears in skill detail modal
- [ ] Confirmation dialog shows before deletion
- [ ] Successful delete closes modal and refreshes skill list
- [ ] Error case shows alert and keeps modal open
- [ ] i18n strings present in both `en.json` and `zh-CN.json`
- [ ] CSS styles for delete button are in `style.css`
- [ ] DELETE endpoint has test coverage in `test_api.py`
- [ ] All existing tests still pass

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `skillhub/static/js/api.js` | Modify | Add `deleteSkill(id)` method |
| `skillhub/static/js/app.js` | Modify | Add delete button in modal + `confirmDeleteSkill()` function |
| `skillhub/static/css/style.css` | Modify | Add `.delete-section` and `.btn-danger` styles |
| `skillhub/static/locales/en.json` | Modify | Add delete-related i18n strings |
| `skillhub/static/locales/zh-CN.json` | Modify | Add delete-related i18n strings |
| `tests/test_api.py` | Modify | Add `test_delete_skill` and `test_delete_skill_not_found` |
