---
name: kb-explore
description: Inspect a Knowledge Bus universe and optionally create or open its offline Explorer.
---

# Explore a Universe

Use this procedure to understand or present declared Knowledge Bus definitions. Explorer is an optional read-only consumer; it does not author definitions or decide whether their contents are true, useful, approved, or applicable to a situation.

## Select and inspect

Follow [Knowledge Bus Directory](references/knowledge-bus-directory.md). An explicit universe file, knowledge-base folder, or its `.knowledge-bus/` folder takes precedence; otherwise use the nearest `.knowledge-bus/` and never fall through an empty nearer scope. Run the bundled command described in [Checker for Agent Workflows](references/agent-runtime.md):

```sh
python3 /absolute/runtime/kbp.py --inspect /absolute/target/.knowledge-bus/
```

Inspection writes nothing. A sole universe may be selected automatically. If the scope contains several, list the candidates and ask the user to select an id or universe file; never choose by filename or sort order. Explain the universe through its questions, artifact purposes, relationships, guidance, and presentation marks. Report conformance and renderability separately.

## Optional static artifact

Before writing, tell the user the proposed destination. The conventional local path is `.knowledge-bus/explorer/<universe-id>/`, but generation always receives an explicit destination:

```sh
python3 /absolute/runtime/kbp.py --explore --universe <id> --output /absolute/destination /absolute/target/.knowledge-bus/
```

Do not replace an existing destination unless the user asks; then add `--replace`. Before recommending replacement, compare the receipt with the current inspection and viewer. Refresh when the definitions, guidance, marks, viewer, or requested presentation changed. A package release alone is not a reason to refresh.

Generation uses bundled files and works offline. Open `index.html` only when requested or useful. Users can export SVG from the viewer; automated export remains contributor and release tooling.

If visualization is unavailable, provide the inspected model or a concise text explanation. Never change definitions, evaluate context, reconstruct an institution, promote descriptive material into an authorized state, or silently ignore invalid or mismatched inputs.
