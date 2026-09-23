"""Publish verified agent packages and GitHub releases. Not an end-user installer."""

import argparse
import base64
import hashlib
import json
import re
import subprocess
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "SterlingJF/knowledge-bus"
HOSTS = ("claude", "codex", "pi", "opencode")
REGISTRY = "https://registry.npmjs.org/"
TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
VISIBILITY_CHECKS = 31
VISIBILITY_INTERVAL = 10


def version_key(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError("Expected a stable vX.Y.Z release tag.")
    return tuple(map(int, match.groups()))


def command(*args):
    """Run commands, inheriting stdio for interactive npm publication."""
    if args[:2] == ("npm", "publish"):
        subprocess.run(args, check=True)
        return ""
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def integrity(path):
    return (
        "sha512-"
        + base64.b64encode(hashlib.sha512(path.read_bytes()).digest()).decode()
    )


def write_manifest(folder, tag, commit, root=ROOT):
    version_key(tag)
    version = tag[1:]
    folder = Path(folder)
    assets = {
        p.name: {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        }
        for p in sorted(folder.iterdir())
        if p.is_file()
        and p.name not in ("release.json", "SHA256SUMS", "release-notes.md")
    }
    required = {
        f"knowledge_bus-{version}-py3-none-any.whl",
        f"knowledge_bus-{version}.tar.gz",
    }
    packages = {}
    for host in HOSTS:
        stem = f"knowledge-bus-plugin-{host}-{version}"
        required.update((stem + ".tgz", stem + ".report.json"))
        report = json.loads((folder / (stem + ".report.json")).read_text())
        name = f"@knowledge-bus/{host}"
        if (
            report["version"] != version
            or report["host"] != host
            or report["package"] != name
            or not report["runtime_checked"]
        ):
            raise ValueError(
                "Release requires checked packages matching its version and identity."
            )
        archive = folder / (stem + ".tgz")
        if report["sha256"] != assets[archive.name]["sha256"]:
            raise ValueError("Package report does not match archive.")
        with tarfile.open(archive) as tar:
            contents = {
                m.name.removeprefix("package/"): hashlib.sha256(
                    tar.extractfile(m).read()
                ).hexdigest()
                for m in tar.getmembers()
                if m.isfile()
            }
            package = json.load(tar.extractfile("package/package.json"))
        if (
            contents != report["file_hashes"]
            or package["name"] != name
            or package["version"] != version
        ):
            raise ValueError("Packed contents differ from the verified package.")
        if (
            package.get("private") is not False
            or package.get("scripts")
            or package.get("bin")
        ):
            raise ValueError("Unsafe or non-publishable agent package.")
        packages[host] = {
            "name": name,
            "archive": archive.name,
            "integrity": integrity(archive),
            "files": report["file_hashes"],
        }
    if set(assets) != required:
        raise ValueError(f"Unexpected release assets: {set(assets) ^ required}")
    data = {
        "schema": 2,
        "repository": REPOSITORY,
        "tag": tag,
        "commit": commit,
        "assets": assets,
        "packages": packages,
    }
    (folder / "release.json").write_text(json.dumps(data, indent=2) + "\n")
    sums = [f"{entry['sha256']}  {name}" for name, entry in sorted(assets.items())]
    sums.append(
        hashlib.sha256((folder / "release.json").read_bytes()).hexdigest()
        + "  release.json"
    )
    (folder / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return data


def npm_view(spec, field, run=command):
    """Read one registry value across npm's scalar and array JSON formats."""
    try:
        raw = run(
            "npm",
            "view",
            spec,
            field,
            "--json",
            "--prefer-online",
            "--registry",
            REGISTRY,
        )
        if not raw.strip():
            return None
        value = json.loads(raw)
        if value is None:
            return None
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if not isinstance(value, str) or not value:
            raise ValueError(f"Unexpected npm lookup result for {spec} {field}")
        return value
    except subprocess.CalledProcessError as error:
        for output in (error.stdout, error.stderr):
            try:
                if json.loads(output or "{}").get("error", {}).get("code") == "E404":
                    return None
            except json.JSONDecodeError:
                pass
        raise


def check_packages(metadata, run=command):
    """Preflight every target before changing GitHub or npm state."""
    version = metadata["tag"][1:]
    for attempt in range(VISIBILITY_CHECKS):
        pending = []
        for item in metadata["packages"].values():
            found = npm_view(item["name"] + "@" + version, "dist.integrity", run)
            if found is not None and found != item["integrity"]:
                raise ValueError(
                    "Published bytes differ; never overwrite an npm version."
                )
            latest = npm_view(item["name"], "dist-tags.latest", run)
            if latest and version_key("v" + latest) > version_key(metadata["tag"]):
                raise ValueError("Refusing to move a newer npm latest tag backwards.")
            if found is not None and latest != version:
                pending.append(item["name"])
        if not pending:
            return
        if attempt + 1 < VISIBILITY_CHECKS:
            time.sleep(VISIBILITY_INTERVAL)
    raise ValueError(
        "Existing version is not latest after the registry visibility window; "
        "repair its tag interactively before retrying."
    )


def publish_packages(folder, metadata, run=command):
    version = metadata["tag"][1:]
    for item in metadata["packages"].values():
        spec = item["name"] + "@" + version
        found = npm_view(spec, "dist.integrity", run)
        if found is not None and found != item["integrity"]:
            raise ValueError(
                f"Published bytes differ for {spec}; never overwrite an npm version."
            )
        if found is None:
            run(
                "npm",
                "publish",
                str(folder / item["archive"]),
                "--access",
                "public",
                "--tag",
                "latest",
                "--ignore-scripts",
                "--registry",
                REGISTRY,
            )


def verify_packages(metadata, run=command):
    """Wait for the complete release to become visible before exposing GitHub."""
    version = metadata["tag"][1:]
    for attempt in range(VISIBILITY_CHECKS):
        pending = []
        for item in metadata["packages"].values():
            spec = item["name"] + "@" + version
            found = npm_view(spec, "dist.integrity", run)
            if found is not None and found != item["integrity"]:
                raise ValueError(
                    f"Published bytes differ for {spec}; never overwrite an npm version."
                )
            latest = npm_view(item["name"], "dist-tags.latest", run)
            if latest and version_key("v" + latest) > version_key(metadata["tag"]):
                raise ValueError("Refusing to move a newer npm latest tag backwards.")
            if found != item["integrity"] or latest != version:
                pending.append(spec)
        if not pending:
            return
        if attempt + 1 < VISIBILITY_CHECKS:
            time.sleep(VISIBILITY_INTERVAL)
    raise TimeoutError(
        f"{', '.join(pending)} did not appear with the expected integrity and latest "
        f"tag within {(VISIBILITY_CHECKS - 1) * VISIBILITY_INTERVAL} seconds; "
        "repair a missing latest tag interactively before retrying."
    )


def should_be_latest(tag, releases, on_main):
    current = version_key(tag)
    return not any(
        not r["draft"]
        and not r["prerelease"]
        and r.get("published_at")
        and TAG.fullmatch(r["tag_name"])
        and version_key(r["tag_name"]) > current
        and on_main(r["tag_name"])
        for r in releases
    )


def publish(folder, tag, run=command):
    folder = Path(folder).resolve()
    metadata = json.loads((folder / "release.json").read_text())
    version_key(tag)
    commit = run("git", "rev-parse", "HEAD").strip()
    if run("git", "rev-parse", tag + "^{commit}").strip() != commit:
        raise ValueError("Release tag does not identify the checkout.")
    if (
        metadata["tag"] != tag
        or metadata["commit"] != commit
        or metadata["repository"] != REPOSITORY
    ):
        raise ValueError("Release metadata does not match the checkout.")
    run("git", "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main")
    if set(metadata["packages"]) != set(HOSTS):
        raise ValueError("Release packages must match the configured agents.")
    for name, expected in metadata["assets"].items():
        if Path(name).name != name:
            raise ValueError("Invalid asset filename.")
        path = folder / name
        if (
            hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]
            or path.stat().st_size != expected["bytes"]
        ):
            raise ValueError("Release asset changed after verification.")
    for host, item in metadata["packages"].items():
        if (
            item["name"] != f"@knowledge-bus/{host}"
            or item["archive"] not in metadata["assets"]
        ):
            raise ValueError("Unexpected package publication target.")
        if integrity(folder / item["archive"]) != item["integrity"]:
            raise ValueError("Package integrity changed.")
    pages = json.loads(
        run(
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{REPOSITORY}/releases?per_page=100",
        )
    )
    releases = [r for page in pages for r in page]

    def on_main(ref):
        comparison = json.loads(
            run("gh", "api", f"repos/{REPOSITORY}/compare/{ref}...main")
        )
        return comparison["status"] in ("ahead", "identical")

    if not should_be_latest(tag, releases, on_main):
        raise ValueError(
            "Refusing to publish an older release over a newer stable release."
        )
    check_packages(metadata, run)
    existing = next((r for r in releases if r["tag_name"] == tag), None)
    published = existing is not None and not existing["draft"]
    if published:
        if existing["prerelease"] or not existing.get("published_at"):
            raise ValueError("Expected a published stable release.")
        remote = json.loads(
            run(
                "gh",
                "release",
                "download",
                tag,
                "--pattern",
                "release.json",
                "--output",
                "-",
            )
        )
        if remote != metadata:
            raise ValueError(
                "Never overwrite an existing release with different content."
            )
    else:
        if existing is None:
            run(
                "gh",
                "release",
                "create",
                tag,
                "--draft",
                "--verify-tag",
                "--title",
                f"Knowledge Bus {tag}",
                "--notes-file",
                str(folder / "release-notes.md"),
            )
        paths = [folder / name for name in metadata["assets"]] + [
            folder / "release.json",
            folder / "SHA256SUMS",
        ]
        manifest_path = folder / "release.json"
        if existing is None:
            run("gh", "release", "upload", tag, str(manifest_path))
            run(
                "gh",
                "release",
                "upload",
                tag,
                *map(str, (p for p in paths if p != manifest_path)),
            )
        else:
            remote = json.loads(run("gh", "release", "view", tag, "--json", "assets"))
            sizes = {a["name"]: a["size"] for a in remote["assets"]}
            if "release.json" in sizes:
                remote_manifest = json.loads(
                    run(
                        "gh",
                        "release",
                        "download",
                        tag,
                        "--pattern",
                        "release.json",
                        "--output",
                        "-",
                    )
                )
                if remote_manifest != metadata:
                    raise ValueError(
                        "Never overwrite an existing release with different content."
                    )
            elif sizes:
                raise ValueError(
                    "Existing draft has assets without a release manifest."
                )
            else:
                run("gh", "release", "upload", tag, str(manifest_path))
            run(
                "gh",
                "release",
                "upload",
                tag,
                *map(str, (p for p in paths if p != manifest_path)),
                "--clobber",
            )
        remote = json.loads(run("gh", "release", "view", tag, "--json", "assets"))
        sizes = {a["name"]: a["size"] for a in remote["assets"]}
        if any(sizes.get(p.name) != p.stat().st_size for p in paths):
            raise ValueError("Uploaded release assets are missing or incomplete.")
    publish_packages(folder, metadata, run)
    verify_packages(metadata, run)
    if not published:
        run("gh", "release", "edit", tag, "--draft=false", "--latest=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("manifest", "publish"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("tag")
    args = parser.parse_args()
    if args.mode == "manifest":
        write_manifest(
            args.folder, args.tag, command("git", "rev-parse", "HEAD").strip()
        )
    else:
        publish(args.folder, args.tag)
