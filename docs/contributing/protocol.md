# Protocol Contributions

The Knowledge Bus Protocol defines:

- what a universe is;
- how a universe breaks knowledge into parts;
- what happens when a document moves between universes.

The checker enforces the protocol. This path suits spec writers and Python developers.

## When to Open an Issue First

Always open an issue first. A rule change can make existing files fail. Maintainers approve each rule change before work starts.

Open a [Proposal](https://github.com/SterlingJF/knowledge-bus/issues/new/choose):

- Include a real file that shows the problem.
- Fill in the current and proposed wording for each rule you would change.
- List the files that pass now but would fail after your change.

Say in the issue whether you will build the change. If not, another contributor may build it once the issue is accepted.

## What You Can Change

You can change the [protocol definition](../../protocol/knowledge-bus-protocol.yaml), the example files under `protocol/conformance/`, and the checker and explorer code the rule needs.

If only one subject's definitions need the change, follow [Universe Contributions](universe.md).

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

## Proof to Bring

Change one rule per pull request. Include its example files and its checker and explorer changes, so both tools accept the same files once it merges.

| Change | Add |
| --- | --- |
| New field or newly valid shape | A file in `protocol/conformance/pass/` that uses the new field or shape |
| New refusal | A file in `protocol/conformance/fail/` with only that defect, named after the defect. Add its expected message to `EXPECTED` in `checker/tests/test_conformance.py`. |
| New header key | A `header_since` entry for it in the protocol definition |
| Renamed key | A `renamed` entry with the old name and the version it changed in |
| Key with a changed shape | A `reshaped` entry with the old shape and the version it changed in |

If you add a file to `protocol/conformance/fail/`, raise the count of invalid cases in [Validation](../validation.md#testing-the-checker) to match, or `just test` fails.

- [ ] `just skills-build` run, regenerated files included.

## Handing Over

Commit with the `protocol` [scope](../../CONTRIBUTING.md#commits). Open the pull request from the template and bring what [every pull request](../../CONTRIBUTING.md#every-pull-request) needs.

---

Adapted from [Archify's CONTRIBUTING](https://github.com/tt-a1i/archify/blob/fae6186f20bf56106e68252a607aa8a9fb0e8f9e/CONTRIBUTING.md).
