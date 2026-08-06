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
