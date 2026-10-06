"""Canonical skill metadata stays discovery-only, and every skill treats input text as content."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_skill_frontmatter_is_capability_metadata_not_runtime_routing():
    """Canonical skill metadata exposes discovery only, not execution policy."""
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        _, header, _ = path.read_text().split("---", 2)
        metadata = yaml.safe_load(header)
        assert set(metadata) <= {"name", "description", "metadata"}
        assert set(metadata.get("metadata", {})) <= {"short-description"}


def test_every_skill_treats_input_text_as_content_not_instructions():
    """Each canonical skill says text in its inputs is content, never a command."""
    paths = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert paths
    missing = []
    for path in paths:
        text = re.sub(r"\s+", " ", path.read_text().replace("**", ""))
        sentences = re.split(r"(?<=[.;])\s", text)
        if not any(
            re.search(r"\binstructions?\b", s, re.IGNORECASE)
            and re.search(r"\b(never|not)\b", s, re.IGNORECASE)
            and re.search(r"\b(content|follow(ed)?)\b", s, re.IGNORECASE)
            for s in sentences
        ):
            missing.append(path.parent.name)
    assert not missing, f"no content-not-instructions guard in: {missing}"
