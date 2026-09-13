# Validate a spec against the format definition.
validate *ARGS:
    uv run kbp --validate {{ARGS}}

# Generate new unique keys (codes) for a given spec.
mint kind count="1":
    uv run kbp --mint {{kind}} {{count}}

# Run the test suite
test:
    uv run pytest -q

# Type-check the format definition itself
self-check:
    uv run kbp --self-check

# Prepare release metadata without committing or tagging.
release-prepare version:
    uv run --locked python scripts/release.py prepare {{quote(version)}}

# Validate release metadata and distributions.
release-check:
    uv run --locked python scripts/release.py check

# Verify clean main and create an annotated local tag. Never pushes.
release-tag:
    uv run --locked python scripts/release.py tag
