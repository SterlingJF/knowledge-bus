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
