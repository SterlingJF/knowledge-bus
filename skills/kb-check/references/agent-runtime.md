# Checker for Agent Workflows

Read this when a workflow needs validation or code minting.

## Locate the Runtime

Resolve paths from the loaded skill's directory, not from the shell's working directory.

- An individually installed skill has its own `runtime/kbp.py`.
- In a full plugin, the shared `runtime/kbp.py` is two directories above the skill directory.

Use the first location that exists. If neither exists, report an incomplete installation rather than running a different checker.

## Run the Checker

Requires [uv](https://docs.astral.sh/uv/) and Python matching `requires_python` in the runtime's `requirements.json`. The launcher reports the requirement if the invoking interpreter is too old. Use the resolved absolute launcher path:

```sh
python3 /absolute/runtime/kbp.py --validate /absolute/target/.knowledge-bus/
python3 /absolute/runtime/kbp.py --mint element 1 /absolute/target/.knowledge-bus/
python3 /absolute/runtime/kbp.py --inspect /absolute/target/.knowledge-bus/
python3 /absolute/runtime/kbp.py --explore --output /absolute/output /absolute/target/.knowledge-bus/
```

The bundled wheel supplies the checker, protocol, and required Python code. The launcher uses bundled files without registry access, keeps its cache outside the installation, and preserves the caller's working directory and failure exit code. If a prerequisite is missing, report it; do not install tools without permission.

Supply an absolute universe file, knowledge-base folder, or its `.knowledge-bus/` folder when the shell is elsewhere. Checking never initializes a folder. `.knowledge-bus/` is the reserved Knowledge Bus configuration directory, not the knowledge base itself. `KNOWLEDGE_BUS_CACHE_DIR` optionally selects another cache location.

`--inspect` prints an Explorer model and writes nothing. When the scope contains several universes, select one with `--universe`. `--explore` requires an output directory and refuses existing output unless `--replace` is supplied. It builds an offline Explorer from the bundled viewer.

## References

The references directory containing this guide includes `knowledge-bus-protocol.yaml`. Read it when authoring or interpreting definitions. The ingestion skill also provides `product-development/` for adopting or adapting the starter. These are reference files, not the user's definitions; do not copy them automatically.

## Interpreting Results

The checker first checks that its protocol is sound. It checks definitions and guidance for required fields, code collisions, references, version compatibility, and permitted structures. Include the universe when checking its guidance.

Each failure names the offending declaration or reference. Explain how to correct the reported problem. Report conformance and Explorer renderability separately. A passing result does not establish that a question is useful or that an answer is true. Answers and ingestion logs still require human review.
