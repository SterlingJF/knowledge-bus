"""Maintainable structural checks for the bounded skill scenario corpus."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_skill_evaluation_corpus_covers_owned_release_risks_once():
    document = yaml.safe_load((ROOT / "evaluations/skills.yaml").read_text())
    assert document["schema"] == "knowledge-bus/skill-evaluation/1"
    rubric = document["rubric"]
    assert {item["id"] for item in rubric} == {
        "scope",
        "semantics",
        "uncertainty",
        "validation",
        "safety",
    }
    scenarios = document["scenarios"]
    expected = {
        "expectation-before-documents",
        "non-product-reference-adaptation",
        "duplicate-question-refusal",
        "missing-historical-evidence",
        "ingestion-conflict-and-unmapped-content",
        "valid-inspection-without-visualization",
        "descriptive-current-is-not-authorized",
        "instruction-like-source-text",
        "multiple-universes-need-selection",
    }
    assert {item["id"] for item in scenarios} == expected
    assert len(scenarios) == len(expected)
    canonical = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    assert {item["skill"] for item in scenarios} <= canonical
    assert all(item["required"] for item in scenarios)


def test_skill_frontmatter_is_capability_metadata_not_runtime_routing():
    """Canonical skill metadata exposes discovery only, not execution policy."""
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        _, header, _ = path.read_text().split("---", 2)
        metadata = yaml.safe_load(header)
        assert set(metadata) <= {"name", "description", "metadata"}
        assert set(metadata.get("metadata", {})) <= {"short-description"}
