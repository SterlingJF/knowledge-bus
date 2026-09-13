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

Paths in this example are placeholders for your files. A directory argument includes every `*.kbp.yaml` file beneath it.

Without explicit paths, the checker searches upward from the working directory for a `spec/` directory and uses the accompanying `universes/` directory. It reports an error if it cannot find the protocol or has no documents to check.

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
