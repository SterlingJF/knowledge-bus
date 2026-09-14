"""README commands, native catalog identities, and removal of custom installation."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_readme_commands_match_native_catalogs_and_packages():
    readme = (ROOT / "README.md").read_text()
    section = readme.split("## Installation\n", 1)[1].split("## Quick Start", 1)[0]
    commands = [
        line
        for _, block in re.findall(r"```(sh|text)\n(.*?)```", section, re.DOTALL)
        for line in block.strip().splitlines()
    ]
    expected = [
        "/plugin marketplace add SterlingJF/knowledge-bus",
        "/plugin install knowledge-bus@knowledge-bus",
        "claude plugin marketplace add SterlingJF/knowledge-bus",
        "claude plugin install knowledge-bus@knowledge-bus",
        "codex plugin marketplace add SterlingJF/knowledge-bus",
        "codex plugin add knowledge-bus@knowledge-bus",
        "pi install npm:@knowledge-bus/pi@latest",
        "opencode plugin @knowledge-bus/opencode@latest",
        "npx skills add SterlingJF/knowledge-bus",
        "npx skills add SterlingJF/knowledge-bus --skill kb-check",
    ]
    assert commands[: len(expected)] == expected
    assert "install.py" not in section and "<module>" not in section
    for host, location in (("claude", ".claude-plugin"), ("codex", ".agents/plugins")):
        catalog = json.loads((ROOT / location / "marketplace.json").read_text())
        assert catalog["name"] == "knowledge-bus"
        (entry,) = catalog["plugins"]
        assert entry["name"] == "knowledge-bus"
        package = json.loads(
            (ROOT / f"plugins/{host}/knowledge-bus/package.json").read_text()
        )
        assert entry["source"] == {
            "source": "npm",
            "package": package["name"],
            "version": "latest",
            "registry": "https://registry.npmjs.org",
        }
    for host in ("pi", "opencode"):
        package = json.loads(
            (ROOT / f"plugins/{host}/knowledge-bus/package.json").read_text()
        )
        assert package["name"] + "@latest" in section


def test_no_custom_installer_or_product_cli_claim():
    assert not (ROOT / "tools/plugin/install.py").exists()
    for host in ("claude", "codex", "pi", "opencode"):
        package = json.loads(
            (ROOT / f"plugins/{host}/knowledge-bus/package.json").read_text()
        )
        assert package["name"] == f"@knowledge-bus/{host}"
        assert package["private"] is True  # Only assembled artifacts are published.
        assert "bin" not in package
