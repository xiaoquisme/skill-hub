---
title: Multi-Target Skill Install - Plan
type: feat
date: 2026-08-06
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

## Goal Capsule

Extend the `skillhub install` CLI command to support installing skills into Hermes, Claude Code, and Codex targets, with user-level and project-level scope options. Currently the install command hardcodes `~/.hermes/skills/` as the only destination.

## Product Contract

### Summary

The `skillhub install` command gains `--target` and `--scope` flags, a target registry that maps each platform to its directory structure, and config-level defaults so users don't repeat flags on every install.

### Problem Frame

Today `skillhub install <name>` always writes to `~/.hermes/skills/<category>/<name>/`. Users who also work with Claude Code or Codex must manually copy skills into the right directories. This defeats the purpose of a centralized registry.

### Requirements

- R1. The install command accepts a `--target` flag to select the destination platform (`hermes`, `claude-code`, `codex`).
- R2. The install command accepts a `--scope` flag to select user-level (`~/.<platform>/`) or project-level (`./.<platform>/`) installation.
- R3. A `targets` section in `~/.skillhub/config.yaml` provides per-target defaults for path, scope, and enabled state.
- R4. Each target adapter knows the correct directory layout and file format for its platform.
- R5. The default target is `hermes` with user-level scope, preserving current behavior when no flags are passed.
- R6. A `skillhub install --list-targets` subcommand shows available targets and their configured paths.

### Scope Boundaries

**In scope:**
- CLI flag additions (`--target`, `--scope`, `--list-targets`)
- Target adapter abstraction (directory resolution, file writing)
- Config schema extension for target defaults
- Unit tests for each target adapter
- Web UI: display target compatibility and install commands in skill detail view
- Built-in skills (`skills/`): ensure `skillhub-server` and `skillhub-client` SKILL.md files are compatible with all targets

**Out of scope:**
- Server-side changes (the API is unaffected)
- Skill format conversion between platforms (skills are stored as-is; Codex adapter renames SKILL.md to AGENTS.md as a directory convention, not a content transformation)
- Uninstall command (future work)
- Auto-detection of which platform is installed on the user's machine

---

## Planning Contract

### Key Technical Decisions

KTD-1. Target abstraction via registry pattern — a dict of `TargetAdapter` instances keyed by name, each responsible for resolving install paths and writing files. (session-settled: user-directed — chosen over a plugin system: simpler for three fixed targets, no dynamic loading needed)

KTD-2. Scope as a flag, not auto-detection — explicit `--scope` flag with `user` / `project` values rather than inferring from cwd. (session-settled: user-directed — chosen over auto-detect: auto-detection is fragile across monorepos and CI environments)

KTD-3. Config-driven defaults — `~/.skillhub/config.yaml` gains a `targets` map so users set their preferred target and scope once. (session-settled: user-directed — chosen over env vars only: YAML is more discoverable and reviewable)

### Assumptions

- Claude Code uses `~/.claude/skills/<name>/SKILL.md` (user) and `.claude/skills/<name>/SKILL.md` (project). Confirmed via code.claude.com/docs/en/skills.
- Codex uses `~/.codex/agents/<name>/AGENTS.md` (user) and `.codex/agents/<name>/AGENTS.md` (project). Based on OpenAI Codex CLI conventions; to be validated during implementation.
- Hermes uses `~/.hermes/skills/<category>/<name>/` (user) and `.hermes/skills/<category>/<name>/` (project). Existing behavior.
- All three targets store skills as markdown files with optional supporting files in the same directory.

### Sequencing

1. Define target adapter interface and registry (U1)
2. Implement Hermes, Claude Code, Codex adapters (U2)
3. Extend CLI with `--target` and `--scope` flags (U3)
4. Extend config schema for target defaults (U4)
5. Add `--list-targets` subcommand (U5)
6. Add tests (U6)
7. Web UI: display target compatibility in skill detail (U7)
8. Validate and update built-in skills for cross-target compatibility (U8)

---

## Implementation Units

### U1. Target adapter interface and registry

**Goal:** Define the abstraction that each platform adapter implements and a registry that maps target names to adapter instances.

**Requirements:** R1, R4

**Dependencies:** None

**Files:**
- `skillhub/targets/__init__.py` (new)
- `skillhub/targets/base.py` (new)
- `skillhub/targets/registry.py` (new)

**Approach:**
- `TargetAdapter` base class with `resolve_path(skill_name, category, scope) -> Path` and `write_skill(path, files) -> None`
- `TargetScope` enum: `USER`, `PROJECT`
- `TargetRegistry` class holding a dict of name -> adapter
- Three concrete adapters registered at import time

**Patterns to follow:** Existing `SkillStorage` class in `skillhub/storage.py` for file-writing patterns.

**Test scenarios:**
- Happy path: registry returns correct adapter for each name
- Edge case: unknown target name raises clear error
- Edge case: scope resolution produces correct paths for each target

**Verification:** `pytest tests/test_targets.py` passes with all scenarios covered.

---

### U2. Implement platform adapters

**Goal:** Implement the three concrete target adapters with correct directory layouts.

**Requirements:** R4

**Dependencies:** U1

**Files:**
- `skillhub/targets/hermes.py` (new)
- `skillhub/targets/claude_code.py` (new)
- `skillhub/targets/codex.py` (new)

**Approach:**
- **Hermes adapter:** `~/.hermes/skills/<category>/<name>/` (user) or `.hermes/skills/<category>/<name>/` (project). Copies files as-is.
- **Claude Code adapter:** `~/.claude/skills/<name>/SKILL.md` + supporting files (user) or `.claude/skills/<name>/` (project). The main SKILL.md is placed at the root of the skill directory.
- **Codex adapter:** `~/.codex/agents/<name>/AGENTS.md` + supporting files (user) or `.codex/agents/<name>/` (project). Copies SKILL.md as-is under the AGENTS.md filename (no content transformation).

Each adapter handles:
- Path resolution based on scope
- Directory creation
- File writing with conflict detection

**Test scenarios:**
- Happy path: each adapter resolves correct user-level path
- Happy path: each adapter resolves correct project-level path
- Happy path: files are written to the correct location
- Edge case: existing skill directory triggers overwrite confirmation
- Edge case: category is None for non-Hermes targets (ignored)

**Verification:** `pytest tests/test_targets.py` passes; manual install to each target produces correct directory structure.

---

### U3. Extend CLI with --target and --scope flags

**Goal:** Add `--target` and `--scope` options to the `install` command.

**Requirements:** R1, R2, R5

**Dependencies:** U1, U2

**Files:**
- `skillhub/cli/commands/install.py` (modify)

**Approach:**
- Add `--target` option with choices `["hermes", "claude-code", "codex"]`, default from config or `"hermes"`
- Add `--scope` option with choices `["user", "project"]`, default from config or `"user"`
- Replace hardcoded path logic with target adapter resolution
- Keep `--category` flag for Hermes (ignored for other targets)
- Preserve existing overwrite confirmation behavior

**Test scenarios:**
- Happy path: `skillhub install my-skill --target claude-code` installs to `~/.claude/skills/my-skill/`
- Happy path: `skillhub install my-skill --scope project` installs to `./.hermes/skills/...`
- Happy path: `skillhub install my-skill` with config default uses configured target
- Edge case: `--category` with non-Hermes target prints warning and ignores
- Edge case: unknown target name produces clear error

**Verification:** `pytest tests/test_cli_install.py` passes; manual test with each target produces correct output.

---

### U4. Extend config schema for target defaults

**Goal:** Add a `targets` section to `~/.skillhub/config.yaml` for per-target defaults.

**Requirements:** R3

**Dependencies:** None (can be done in parallel with U1-U3)

**Files:**
- `skillhub/config.py` (modify)

**Approach:**
- Add `TargetConfig` model: `name: str`, `scope: str = "user"`, `enabled: bool = True`
- Add `targets: dict[str, TargetConfig]` to `AppConfig`
- Load from YAML `targets:` section
- Environment variable `SKILLHUB_DEFAULT_TARGET` overrides the default target
- Config example:
  ```yaml
  targets:
    hermes:
      scope: user
      enabled: true
    claude-code:
      scope: user
      enabled: true
    codex:
      scope: project
      enabled: true
  ```

**Test scenarios:**
- Happy path: config loads with target defaults
- Happy path: env var overrides default target
- Edge case: missing targets section uses built-in defaults
- Edge case: invalid target config falls back to defaults

**Verification:** `pytest tests/test_config.py` passes.

---

### U5. Add --list-targets subcommand

**Goal:** Show available targets and their configured paths.

**Requirements:** R6

**Dependencies:** U1, U4

**Files:**
- `skillhub/cli/commands/install.py` (modify)
- `skillhub/cli/main.py` (modify — add as subcommand of `install` or as standalone)

**Approach:**
- `skillhub install --list-targets` prints a table of target name, scope, path, and enabled status
- Uses the registry and config to resolve paths
- Output format: plain text table for terminal readability

**Test scenarios:**
- Happy path: lists all three targets with correct paths
- Happy path: shows configured defaults from config file

**Verification:** `skillhub install --list-targets` outputs correct table.

---

### U6. Add tests

**Goal:** Comprehensive test coverage for the new target system.

**Requirements:** All

**Dependencies:** U1-U5

**Files:**
- `tests/test_targets.py` (new)
- `tests/test_cli_install.py` (new)
- `tests/test_config.py` (new — or extend existing)

**Approach:**
- Unit tests for each adapter's path resolution
- Integration tests for the CLI install command with each target
- Config loading tests with target defaults
- Use `tempfile.TemporaryDirectory` for all path-based tests (existing pattern)

**Test scenarios:**
- All scenarios listed in U1-U5 above
- Cross-cutting: install to all three targets in sequence
- Cross-cutting: config defaults + CLI flag override interaction

**Verification:** `pytest tests/` passes with full coverage of new code.

---

### U7. Web UI: display target compatibility

**Goal:** Show which platforms a skill supports and provide install commands in the web UI skill detail view.

**Requirements:** R1 (UI support for multi-target)

**Dependencies:** U1 (target registry)

**Files:**
- `skillhub/static/js/app.js` (modify)
- `skillhub/static/index.html` (modify)
- `skillhub/static/css/style.css` (modify)
- `skillhub/api/skills.py` (modify — include target info in skill detail response)

**Approach:**
- The skill detail API response includes a `targets` field listing compatible platforms (derived from the skill's `platforms` frontmatter metadata, or defaulting to `["hermes"]` if not specified)
- The detail modal in `app.js` renders target badges (e.g., "Hermes", "Claude Code", "Codex") below the skill description
- Each badge shows the platform name; clicking it reveals the install command for that target (e.g., `skillhub install skillhub-server --target claude-code`)
- Add a `target-commands` section to the detail template with pre-formatted CLI commands per target
- Styles: platform badges use distinct colors (Hermes: blue, Claude Code: orange, Codex: green)

**Test scenarios:**
- Happy path: skill with `platforms: [hermes, claude-code]` shows two badges and two install commands
- Happy path: skill without `platforms` metadata shows only Hermes badge (backward compatible)
- Edge case: skill detail API returns empty platforms list → shows Hermes only

**Verification:** Open `http://localhost:8000`, click a skill, verify target badges and install commands appear.

---

### U8. Validate and update built-in skills for cross-target compatibility

**Goal:** Ensure the two built-in skills in `skills/` (`skillhub-server` and `skillhub-client`) install cleanly to all three targets.

**Requirements:** R4 (target adapter correctness)

**Dependencies:** U2 (platform adapters)

**Files:**
- `skills/skillhub-server/SKILL.md` (verify — may need `platforms` metadata update)
- `skills/skillhub-client/SKILL.md` (verify — may need `platforms` metadata update)

**Approach:**
- Read both SKILL.md files and verify their frontmatter includes a `platforms` field listing all supported targets
- If `platforms` is missing, add `platforms: [hermes, claude-code, codex]` to the frontmatter
- Verify that the SKILL.md content (instructions, examples) does not contain Hermes-specific syntax that would break in Claude Code or Codex contexts
- Test: install each skill to all three targets using the CLI and verify files appear correctly
- Note: Codex adapter copies SKILL.md as-is (renamed to AGENTS.md), so the content must be self-contained

**Test scenarios:**
- Happy path: `skillhub install skillhub-server --target hermes` → files in `~/.hermes/skills/...`
- Happy path: `skillhub install skillhub-server --target claude-code` → files in `~/.claude/skills/skillhub-server/`
- Happy path: `skillhub install skillhub-server --target codex` → files in `~/.codex/agents/skillhub-server/AGENTS.md`
- Same three tests for `skillhub-client`

**Verification:** Manual install of both skills to all three targets produces correct directory structures.

---

## Verification Contract

| Gate | Command | Pass condition |
|------|---------|----------------|
| Unit tests | `pytest tests/` | All tests pass |
| CLI smoke test | `skillhub install --list-targets` | Shows 3 targets with paths |
| Install smoke test | `skillhub install skillhub-server --target claude-code` | Files appear in `~/.claude/skills/skillhub-server/` |
| Config test | Create config with targets section, run install | Uses configured defaults |

## Definition of Done

- [ ] `--target` flag works for hermes, claude-code, codex
- [ ] `--scope` flag works for user and project
- [ ] Config file supports per-target defaults
- [ ] `--list-targets` shows available targets
- [ ] Default behavior (no flags) matches current hermes behavior
- [ ] All tests pass
- [ ] README updated with new install options
- [ ] Web UI skill detail shows target badges and install commands
- [ ] Built-in skills (`skillhub-server`, `skillhub-client`) install cleanly to all three targets
