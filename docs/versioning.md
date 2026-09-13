# Versioning

Knowledge Bus has one release version. Its protocol, universes, and guidance have independent versions.

## Version Contract

| Version | Source of truth | Identifies |
| --- | --- | --- |
| Release | `pyproject.toml` | The shipped checker, skills, docs, and bundled content |
| Protocol | `spec/knowledge-bus-protocol.yaml` | The conformance rules |
| Universe | Each universe's `version` | A revision of that definition set |
| Guidance | Each guidance file's `version` | A revision of that guidance |

The Claude plugin version mirrors the release version. Git tags use `v<release-version>`. Tags identify commits; they are not branches.

For example, release `0.6.0` can bundle protocol `kbp/0.5` and product-development universe and guidance versions `0.5`. Those numbers do not need to match. A document's `conforms_to` names the protocol, not the application release.

`kbp --version` reports the installed release and bundled protocol. An explicit protocol argument can override the bundled protocol when checking files.

## Compatibility

Release versions use `X.Y.Z`. While releases remain `0.x`, patches preserve documented behavior; minor releases may change it. Call out breaking changes in release notes. Prerelease suffixes are not supported by the release commands yet.

Change the protocol version when its conformance contract changes. Change universe or guidance versions when their contents change. Release preparation does not change any of these automatically.

The checker requires an exact protocol-version match. It does not infer compatibility between protocol versions.

Never move or reuse a published release tag. Fix a released defect in a new release.

## Release Preparation

Use a short-lived feature branch and start from a clean working tree:

```sh
just release-prepare 0.6.0
```

This updates the package and plugin versions, refreshes the lockfile, and inserts a changelog entry with the bundled protocol version. Replace the TODO with user-facing changes, including any breaking behavior. A failed preparation restores the four files it edits.

Preparation leaves changes unstaged. It does not commit, tag, push, or publish. It rejects versions no greater than the current release and tags already present locally. Tagging later fetches remote tags and checks again.

```sh
just release-check
```

Checks cover version alignment, release notes, lockfile consistency, tests, protocol soundness, bundled definitions, and installed distributions outside the checkout. The source archive must also rebuild successfully.

Review and commit the changes, merge through the normal PR workflow, then delete the feature branch. There are no release branches.

## Tagging

Switch to an up-to-date, clean `main` checkout:

```sh
just release-tag
```

This fetches `origin/main` and tags, requires local `main` to match it, runs release checks, and creates an annotated local tag. It never pushes.

Publish the tag explicitly, replacing the example version:

```sh
git push origin refs/tags/v0.6.0
```

This pushes a tag, not a branch. Commit prefixes do not trigger releases.

## GitHub Releases

Pushing a `v*` tag triggers verification. The workflow requires an annotated tag matching the manifests and changelog, on a commit contained in `main`. It tests and builds before a separate job creates the GitHub Release and attaches the wheel and source archive.

Only the publishing job has release-write permission. No PyPI publishing is configured. A failed verification produces no GitHub Release. Fix and rerun transient failures without moving the tag; code changes require a new release. The workflow does not overwrite an existing GitHub Release.

## History

[Release history](../CHANGELOG.md) records shipped software changes. [Protocol history](../spec/CHANGELOG.md) records conformance changes. Older release notes that did not identify an exact version remain labeled as historical notes rather than assigned a new version.
