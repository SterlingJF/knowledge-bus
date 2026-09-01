# Validation

The checker validates the format against itself before it validates anything of yours.

## Self-check first

One convention binds the checker: a key the code subscripts must be a key the format requires,
checked before anything reads it. An unsound format stops the run with a named failure, not a
`KeyError` deep in a loop.

## What gets checked

Seventeen registered validity clauses — 11 on spec files, 6 on guidance files — plus the
unsanctioned-field rule: a file carrying keys the format does not declare is refused, not skimmed.

## The refusal corpus

Every registered refusal has a file in `tests/conformance/fail/` that must be refused for its own
reason, not merely rejected — a refusal nobody has written a file for is a refusal nobody has
tested. Five today: a duplicate code, a declaration missing a required key, a predicate naming a
factor, a composition referencing an undeclared element, a wrong `conforms_to`.

## Running it

```bash
uv run kbp                 # format self-check + every spec from the repo root
uv run kbp --validate a.kbp.yaml b.kbp.yaml
just test                  # the refusal corpus
```

Exit is non-zero on any refusal. Given no arguments, the checker finds the format and every spec
from the repository root; given nothing to check, it refuses rather than reporting success.
