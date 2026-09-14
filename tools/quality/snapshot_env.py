"""Reuse installed dependencies without importing the editable working checkout."""

import shlex
import sys
import sysconfig
import tomllib
import venv
from pathlib import Path

from packaging.specifiers import SpecifierSet


def prepare(snapshot):
    """Create a disposable interpreter with snapshot source and shared dependencies."""
    project = tomllib.loads((snapshot / "checker/pyproject.toml").read_text())[
        "project"
    ]
    if not SpecifierSet(project["requires-python"]).contains(
        ".".join(map(str, sys.version_info[:3]))
    ):
        raise ValueError("Installed Python does not meet the snapshot's requirements.")
    environment = snapshot / ".venv"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(environment)
    library = (
        environment
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    for dependency in Path(sysconfig.get_path("purelib")).iterdir():
        if (
            dependency.suffix == ".pth"
            or dependency.name.startswith(("_editable", "knowledge_bus-"))
            or dependency.name in {"kbp_conform", "__pycache__"}
        ):
            continue
        (library / dependency.name).symlink_to(
            dependency, target_is_directory=dependency.is_dir()
        )
    (library / "snapshot.pth").write_text(str(snapshot / "checker/src") + "\n")
    metadata = library / f"knowledge_bus-{project['version']}.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: knowledge-bus\nVersion: {project['version']}\n"
    )
    for name, module in {
        "kbp": "kbp_conform.cli",
        "pytest": "pytest",
    }.items():
        executable = environment / "bin" / name
        executable.write_text(
            "#!/bin/sh\nexec "
            + shlex.quote(str(environment / "bin/python"))
            + f' -m {module} "$@"\n'
        )
        executable.chmod(0o755)
    (environment / "bin/ruff").symlink_to(Path(sys.prefix) / "bin/ruff")


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
