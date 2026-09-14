"""Native CLI smoke checks, exclusively on disposable GitHub-hosted runners."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import plugin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--host", choices=plugin.HOSTS, required=True)
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
    ):
        parser.error(
            "Only disposable GitHub-hosted runners may run native registration tests."
        )
    host = args.host
    artifacts = args.artifacts.resolve()
    (report_path,) = artifacts.glob(f"knowledge-bus-plugin-{host}-*.report.json")
    report = json.loads(report_path.read_text())
    archive = report_path.with_name(report_path.name.replace(".report.json", ".tgz"))
    with tempfile.TemporaryDirectory(prefix="kb-host-cli-") as temporary:
        base = Path(temporary)
        installed = base / "catalog/plugins/knowledge-bus"
        plugin.unpack(archive, installed)
        catalog_root = base / "catalog"
        entry = {"name": "knowledge-bus", "source": "./plugins/knowledge-bus"}
        if host == "claude":
            catalog = {
                "name": "knowledge-bus",
                "owner": {"name": "Fixture"},
                "plugins": [entry],
            }
            plugin.json_write(catalog_root / ".claude-plugin/marketplace.json", catalog)
        if host == "codex":
            entry.update(
                source={"source": "local", "path": "./plugins/knowledge-bus"},
                policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                category="Productivity",
            )
            plugin.json_write(
                catalog_root / ".agents/plugins/marketplace.json",
                {"name": "knowledge-bus", "plugins": [entry]},
            )
        project = base / "project"
        project.mkdir()
        env = {**os.environ, "DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1"}

        def run(command):
            result = subprocess.run(
                command,
                cwd=project,
                env=env,
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(f"{command}:\n{result.stdout}\n{result.stderr}")
            return result.stdout

        source = "SterlingJF/knowledge-bus" if args.public else str(catalog_root)
        if host in ("claude", "codex"):
            run([host, "plugin", "marketplace", "add", source])
            verb = "install" if host == "claude" else "add"
            for _ in range(2):
                run([host, "plugin", verb, "knowledge-bus@knowledge-bus"])
            run(
                [
                    host,
                    "plugin",
                    "marketplace",
                    "update" if host == "claude" else "upgrade",
                    "knowledge-bus",
                ]
            )
            run(
                [
                    host,
                    "plugin",
                    "update" if host == "claude" else "add",
                    "knowledge-bus@knowledge-bus",
                ]
            )
            listing = run([host, "plugin", "list"])
            if "knowledge-bus" not in listing:
                raise ValueError("Native plugin listing did not contain Knowledge Bus.")
        elif host == "pi":
            source = (
                "npm:" + report["package"] + "@latest"
                if args.public
                else str(installed)
            )
            for _ in range(2):
                run(["pi", "install", source])
            if "knowledge-bus" not in run(["pi", "list"]):
                raise ValueError("Pi did not register the package.")
            if args.public:
                run(["pi", "update", "--extension", source])
        else:
            source = (
                report["package"] + "@latest" if args.public else "file:" + str(archive)
            )
            run(["opencode", "plugin", source])
            run(["opencode", "plugin", source, "--force"])
            discovered = run(["opencode", "debug", "skill"])
            if not all(name in discovered for name in plugin.SKILLS):
                raise ValueError("OpenCode did not discover every bundled skill.")
        print(
            f"{host}: native CLI registration/repeat/refresh passed ({'public' if args.public else 'local transport'})."
        )
        print("This is not a chat interaction or model-quality test.")


if __name__ == "__main__":
    main()
