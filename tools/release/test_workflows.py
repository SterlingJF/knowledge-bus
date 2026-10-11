"""Hosted verification prerequisites and publication boundaries."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("workflow", "job", "command"),
    [
        ("ci.yml", "checks-static", "pnpm run check:fast"),
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


def test_ci_skips_package_and_explorer_work_only_on_a_copy_only_change():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    code = "${{ needs.changes.outputs.lane == 'code' }}"
    lane = "\n".join(step.get("run", "") for step in jobs["changes"]["steps"])
    assert "tools/quality/lane.mjs" in lane
    assert jobs["changes"]["steps"][0]["with"]["fetch-depth"] == 0
    for job in ("explorer-unit", "explorer-browser", "explorer-shots"):
        assert jobs[job]["needs"] == "changes"
        assert jobs[job]["if"] == code
    assert jobs["native-hosts"]["needs"] == "changes"
    assert "if" not in jobs["native-hosts"]
    assert all(step.get("if") == code for step in jobs["native-hosts"]["steps"])
    gated = {
        step["run"]: step.get("if")
        for step in jobs["checks-static"]["steps"]
        if "run" in step
    }
    for command in (
        "pnpm run check:plugins",
        "pnpm run check:explorer:gallery",
        "uv run --locked python tools/plugin/check_skills_install.py",
        "uv run --locked python tools/plugin/check_native_install.py",
    ):
        assert gated[command] == code
    for command in ("pnpm run check:fast", "pnpm run test", "uv run kbp --validate"):
        assert gated[command] is None


def test_ci_checks_aggregate_every_split_lane_and_keep_outputs():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    lanes = {"checks-static", "explorer-unit", "explorer-browser", "explorer-shots"}
    assert set(jobs["checks"]["needs"]) == lanes | {"changes"}
    assert "always()" in jobs["checks"]["if"]
    verdict = "\n".join(step.get("run", "") for step in jobs["checks"]["steps"])
    for job in ("changes", "checks-static"):
        assert f'test "${{{{ needs.{job}.result }}}}" = success' in verdict
    assert all(
        f'"${{{{ needs.{lane}.result }}}}"' in verdict
        for lane in lanes - {"checks-static"}
    )
    assert (
        'test "$result" = success || { test "$LANE" = copy && test "$result" = skipped; }'
        in verdict
    )
    commands = {
        lane: "\n".join(step.get("run", "") for step in jobs[lane]["steps"])
        for lane in lanes
    }
    assert all(
        f"pnpm run {script}" in commands["checks-static"]
        for script in ("check:fast", "check:plugins", "test", "check:explorer:gallery")
    )
    assert all(
        command in commands["checks-static"]
        for command in (
            "tools/plugin/check_skills_install.py",
            "kbp --validate",
            "tools/plugin/check_native_install.py",
        )
    )
    assert "pnpm run test:explorer:unit" in commands["explorer-unit"]
    assert all(
        f"pnpm run {script}" in commands["explorer-browser"]
        for script in (
            "test:explorer:adapter",
            "build:explorer",
            "render:explorer",
            "test:explorer:browser",
            "check:explorer:artifacts",
        )
    )
    assert all(
        f"pnpm run {script}" in commands["explorer-shots"]
        for script in ("build:explorer", "render:explorer", "capture:explorer:step")
    )
    uploads = {
        lane: [
            step.get("with", {}).get("name")
            for step in jobs[lane]["steps"]
            if step.get("uses", "").startswith("actions/upload-artifact@")
        ]
        for lane in ("explorer-browser", "explorer-shots")
    }
    assert uploads == {
        "explorer-browser": ["explorer"],
        "explorer-shots": ["explorer-shots-step"],
    }
    assert jobs["native-hosts"]["strategy"]["matrix"]["host"] == [
        "claude",
        "codex",
        "pi",
        "opencode",
    ]


def test_release_keeps_native_checks_and_oidc_gate():
    data = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    jobs = data["jobs"]
    assert set(jobs["publish"]["needs"]) == {"verify", "native-hosts"}
    assert jobs["publish"]["permissions"]["id-token"] == "write"
    assert jobs["public-smoke"]["needs"] == "publish"
