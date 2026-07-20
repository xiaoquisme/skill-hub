"""Shared parsing utilities for SkillHub."""

import yaml


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from text content.

    Expects text starting with '---' delimiter.
    Returns the parsed frontmatter as a dict, or empty dict if none found.
    """
    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}
