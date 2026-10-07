# Checker Contributions

The checker validates definition and guidance files and generates new codes for definitions. This path suits Python developers and QA engineers.

## When to Open an Issue First

You don't need an issue when the checker crashes, prints an unclear message or refuses a valid file. Open a pull request with a test that fails before your fix.

Open an issue first if your change would make an existing file fail the checker. If the rule itself is wrong, follow [Protocol Contributions](protocol.md).

## What You Can Change

You can change the checker in `checker/src/kbp_conform/` and its tests in `checker/tests/`. The proof below may also need example files and the Validation guide.

Every change must follow these rules:

- Don't add a runtime dependency. The checker has none and carries its own copy of PyYAML.
- Don't edit the generated copies under `skills/*/runtime/` or `skills/*/references/`. Edit the source and rebuild.
- Follow [Development](../development.md#other-changes) for packaging and CI changes.

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

## Run It Locally

`uv run --locked pytest -q checker/tests` runs the checker tests. `just validate <files>` checks the files you name.

## Proof to Bring

Fix one problem per pull request, with its test in the same commit.

| Fix | Add |
| --- | --- |
| Valid file refused | The smallest version of the refused file, in `protocol/conformance/pass/` |
| Invalid file accepted | A file in `protocol/conformance/fail/` with only that defect, named after the defect. Add its expected message to `EXPECTED` in `checker/tests/test_conformance.py`. |
| Crash or unclear message | A test in `checker/tests/` that fails before the fix |

If you add a file to `protocol/conformance/fail/`, raise the count of invalid cases in [Validation](../validation.md#testing-the-checker) to match, or `just test` fails.

- [ ] `just skills-build` run, regenerated files included.

## Handing Over

Commit with the `checker` [scope](../../CONTRIBUTING.md#commits). Open the pull request from the template and bring what [every pull request](../../CONTRIBUTING.md#every-pull-request) needs.

---

Adapted from [Archify's CONTRIBUTING](https://github.com/tt-a1i/archify/blob/fae6186f20bf56106e68252a607aa8a9fb0e8f9e/CONTRIBUTING.md).
