"""Tests for multi-target skill installation."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from skillhub.targets.base import TargetAdapter, TargetScope
from skillhub.targets.registry import TargetRegistry
from skillhub.targets import registry
from skillhub.targets.hermes import HermesAdapter
from skillhub.targets.claude_code import ClaudeCodeAdapter
from skillhub.targets.codex import CodexAdapter
from skillhub.config import AppConfig, TargetConfig, load_config
from skillhub.storage import SkillStorage


class TestTargetScope:
    def test_enum_values(self):
        assert TargetScope.USER.value == "user"
        assert TargetScope.PROJECT.value == "project"

    def test_from_string(self):
        assert TargetScope("user") == TargetScope.USER
        assert TargetScope("project") == TargetScope.PROJECT


class TestTargetRegistry:
    def test_register_and_get(self):
        reg = TargetRegistry()
        adapter = HermesAdapter()
        reg.register(adapter)
        assert reg.get("hermes") is adapter

    def test_get_unknown_returns_none(self):
        reg = TargetRegistry()
        assert reg.get("unknown") is None

    def test_get_or_raise_unknown_raises(self):
        reg = TargetRegistry()
        with pytest.raises(KeyError, match="Unknown target 'unknown'"):
            reg.get_or_raise("unknown")

    def test_targets_property(self):
        reg = TargetRegistry()
        reg.register(HermesAdapter())
        reg.register(ClaudeCodeAdapter())
        assert reg.targets == ["claude-code", "hermes"]

    def test_list_all(self):
        reg = TargetRegistry()
        reg.register(HermesAdapter())
        reg.register(CodexAdapter())
        adapters = reg.list_all()
        assert len(adapters) == 2
        names = [a.name for a in adapters]
        assert "codex" in names
        assert "hermes" in names


class TestGlobalRegistry:
    def test_has_all_three_targets(self):
        assert set(registry.targets) == {"hermes", "claude-code", "codex"}


class TestHermesAdapter:
    def setup_method(self):
        self.adapter = HermesAdapter()

    def test_name_and_description(self):
        assert self.adapter.name == "hermes"
        assert self.adapter.description == "Hermes Agent"

    def test_resolve_user_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.USER)
        assert path == Path.home() / ".hermes" / "skills" / "uncategorized" / "my-skill"

    def test_resolve_user_path_with_category(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.USER, "ai")
        assert path == Path.home() / ".hermes" / "skills" / "ai" / "my-skill"

    def test_resolve_project_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.PROJECT)
        assert path == Path.cwd() / ".hermes" / "skills" / "uncategorized" / "my-skill"

    def test_write_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir) / "test-skill"
            files = {"SKILL.md": b"# Test", "helper.py": b"# Helper"}
            written = self.adapter.write_skill(install_dir, files)
            assert len(written) == 2
            assert (install_dir / "SKILL.md").read_bytes() == b"# Test"
            assert (install_dir / "helper.py").read_bytes() == b"# Helper"


class TestClaudeCodeAdapter:
    def setup_method(self):
        self.adapter = ClaudeCodeAdapter()

    def test_name_and_description(self):
        assert self.adapter.name == "claude-code"
        assert self.adapter.description == "Claude Code"

    def test_resolve_user_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.USER)
        assert path == Path.home() / ".claude" / "skills" / "my-skill"

    def test_resolve_project_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.PROJECT)
        assert path == Path.cwd() / ".claude" / "skills" / "my-skill"

    def test_category_ignored(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.USER, "ai")
        assert path == Path.home() / ".claude" / "skills" / "my-skill"

    def test_write_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir) / "test-skill"
            files = {"SKILL.md": b"# Test"}
            written = self.adapter.write_skill(install_dir, files)
            assert len(written) == 1
            assert (install_dir / "SKILL.md").read_bytes() == b"# Test"


class TestCodexAdapter:
    def setup_method(self):
        self.adapter = CodexAdapter()

    def test_name_and_description(self):
        assert self.adapter.name == "codex"
        assert self.adapter.description == "Codex"

    def test_resolve_user_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.USER)
        assert path == Path.home() / ".codex" / "agents" / "my-skill"

    def test_resolve_project_path(self):
        path = self.adapter.resolve_path("my-skill", TargetScope.PROJECT)
        assert path == Path.cwd() / ".codex" / "agents" / "my-skill"

    def test_write_skill_renames_skillmd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir) / "test-skill"
            files = {"SKILL.md": b"# Test", "helper.py": b"# Helper"}
            written = self.adapter.write_skill(install_dir, files)
            # SKILL.md should be renamed to AGENTS.md
            assert not (install_dir / "SKILL.md").exists()
            assert (install_dir / "AGENTS.md").read_bytes() == b"# Test"
            assert (install_dir / "helper.py").read_bytes() == b"# Helper"

    def test_write_skill_non_skillmd_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir) / "test-skill"
            files = {"README.md": b"# Readme"}
            written = self.adapter.write_skill(install_dir, files)
            assert (install_dir / "README.md").read_bytes() == b"# Readme"


class TestTargetConfig:
    def test_default_config_has_targets(self):
        config = AppConfig()
        assert "hermes" in config.targets
        assert "claude-code" in config.targets
        assert "codex" in config.targets

    def test_target_config_defaults(self):
        config = AppConfig()
        assert config.targets["hermes"].scope == "user"
        assert config.targets["hermes"].enabled is True

    def test_load_config_with_targets(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
targets:
  hermes:
    scope: project
    enabled: false
  claude-code:
    scope: user
    enabled: true
""")
        config = load_config(config_file)
        assert config.targets["hermes"].scope == "project"
        assert config.targets["hermes"].enabled is False
        assert config.targets["claude-code"].scope == "user"

    def test_load_config_missing_targets_uses_defaults(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("server:\n  port: 9000\n")
        config = load_config(config_file)
        assert "hermes" in config.targets
        assert config.targets["hermes"].scope == "user"

    def test_load_config_default_target_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SKILLHUB_DEFAULT_TARGET", "claude-code")
        config = load_config()
        keys = list(config.targets.keys())
        assert keys[0] == "claude-code"

    def test_load_config_default_target_env_var_invalid(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SKILLHUB_DEFAULT_TARGET", "nonexistent")
        config = load_config()
        # Should be silently ignored, hermes stays first
        keys = list(config.targets.keys())
        assert keys[0] == "hermes"

    def test_load_config_default_target_env_var_with_config_file(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
targets:
  hermes:
    scope: project
    enabled: true
  codex:
    scope: user
    enabled: true
""")
        monkeypatch.setenv("SKILLHUB_DEFAULT_TARGET", "codex")
        config = load_config(config_file)
        keys = list(config.targets.keys())
        assert keys[0] == "codex"
        assert config.targets["codex"].scope == "user"


class TestExtractPlatformsFromSkillmd:
    """Tests for _extract_platforms_from_skillmd (P0 finding)."""

    def _make_storage(self, tmp_path, skill_id, content):
        storage = SkillStorage(tmp_path / "skills")
        storage.save_skill_file(skill_id, "SKILL.md", content)
        return storage

    def test_extracts_targets_field(self, tmp_path):
        storage = self._make_storage(tmp_path, "s1", b"---\ntargets: [hermes, claude-code]\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s1", storage)
        assert result == ["hermes", "claude-code"]

    def test_falls_back_to_platforms_field(self, tmp_path):
        storage = self._make_storage(tmp_path, "s2", b"---\nplatforms: [linux, macos]\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s2", storage)
        assert result == ["linux", "macos"]

    def test_no_frontmatter_defaults_hermes(self, tmp_path):
        storage = self._make_storage(tmp_path, "s3", b"# Just a heading\nNo frontmatter here")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s3", storage)
        assert result == ["hermes"]

    def test_empty_frontmatter_defaults_hermes(self, tmp_path):
        storage = self._make_storage(tmp_path, "s4", b"---\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s4", storage)
        assert result == ["hermes"]

    def test_missing_skillmd_defaults_hermes(self, tmp_path):
        storage = SkillStorage(tmp_path / "skills")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("nonexistent", storage)
        assert result == ["hermes"]

    def test_malformed_yaml_defaults_hermes(self, tmp_path):
        storage = self._make_storage(tmp_path, "s6", b"---\ntargets: [unclosed\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s6", storage)
        assert result == ["hermes"]

    def test_targets_not_list_defaults_hermes(self, tmp_path):
        storage = self._make_storage(tmp_path, "s7", b"---\ntargets: hermes\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s7", storage)
        assert result == ["hermes"]

    def test_all_three_targets(self, tmp_path):
        storage = self._make_storage(tmp_path, "s8", b"---\ntargets: [hermes, claude-code, codex]\n---\n# Skill")
        from skillhub.api.skills import _extract_platforms_from_skillmd
        result = _extract_platforms_from_skillmd("s8", storage)
        assert result == ["hermes", "claude-code", "codex"]


class TestCliInstallCommand:
    """Tests for the CLI install command's new --target/--scope options."""

    def test_install_help_shows_target_option(self):
        from skillhub.cli.commands.install import install
        runner = CliRunner()
        result = runner.invoke(install, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--scope" in result.output
        assert "--yes" in result.output

    def test_install_unknown_target_exits_with_error(self):
        from skillhub.cli.commands.install import install
        runner = CliRunner()
        result = runner.invoke(install, ["test-skill", "--target", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown target" in result.output or "Error" in result.output
