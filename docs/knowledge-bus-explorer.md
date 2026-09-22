# Knowledge Bus Explorer

Knowledge Bus Explorer turns a universe into a map you can explore in a browser or embed as an image. It reads definitions that have passed the checker and shows the document types, the knowledge elements they contain, the frames that change what applies, and the relationships declared between them.

## Opening the Map

Every render produces a single HTML file. Open it directly: it needs no server and no network. The bundled product-development universe renders to `dist/explorer/product-development.html`.

Three views sit behind the tabs at the top:

- **Dimensions** — the frames the universe is indexed by, with the ordering frame and its values nested among them, the exceptions that mean no artifact is needed, and any declared factors.
- **Artifacts** — document types alone, arranged so connected ones sit near each other, with element-level relations rolled up onto them.
- **Artifacts & Elements** — both, with elements grouped by the ordering frame.

## Reading Connections

Each card shows a count of its connections by default. Switching Display to Lines draws the routes instead, labelled with the wording the universe authors declared. Composition can be shown uniformly or with required and situational membership distinguished, with a legend explaining the strokes.

Selecting a card, a connection, a count or a group heading opens its details and frames the selected set beside the panel. Details give the requirement, where the answer is kept, any conditions that apply, and related knowledge in the universe's own phrasing. Long lists start at three entries with the rest one click away.

Close the panel, press Escape, or press an empty part of the canvas to return to the overview.

## View Options

The menu on the right holds the choices that persist: theme, element grouping, frame and factor filters, connection family, emphasis for one or more relation types, display, and composition line style. Resetting view options keeps whatever is selected. The search button finds an artifact or element by name, alias or question, switching view if the match is not on the current map.

The bottom dock toggles the map overview, fits the map, and zooms. The overview can be dragged by its header and navigated by its plot.

## Exporting

The export button downloads the visible map as SVG. One file carries both light and dark palettes and follows the reader's system colour scheme, so a single image serves a README in either theme. Exports contain no scripts or external references, and they leave out menus, overlays and transient selection.

Installed users can first create a self-contained artifact through `kb-explore` or the bundled launcher:

```bash
python3 /absolute/runtime/kbp.py --explore --output .knowledge-bus/explorer/<universe-id> .knowledge-bus/
```

Open `index.html`, then use Export to download SVG. The Explorer works offline. Its SVG fits the browser window when opened and keeps its aspect ratio when embedded. Generation refuses an existing destination unless `--replace` is supplied.

## Rendering Your Own Universe

```bash
pnpm run build:explorer
node tools/explorer/render.mjs --input .knowledge-bus/universe.kbp.yaml --html map.html --svg map.svg
```

Contributor and release rendering validates the universe first and refuses non-conforming input. It requires Node, pnpm, uv, and Playwright Chromium. Generated files remain self-contained.

## What the Map Does Not Decide

The viewer shows declarations. It does not evaluate a context, so conditional composition and gated artifacts are described as depending on context rather than resolved. Relationship wording comes from the universe; when a relation kind declares no phrasing, the viewer says only what the universe says rather than inventing an inverse.

See [Knowledge Bus Explorer](../explorer/README.md) for the library, commands, checks and limits.
