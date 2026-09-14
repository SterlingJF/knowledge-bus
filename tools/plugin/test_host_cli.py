"""Native marketplace command selection without touching personal agent settings."""

import check_host_cli
import pytest


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("git_source", [False, True])
def test_marketplace_commands_match_source(host, git_source):
    commands = []
    source = "SterlingJF/knowledge-bus" if git_source else "/fixture/catalog"

    def run(command):
        commands.append(command)
        return "knowledge-bus" if command[-1] == "list" else ""

    check_host_cli.check_marketplace(host, source, git_source=git_source, run=run)
    verb = "install" if host == "claude" else "add"
    expected = [
        [host, "plugin", "marketplace", "add", source],
        [host, "plugin", verb, "knowledge-bus@knowledge-bus"],
        [host, "plugin", verb, "knowledge-bus@knowledge-bus"],
    ]
    if host == "claude" or git_source:
        expected.extend(
            [
                [
                    host,
                    "plugin",
                    "marketplace",
                    "update" if host == "claude" else "upgrade",
                    "knowledge-bus",
                ],
                [
                    host,
                    "plugin",
                    "update" if host == "claude" else "add",
                    "knowledge-bus@knowledge-bus",
                ],
            ]
        )
    assert commands == [*expected, [host, "plugin", "list"]]


def test_local_codex_does_not_request_git_upgrade():
    def run(command):
        if "upgrade" in command:
            raise RuntimeError("marketplace is not configured as a Git marketplace")
        return "knowledge-bus"

    check_host_cli.check_marketplace(
        "codex", "/fixture/catalog", git_source=False, run=run
    )


def test_git_upgrade_failure_is_not_suppressed():
    def run(command):
        if "upgrade" in command:
            raise RuntimeError("refresh failed")
        return "knowledge-bus"

    with pytest.raises(RuntimeError, match="refresh failed"):
        check_host_cli.check_marketplace(
            "codex", "SterlingJF/knowledge-bus", git_source=True, run=run
        )


@pytest.mark.parametrize("git_source", [False, True])
def test_missing_plugin_discovery_fails(git_source):
    with pytest.raises(ValueError, match="listing did not contain"):
        check_host_cli.check_marketplace(
            "codex", "fixture", git_source=git_source, run=lambda _: ""
        )
