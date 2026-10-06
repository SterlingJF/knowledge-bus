"""Run the generated Claude cases against the freshly assembled Claude plugin.

    run_claude.py [claude plugin eval options, e.g. --case 'element-question-*' --runs 1]

Assembles the plugin as the release build does, places evals/generated/claude/ under it as its
eval directory, and writes results to .evidence/<date>/evals/claude-<time>/. Every run calls
paid models: the agent under test, and the llm graders' judge.
"""

import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import spec as spec_module
import write_claude

ROOT = spec_module.ROOT
sys.path.insert(0, str(ROOT / "tools/plugin"))

import plugin


def command(plugin_dir, out, extra):
    return [
        "claude", "plugin", "eval", str(plugin_dir), "--trust-plugin", "--no-publish",
        "--output-dir", str(out), "--json", str(out / "result.json"), *extra,
    ]  # fmt: skip


def main(argv=None):
    extra = sys.argv[1:] if argv is None else argv
    files, _ = write_claude.render(spec_module.load())
    if write_claude.drift(write_claude.OUT, files):
        sys.exit("Generated cases are stale; run `just evals-write` first.")
    stamp = datetime.now(UTC)
    out = (
        ROOT
        / ".evidence"
        / f"{stamp:%Y-%m-%d}"
        / "evals"
        / f"claude-{stamp:%Y%m%dT%H%M%SZ}"
    )
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="evals-claude-") as folder:
        base = Path(folder)
        plugin.run(
            "uv",
            "build",
            "--package",
            "knowledge-bus",
            "--wheel",
            "--out-dir",
            str(base / "wheel"),
        )
        (wheel,) = (base / "wheel").glob("*.whl")
        target = base / "knowledge-bus"
        plugin.assemble("claude", target, wheel)
        shutil.copytree(
            write_claude.OUT, target / "evals", ignore=shutil.ignore_patterns("results")
        )
        done = subprocess.run(command(target, out, extra), check=False)
    print(out)
    return done.returncode


if __name__ == "__main__":
    sys.exit(main())
