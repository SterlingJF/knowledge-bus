"""Real npm installation of assembled agent packages in disposable projects.

This verifies the registry/package-manager boundary, not host chat behavior.
"""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import plugin


def files(path):
    return {
        p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file()
    }


def check(output=None, public_version=None):
    with tempfile.TemporaryDirectory(prefix="knowledge-bus-native-") as temporary:
        base = Path(temporary).resolve()
        artifacts = Path(output).resolve() if output else base / "artifacts"
        if output is None:
            plugin.build(plugin.HOSTS, output=artifacts)
        env = {
            **os.environ,
            "npm_config_cache": str(base / "npm-cache"),
            "npm_config_userconfig": str(base / "empty.npmrc"),
            "DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
        }
        (base / "empty.npmrc").write_text("")
        for host in plugin.HOSTS:
            (report_path,) = artifacts.glob(
                f"knowledge-bus-plugin-{host}-*.report.json"
            )
            report = json.loads(report_path.read_text())
            project = base / host
            project.mkdir()
            (project / "package.json").write_text('{"private":true}\n')
            archive = report_path.with_name(
                report_path.name.replace(".report.json", ".tgz")
            )
            source = (
                report["package"] + "@" + public_version
                if public_version
                else str(archive)
            )
            for _ in range(2):
                command = [
                    "npm",
                    "install",
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                    "--registry",
                    "https://registry.npmjs.org/",
                    source,
                ]
                result = subprocess.run(
                    command,
                    cwd=project,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                installed = project / "node_modules" / report["package"]
                if files(installed) != report["file_hashes"]:
                    raise ValueError(
                        f"{host}: npm-installed files differ from the verified package."
                    )
                scope = project / "node_modules/@knowledge-bus"
                if {p.name for p in scope.iterdir()} != {
                    report["package"].split("/")[1]
                }:
                    raise ValueError("An unrelated agent package was installed.")
            plugin.runtime_check(installed)
            if host == "opencode":
                result = plugin.run(
                    "node",
                    "--input-type=module",
                    "-e",
                    "const {default: p}=await import(process.argv[1]); const c={}; "
                    "await (await p()).config(c); console.log(JSON.stringify(c));",
                    (installed / "index.js").as_uri(),
                    cwd=project,
                    env=env,
                )
                if json.loads(result)["skills"]["paths"] != [str(installed / "skills")]:
                    raise ValueError(
                        "OpenCode package did not register its own skill path."
                    )
            print(
                f"{host}: real npm install/reinstall, exact contents, and checker runtime passed."
            )
        print(
            "Host CLI registration and chat behavior are separate from these npm checks."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument(
        "--public-version",
        help="Read-only public npm install smoke test after publication",
    )
    args = parser.parse_args()
    check(args.artifacts, args.public_version)
