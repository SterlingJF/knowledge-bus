# Universes

A universe is a populated vocabulary declared in KBP: the elements, artifact types, frames and
factors a particular domain cares about.

**The universes here are reference content, not requirements.** The protocol does not name them,
does not depend on them, and conformance to KBP does not mean conformance to any universe in this
directory. Declaring your own is the expected case, not the exception — `docs/` describes the
procedure this project follows, and you are under no obligation to follow it.

`product-development/` is the universe this project maintains and the one the checker is tested
against. It carries its own version, independent of the protocol's.

A universe declares two documents: the universe itself, and the type guidance that says how to
answer its elements well. Both are checked, guidance against the universe it names.

## Presentation is a third sibling, and it is not a protocol document

`marks.explorer.yaml` declares what mark a concept is drawn with. It sits beside the universe for
the reason type guidance does — the universe says what things mean, a sibling says how they look,
and meaning stays uncontaminated by rendering. It is **not** a KBP document: the protocol's
`document_types` are `universe` and `guidance` only, it names nothing about drawing, and the
filename deliberately stays out of the `*.kbp.yaml` glob the checker validates. It is read by the
Explorer's own adapter, `tools/explorer/prepare_model.py --marks`, which refuses a mark naming a
concept the universe does not declare, a malformed mark, and two concepts declaring one mark.

A mark is exactly one of:

| key | value | drawn as |
| --- | --- | --- |
| `monogram` | one or two letters or digits | text centred in the 24-unit icon box |
| `glyph` | SVG path data, starting with a move and carrying at least one number | a stroked path on the 24-unit grid |

Path data is required to be inline because the artifact is self-contained: a reference — a URL, a
`url(...)`, a fragment, a filename, or a name in some table the viewer is assumed to hold — cannot
travel inside it, and `tools/explorer/check-artifacts.mjs` refuses one.

**Declaring is optional, and a concept the document leaves out is not unmarked.** The Explorer
derives a monogram from the concept's own label, unique across the model. Declared wins; absence
derives.
