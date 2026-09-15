"""Publication state-machine tests: no real registry writes or GitHub mutations."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "publisher", ROOT / "tools/release/publish.py"
)
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


@pytest.fixture
def release(tmp_path):
    metadata = {
        "schema": 2,
        "repository": publish.REPOSITORY,
        "tag": "v0.5.0",
        "commit": "a" * 40,
        "assets": {},
        "packages": {},
    }
    for host in publish.HOSTS:
        archive = tmp_path / f"{host}.tgz"
        archive.write_bytes(host.encode())
        metadata["assets"][archive.name] = {
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "bytes": archive.stat().st_size,
        }
        metadata["packages"][host] = {
            "name": f"@knowledge-bus/{host}",
            "archive": archive.name,
            "integrity": publish.integrity(archive),
        }
    (tmp_path / "release.json").write_text(json.dumps(metadata))
    (tmp_path / "SHA256SUMS").write_text("fixture")
    (tmp_path / "release-notes.md").write_text("fixture")
    return tmp_path, metadata


class Services:
    def __init__(self, folder, metadata):
        self.folder, self.metadata = folder, metadata
        self.calls, self.releases = [], []
        self.packages, self.latest = {}, {}
        self.fail_host = None
        self.fail_after_publish = None
        self.missing_asset = False

    def __call__(self, *args):
        self.calls.append(args)
        if args[:2] == ("git", "rev-parse"):
            return self.metadata["commit"]
        if args[:2] == ("git", "merge-base"):
            return ""
        if args[:2] == ("gh", "api"):
            return (
                json.dumps({"status": "ahead"})
                if "/compare/" in args[-1]
                else json.dumps([self.releases])
            )
        if args[:3] == ("gh", "release", "create"):
            self.releases.append(
                {
                    "tag_name": "v0.5.0",
                    "draft": True,
                    "prerelease": False,
                    "published_at": None,
                }
            )
        elif args[:3] == ("gh", "release", "view"):
            return json.dumps(
                {
                    "assets": []
                    if self.missing_asset
                    else [
                        {"name": p.name, "size": p.stat().st_size}
                        for p in self.folder.iterdir()
                    ]
                }
            )
        elif args[:3] == ("gh", "release", "download"):
            return json.dumps(self.metadata)
        elif args[:3] == ("gh", "release", "edit"):
            item = next(r for r in self.releases if r["tag_name"] == "v0.5.0")
            item.update(draft=False, published_at="now")
        elif args[:2] == ("npm", "view"):
            if args[3] == "dist-tags.latest":
                return json.dumps(self.latest.get(args[2]))
            return json.dumps(self.packages.get(args[2]))
        elif args[:2] == ("npm", "publish"):
            host = Path(args[2]).stem
            if self.fail_host == host:
                raise subprocess.CalledProcessError(1, args)
            item = self.metadata["packages"][host]
            self.packages[item["name"] + "@0.5.0"] = item["integrity"]
            self.latest[item["name"]] = "0.5.0"
            if self.fail_after_publish == host:
                raise subprocess.CalledProcessError(1, args)
        elif args[:2] == ("npm", "dist-tag"):
            raise AssertionError(
                "OIDC publication must not require dist-tag management."
            )
        return ""


def test_complete_release_publishes_github_before_npm_latest(release):
    folder, metadata = release
    services = Services(*release)
    publish.publish(folder, "v0.5.0", services)
    publish_indices = [
        i for i, c in enumerate(services.calls) if c[:2] == ("npm", "publish")
    ]
    visible = next(
        i for i, c in enumerate(services.calls) if c[:3] == ("gh", "release", "edit")
    )
    assert len(publish_indices) == len(services.latest) == len(metadata["packages"])
    assert visible < min(publish_indices)
    assert all(
        c[c.index("--tag") + 1] == "latest"
        for c in services.calls
        if c[:2] == ("npm", "publish")
    )


def test_partial_npm_publication_resumes_without_overwriting(release):
    folder, _ = release
    services = Services(*release)
    services.fail_host = "pi"
    with pytest.raises(subprocess.CalledProcessError):
        publish.publish(folder, "v0.5.0", services)
    assert len(services.latest) == 2 and not services.releases[0]["draft"]
    services.fail_host = None
    count = len(services.calls)
    publish.publish(folder, "v0.5.0", services)
    subsequent = [c for c in services.calls[count:] if c[:2] == ("npm", "publish")]
    assert [Path(c[2]).stem for c in subsequent] == ["pi", "opencode"]
    assert not any(c[:3] == ("gh", "release", "upload") for c in services.calls[count:])


def test_successful_publish_with_lost_response_resumes_without_republishing(release):
    folder, _ = release
    services = Services(*release)
    services.fail_after_publish = "pi"
    with pytest.raises(subprocess.CalledProcessError):
        publish.publish(folder, "v0.5.0", services)
    assert not services.releases[0]["draft"]
    services.fail_after_publish = None
    count = len(services.calls)
    publish.publish(folder, "v0.5.0", services)
    assert len(services.latest) == len(services.metadata["packages"])
    assert not any(c[:3] == ("gh", "release", "upload") for c in services.calls[count:])
    assert [
        Path(c[2]).stem for c in services.calls[count:] if c[:2] == ("npm", "publish")
    ] == ["opencode"]


def test_missing_assets_prevent_npm_publication(release):
    folder, _ = release
    services = Services(*release)
    services.missing_asset = True
    with pytest.raises(ValueError, match="assets"):
        publish.publish(folder, "v0.5.0", services)
    assert not services.packages


def test_conflicting_npm_version_never_overwritten(release):
    folder, _ = release
    services = Services(*release)
    services.packages["@knowledge-bus/claude@0.5.0"] = "different"
    with pytest.raises(ValueError, match="bytes differ"):
        publish.publish(folder, "v0.5.0", services)
    assert not services.latest
    assert not any(c[:2] == ("npm", "publish") for c in services.calls)


def test_older_release_cannot_displace_newer_stable_release(release):
    folder, _ = release
    services = Services(*release)
    services.releases = [
        {
            "tag_name": "v0.6.0",
            "draft": False,
            "prerelease": False,
            "published_at": "now",
        }
    ]
    with pytest.raises(ValueError, match="older release"):
        publish.publish(folder, "v0.5.0", services)
    assert not services.latest
    assert not any(
        c[:2] == ("npm", "publish") or c[:2] == ("gh", "release")
        for c in services.calls
    )


def test_latest_selection_excludes_drafts_prereleases_and_unmerged_tags():
    releases = [
        {
            "tag_name": "v9.0.0",
            "draft": True,
            "prerelease": False,
            "published_at": None,
        },
        {
            "tag_name": "v8.0.0",
            "draft": False,
            "prerelease": True,
            "published_at": "now",
        },
        {
            "tag_name": "v7.0.0",
            "draft": False,
            "prerelease": False,
            "published_at": "now",
        },
    ]
    assert publish.should_be_latest("v0.5.0", releases, lambda tag: False)
    assert not publish.should_be_latest("v0.5.0", releases, lambda tag: True)


@pytest.mark.parametrize(
    "code,missing", [("E404", True), ("E401", False), ("ECONNRESET", False)]
)
def test_npm_lookup_fails_closed_except_missing_versions(code, missing):
    def fail(*args):
        raise subprocess.CalledProcessError(
            1, args, output=json.dumps({"error": {"code": code}})
        )

    if missing:
        assert publish.npm_view("package", "version", fail) is None
    else:
        with pytest.raises(subprocess.CalledProcessError):
            publish.npm_view("package", "version", fail)


@pytest.mark.parametrize("value", ["sha512-example", "0.5.0"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_npm_lookup_normalizes_single_values(value, wrapped):
    response = [value] if wrapped else value
    assert (
        publish.npm_view("package", "field", lambda *args: json.dumps(response))
        == value
    )


@pytest.mark.parametrize("response", [[], ["a", "b"], {}, [None]])
def test_npm_lookup_rejects_unexpected_results(response):
    with pytest.raises(ValueError, match="Unexpected npm lookup"):
        publish.npm_view("package", "field", lambda *args: json.dumps(response))


def test_changed_local_assets_never_publish(release):
    folder, _ = release
    (folder / "pi.tgz").write_bytes(b"changed")
    services = Services(*release)
    with pytest.raises(ValueError, match="changed"):
        publish.publish(folder, "v0.5.0", services)
    assert not services.packages


def test_preflight_checks_all_packages_before_any_external_write(release):
    services = Services(*release)
    services.packages["@knowledge-bus/opencode@0.5.0"] = "different"
    with pytest.raises(ValueError, match="bytes differ"):
        publish.publish(release[0], "v0.5.0", services)
    assert not any(
        c[:2] == ("gh", "release") or c[:2] == ("npm", "publish")
        for c in services.calls
    )


def test_newer_npm_latest_blocks_release_before_writes(release):
    services = Services(*release)
    services.latest["@knowledge-bus/opencode"] = "0.6.0"
    with pytest.raises(ValueError, match="backwards"):
        publish.publish(release[0], "v0.5.0", services)
    assert not services.releases and not services.packages


def test_existing_version_with_missing_latest_requires_manual_repair(release):
    services = Services(*release)
    item = release[1]["packages"]["pi"]
    services.packages[item["name"] + "@0.5.0"] = item["integrity"]
    with pytest.raises(ValueError, match="repair its tag interactively"):
        publish.publish(release[0], "v0.5.0", services)
    assert not services.releases


def test_completed_release_retry_has_no_external_writes(release):
    services = Services(*release)
    publish.publish(release[0], "v0.5.0", services)
    count = len(services.calls)
    publish.publish(release[0], "v0.5.0", services)
    assert not any(
        c[:2] == ("npm", "publish")
        or c[:3] in (("gh", "release", "upload"), ("gh", "release", "edit"))
        for c in services.calls[count:]
    )


def test_tag_must_match_checkout(release):
    services = Services(*release)

    def wrong_tag(*args):
        if args[:3] == ("git", "rev-parse", "v0.5.0^{commit}"):
            return "b" * 40
        return services(*args)

    with pytest.raises(ValueError, match="tag does not identify"):
        publish.publish(release[0], "v0.5.0", wrong_tag)
    assert not services.releases


def test_release_workflow_uses_oidc_without_optional_publication():
    import yaml

    workflow_text = (ROOT / ".github/workflows/release.yml").read_text()
    workflow = yaml.safe_load(workflow_text)
    job = workflow["jobs"]["publish"]
    assert job["permissions"]["id-token"] == "write"
    assert job["runs-on"] == "ubuntu-latest"
    assert "NPM_TOKEN" not in workflow_text and "NODE_AUTH_TOKEN" not in workflow_text
    steps = job["steps"]
    assert any("npm@12.0.2" in s.get("run", "") for s in steps)
    npm = next(
        i for i, s in enumerate(steps) if "publish.py publish" in s.get("run", "")
    )
    assert "if" not in steps[npm]
    assert "if" not in workflow["jobs"]["public-smoke"]
    assert workflow["concurrency"]["cancel-in-progress"] is False
