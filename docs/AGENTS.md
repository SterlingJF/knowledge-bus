# Knowledge Bus docs

Mintlify site for Knowledge Bus. Pages are MDX with YAML frontmatter; navigation, colors and links live in `docs.json`.

## Terminology

- Knowledge Bus is the project; the Knowledge Bus Protocol is its conformance contract.
- A universe spec declares knowledge elements, document types and their relations. Say "document type" in prose; "artifact" is the protocol's term.
- Samples are the universe specs in `universe-samples/`.

## Writing rules

- Keep the owner-reviewed wording. Change format, links and components, not prose, unless asked.
- Headings in sentence case. Links to other pages are root-relative with no extension; links to repository files are full GitHub URLs.
- `knowledge-bus-directory.mdx` is also bundled into the agent skills as Markdown. Keep it free of components, and keep its links to anchors on the same page.

## Checks

Run `pnpm dlx mint validate` and `pnpm dlx mint broken-links` from this folder.
