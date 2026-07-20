---
title: "feat: Chinese Language UI Support - Plan"
type: feat
date: 2026-07-20
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

## Goal Capsule

**Objective:** Add Chinese language support to the SkillHub web UI with Chinese as the default language, using browser auto-detection and a single JSON translation file architecture.

**Authority hierarchy:** The ideation document (`docs/ideation/2026-07-20-chinese-language-support-ideation.html`) defines the user's intent. This plan implements ideas #3 (browser auto-detect locale) and #4 (single JSON translation file).

**Stop conditions:** All hardcoded English strings in the web UI are replaced with `t()` calls. Chinese displays by default for `zh-*` browsers. English displays for all other locales. The `<html lang>` attribute updates dynamically. CJK fonts render correctly on all platforms.

**Execution profile:** Lightweight — 4 implementation units, no framework dependencies, no build step.

**Tail ownership:** The implementer owns the commit. No deployment or CI changes needed.

---

## Product Contract

### Summary

Implement a lightweight i18n system for SkillHub's web UI: extract ~30 hardcoded English strings into JSON translation files, auto-detect the browser's locale, and serve Chinese by default.

### Problem Frame

SkillHub's web UI has all text hardcoded in English. Chinese-speaking users cannot understand the interface. The user explicitly requires Chinese as the default language with no manual language switcher — the browser's locale should drive the language automatically.

### Requirements

- **UI text extraction & translation (Idea #4)**
  - R1. All hardcoded English strings in `index.html` and `app.js` are extracted to JSON translation files
  - R2. A `t(key)` function replaces all hardcoded strings with translation lookups
  - R3. Translation files follow a simple key-value JSON format (`locales/zh-CN.json`, `locales/en.json`)
  - R4. Chinese (`zh-CN`) is the default locale

- **Browser auto-detection (Idea #3)**
  - R5. The browser's `navigator.language` is read on page load to determine locale
  - R6. If the locale starts with `zh`, the UI renders in Chinese; otherwise English
  - R7. The `<html lang>` attribute updates to match the detected locale
  - R8. No language switcher UI is provided — detection is automatic

- **CJK rendering**
  - R9. The CSS font stack includes explicit Chinese font fallbacks for Windows/Linux
  - R10. Dates use `Intl.DateTimeFormat('zh-CN')` for Chinese locale formatting

### Scope Boundaries

- **In scope:** Web UI only (`skillhub/static/`)
- **Deferred to follow-up:** CLI i18n, skill metadata translation, language switcher UI, additional languages beyond zh/en

---

## Planning Contract

### Key Technical Decisions

- **KTD-1: Custom `t()` function over i18n library.** For ~30 strings in a vanilla JS codebase, a full i18n library (i18next, etc.) adds unnecessary complexity and dependencies. A 15-line `t()` function with JSON imports is proportionate and zero-dependency.

- **KTD-2: JSON file format over inline strings.** Centralizing translations in `locales/zh-CN.json` and `locales/en.json` makes maintenance trivial — adding a new language is one file, adding a new string is two entries. The alternative (inline bilingual objects) couples translations to components.

- **KTD-3: Browser auto-detection over manual switcher.** The user explicitly chose auto-detection only. `navigator.language` is available on all modern browsers. For a self-hosted tool where the operator controls deployment, auto-detection is zero-config for the target audience.

- **KTD-4: Static JSON import over fetch.** Since there's no build step, use `<script>` tags to load translation files as global objects. This avoids async complexity and works with the existing vanilla JS architecture.

### Assumptions

- The browser's `navigator.language` reliably signals user preference for self-hosted tools
- ~30 strings is small enough for a single JSON file per locale (no namespace splitting needed)
- The existing font stack works on macOS; only Windows/Linux need explicit CJK fallbacks

---

## Implementation Units

### U1. Create i18n infrastructure

**Goal:** Create the translation file structure and `t()` function.

**Files:**
- `skillhub/static/locales/zh-CN.json` (new)
- `skillhub/static/locales/en.json` (new)
- `skillhub/static/js/i18n.js` (new)

**Approach:**
- Create `locales/en.json` with all current hardcoded English strings as key-value pairs (keys like `search.placeholder`, `btn.search`, `filter.all_categories`, etc.)
- Create `locales/zh-CN.json` with Chinese translations for the same keys
- Create `js/i18n.js` containing:
  - A `currentLocale` variable initialized from `navigator.language`
  - A `messages` object holding both locale dictionaries
  - A `t(key)` function that returns `messages[currentLocale][key]` with fallback to English
  - An `init()` function that sets `document.documentElement.lang` to the detected locale

**Test scenarios:**
- Happy path: `t('search.placeholder')` returns "搜索技能..." when locale is `zh-CN`
- Happy path: `t('search.placeholder')` returns "Search skills..." when locale is `en`
- Edge case: `t('nonexistent.key')` returns the key itself as fallback
- Edge case: Browser locale `zh-TW` still resolves to `zh-CN` (use first two chars)

**Verification:** Run `python -m pytest` to confirm no regressions. Open `index.html` in browser and verify `i18n.js` loads without errors.

---

### U2. Replace hardcoded strings in index.html

**Goal:** Replace all hardcoded English text in the HTML with `t()` calls.

**Files:**
- `skillhub/static/index.html` (modify)

**Dependencies:** U1

**Approach:**
- Add `<script src="/ui/js/i18n.js"></script>` before `app.js` and `api.js`
- Replace hardcoded text content with `data-i18n` attributes or inline `t()` calls
- Key replacements: title, tagline, search placeholder, button text, filter options, loading text, footer

**Test scenarios:**
- Happy path: Page title shows "SkillHub - Hermes Agent 技能注册中心" for zh-CN browsers
- Happy path: Search placeholder shows "搜索技能..." for zh-CN browsers
- Happy path: All filter options display in Chinese for zh-CN browsers
- Edge case: Page still renders correctly when i18n.js fails to load (fallback to English)

**Verification:** Open `index.html` in browser with Chrome set to zh-CN. Verify all visible text is Chinese. Switch to English locale and verify English text.

---

### U3. Replace hardcoded strings in app.js

**Goal:** Replace all hardcoded English strings in the JavaScript with `t()` calls.

**Files:**
- `skillhub/static/js/app.js` (modify)

**Dependencies:** U1

**Approach:**
- Replace all hardcoded strings in `renderSkills()`, `showSkillDetail()`, `updateCategoryFilter()`, and error states with `t()` calls
- Key replacements: loading states, error messages, empty states, metadata labels (Name, Author, Category, License, Tags, Updated), file list header, SKILL.md content label, copy button text

**Test scenarios:**
- Happy path: "No skills found" displays as "未找到技能" for zh-CN browsers
- Happy path: Metadata labels (Name, Author, etc.) display in Chinese
- Happy path: Error messages display in Chinese
- Happy path: "Copied!" feedback displays as "已复制!" for zh-CN browsers
- Edge case: `toLocaleDateString()` still works with Chinese locale formatting

**Verification:** Open SkillHub in browser with zh-CN locale. Search for a skill, open detail modal, verify all text is Chinese.

---

### U4. Update CSS font stack and HTML lang

**Goal:** Add CJK font fallbacks and ensure the HTML lang attribute is set correctly.

**Files:**
- `skillhub/static/css/style.css` (modify)
- `skillhub/static/index.html` (modify — `<html lang>` attribute)

**Dependencies:** U1

**Approach:**
- Update font-family in `style.css` to include PingFang SC, Microsoft YaHei, Noto Sans SC
- The `i18n.js` `init()` function already sets `document.documentElement.lang` — verify it works

**Test scenarios:**
- Happy path: Chinese text renders with PingFang SC on macOS
- Happy path: Chinese text renders with Microsoft YaHei on Windows (or Noto Sans SC on Linux)
- Happy path: `<html lang="zh-CN">` is set for Chinese browsers
- Happy path: `<html lang="en">` is set for English browsers

**Verification:** Inspect rendered page in browser DevTools. Check computed font-family includes CJK fonts. Check `<html>` tag has correct `lang` attribute.

---

## Verification Contract

- Run `python -m pytest` — all existing tests must pass (no Python code changes)
- Open `skillhub/static/index.html` in browser with zh-CN locale — verify Chinese UI
- Open `skillhub/static/index.html` in browser with en locale — verify English UI
- Check browser DevTools console for JS errors
- Verify `<html lang>` attribute matches detected locale

---

## Definition of Done

- All ~30 hardcoded English strings replaced with `t()` calls
- Chinese displays by default for `zh-*` browsers
- English displays for all other locales
- `<html lang>` attribute updates dynamically
- CJK fonts render correctly on macOS, Windows, and Linux
- No new dependencies added
- All existing tests pass
- No console errors in browser
