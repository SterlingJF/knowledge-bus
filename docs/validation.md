# Validation

Use the checker to find structural errors in definition and guidance files before people or tools rely on them.

## What Gets Checked

The checker uses the protocol's conformance rules to check supported conditions, including:

- required declarations and fields;
- references to declared elements and document types;
- duplicate codes;
- protocol-version compatibility, including fields an older declared version does not allow and keys renamed between versions (a `kbp/0.8` universe writes `no_artifact`; a `kbp/0.7` universe writes `empty_composition`);
- universe `terms`: unique, with a nonblank term and meaning;
- permitted uses of frames and factors;
- the ordering frame: from `kbp/0.9`, a universe spec with elements declares exactly one ordering frame, and a universe spec with no element declares no ordering frame;
- relation edge gates: from `kbp/0.8`, each key is a declared frame or `latency`, each value is one that frame declares, `latency` is a nonblank string, and no frame is named `latency`;
- guidance references, kinds, and source declarations;
- fields that the format does not allow.

Guidance is checked against the universe it names, so provide both files in the same run.

## What Requires Human Review

Passing means the definitions and guidance meet the structural checks currently implemented. Explorer inspection separately reports whether the selected universe can be rendered. Neither result establishes that a question is useful, that an answer is true, or that advice is well supported.

The checker does not yet validate `answers.yaml` or `ingest-log.md`, the files that ingestion writes. Both are review-only for now; validating them is on the [roadmap](../README.md#roadmap). The protocol defines rules for instances and exchange, but the checker does not validate those workflows fully.

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

Paths in this example are placeholders for your files. A target folder with `.knowledge-bus/` selects the definition and guidance files in that directory. Explicit file arguments select exactly those files. The checker applies the rules in [Nested Folders](knowledge-bus-directory.md#nested-folders) to an explicit `.knowledge-bus/workspace.yaml` argument. For generic directory arguments, the checker scans `*.kbp.yaml` files and skips nested folders that contain their own `.knowledge-bus/`.

Without explicit targets, the checker uses the nearest `.knowledge-bus/` from the working directory upward. It never combines definitions from different Knowledge Bus directories or creates a missing `.knowledge-bus/`. When the selected `.knowledge-bus/workspace.yaml` lists universe specs of the parent folder under `from_parent`, the checker also checks `workspace.yaml` and those universe specs, one block per file; see [Nested Folders](knowledge-bus-directory.md#nested-folders). In the implementation checkout, it checks bundled `universes/` when no `.knowledge-bus/` directory is found. The package supplies the protocol independently of the working directory. See [Knowledge Bus Directory](knowledge-bus-directory.md).

Inspect one universe without writing:

```bash
uv run kbp --inspect path/to/.knowledge-bus/
```

When the scope contains several universes, select one with `--universe <id>` or target its file. Duplicate ids and ambiguous guidance or marks fail.

Print the card for one document type, or list every document type:

```bash
uv run kbp --card <kind> path/to/.knowledge-bus/
uv run kbp --kinds path/to/.knowledge-bus/
```

`--card` and `--kinds` skip marks files. When the scope holds several universe specs, `--kinds` without `--universe` prints one group per universe spec. See [Document Type Card](document-type-card.md).

## Understanding Results

The checker first reports whether the protocol is `SOUND`. It then reports whether each document conforms, with `FAIL` messages describing the problems it found.

Fix the reported declaration or reference and run the check again. A non-zero exit status means the run failed, so scripts and CI can stop on that result.

## Testing the Checker

Before checking documents, the checker checks the protocol itself. This includes checking that fields it expects to read are declared as required. An inconsistent protocol stops the run.

Run that check alone with:

```bash
uv run kbp --self-check
```

The test corpus includes valid documents and 34 deliberately invalid cases, among them a duplicate code, a missing required field, an unknown element in a composition, a mismatched protocol version, and a document using a key from the wrong protocol version. Each invalid case must fail with the expected reason. These cases do not cover every possible violation.

Run the tests with:

```bash
just test
```
