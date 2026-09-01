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
