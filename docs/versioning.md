# Versioning

Knowledge Bus releases, the protocol, universes, and guidance have independent versions.

## Versions

| Version  | Source of truth                        | Identifies                                             |
| -------- | -------------------------------------- | ------------------------------------------------------ |
| Release  | `checker/pyproject.toml`               | The shipped checker, skills, docs, and bundled content |
| Protocol | `protocol/knowledge-bus-protocol.yaml` | The conformance rules                                  |
| Universe | Each universe's `version`              | A revision of that definition set                      |
| Guidance | Each guidance file's `version`         | A revision of that guidance                            |

Agent package versions and versioned plugin manifests mirror the release version. Git tags use `v<release-version>`.

Explorer changes ship with a Knowledge Bus release but do not change the protocol or universe. Receipts record the producing release and the exact model and viewer. A packaging change alone does not change the model's identity.

For example, release `0.6.0` can bundle protocol `kbp/0.5` and product-development universe and guidance versions `0.5`. Those numbers do not need to match. A document's `conforms_to` names the protocol, not the application release.

`kbp --version` reports the installed release and bundled protocol. An explicit protocol argument can override the bundled protocol when checking files.

## Compatibility

Release versions use `X.Y.Z`. While releases remain `0.x`, patches preserve documented behavior; minor releases may change it. Release notes identify breaking changes.

The protocol version changes when its conformance rules change. Universe and guidance versions track changes to their definitions and advice. Explorer-only and packaging changes leave those versions unchanged.

The checker requires an exact protocol-version match. It does not infer compatibility between protocol versions.

## Installation Versions

Native agent packages use npm's `latest` tag to select the latest published stable release. Each agent controls how installed packages are refreshed; see [update instructions](agent-plugins.md#updates).

The general `npx skills add SterlingJF/knowledge-bus` command installs from the default branch, which can include unreleased changes. An explicit GitHub tree/tag URL selects a particular version.

## History

[Release history](../CHANGELOG.md) records shipped software changes. [Protocol history](../protocol/CHANGELOG.md) records conformance changes.
