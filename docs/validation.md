# Validation

Use the checker to find structural errors in definition and guidance files before people or tools rely on them.

## What Gets Checked

The checker uses the protocol's conformance rules to check supported conditions, including:

- required declarations and fields;
- references to declared elements and document types;
- duplicate codes;
- protocol-version compatibility;
- permitted uses of frames and factors;
- guidance references, kinds, and source declarations;
- fields that the format does not allow.

Guidance is checked against the universe it names, so provide both files in the same run.

## What Requires Human Review

Passing means the files meet the checks currently implemented. It does not establish that a question is useful, that an answer is true, or that advice is well supported.

The checker does not yet validate the `answers.yaml` output from ingestion. Protocol rules for instances and exchange should not be read as a claim that those workflows are fully checked.

## Running the Checker

Requires [`uv`](https://docs.astral.sh/uv/). Run these commands from a clone of the repository.

Check the bundled definitions and guidance:

```bash
uv run kbp
```

Check a particular definition file and its guidance:

```bash
uv run kbp --validate path/to/universe.kbp.yaml path/to/type-guidance.kbp.yaml
```

Paths in this example are placeholders for your files. A target folder with `.knowledge-bus/` selects the definition and guidance files in that directory. Explicit file arguments select exactly those files. Generic directory arguments scan `*.kbp.yaml` files while excluding nested folders that contain their own `.knowledge-bus/`.

Without explicit targets, the checker uses the nearest `.knowledge-bus/` from the working directory upward. It never combines definitions from different Knowledge Bus directories or creates a missing `.knowledge-bus/`. In the implementation checkout, it checks bundled `universes/` when no `.knowledge-bus/` directory is found. The package supplies the protocol independently of the working directory. See [Knowledge Bus Directory](knowledge-bus-directory.md).

## Understanding Results

The checker first reports whether the protocol is `SOUND`. It then reports whether each document conforms, with `FAIL` messages describing the problems it found.

Fix the reported declaration or reference and run the check again. A non-zero exit status means the run failed, so scripts and CI can stop on that result.

## Testing the Checker

Before checking documents, the checker checks the protocol itself. This includes checking that fields it expects to read are declared as required. An inconsistent protocol stops the run.

Run that check alone with:

```bash
uv run kbp --self-check
```

The test corpus includes valid documents and five deliberately invalid cases: a duplicate code, a missing required field, an invalid factor reference, an unknown element in a composition, and a mismatched protocol version. Each invalid case must fail with the expected reason. These cases do not cover every possible violation.

Run the tests with:

```bash
just test
```
