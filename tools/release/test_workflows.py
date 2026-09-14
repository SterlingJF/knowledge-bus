"""Hosted verification prerequisites and publication boundaries."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("workflow", "job", "command"),
    [
        ("ci.yml", "checks", "pnpm run check"),
        ("release.yml", "verify", "tools/release/release.py check"),
    ],
)
def test_full_checks_have_just_available(workflow, job, command):
    data = yaml.safe_load((ROOT / ".github/workflows" / workflow).read_text())
    steps = data["jobs"][job]["steps"]
    setup = next(
        i
        for i, step in enumerate(steps)
        if step.get("uses", "").startswith("extractions/setup-just@")
    )
    check = next(i for i, step in enumerate(steps) if command in step.get("run", ""))
    assert setup < check


def test_release_keeps_native_checks_and_oidc_gate():
    data = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    jobs = data["jobs"]
    assert set(jobs["publish"]["needs"]) == {"verify", "native-hosts"}
    assert jobs["publish"]["permissions"]["id-token"] == "write"
    assert jobs["public-smoke"]["needs"] == "publish"
