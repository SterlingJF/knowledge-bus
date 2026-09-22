"""Product-development relationships and composition."""

from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    ("artifact_id", "expected_mode"),
    [
        ("product-strategy-canvas", "links"),
        ("startup-canvas", "links"),
        ("success-metrics", "owns"),
    ],
    ids=["strategy-references", "startup-references", "metrics-owns"],
)
def test_north_star_is_core_with_declared_ownership(artifact_id, expected_mode):
    path = (
        Path(__file__).resolve().parents[2]
        / "universes/product-development/universe.kbp.yaml"
    )
    universe = yaml.safe_load(path.read_text())
    artifact = next(a for a in universe["artifacts"] if a["id"] == artifact_id)
    matches = [
        (strength, entry.get("mode", "owns"), entry.get("when"))
        for strength, entries in artifact["composition"].items()
        for member in entries
        for entry in [member if isinstance(member, dict) else {"element": member}]
        if entry["element"] == "north-star-metric"
    ]
    assert matches == [("core", expected_mode, None)]


@pytest.mark.parametrize("source", ["macro-environment-factors", "competitor-profile"])
def test_external_analysis_feeds_opportunities_and_threats(source):
    path = (
        Path(__file__).resolve().parents[2]
        / "universes/product-development/universe.kbp.yaml"
    )
    universe = yaml.safe_load(path.read_text())
    edges = {(edge["from"], edge["to"], edge["kind"]) for edge in universe["relations"]}
    target = "external-opportunities-threats"
    assert (source, target, "feeds") in edges
    assert (target, source, "feeds") not in edges
