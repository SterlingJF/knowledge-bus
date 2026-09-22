# Knowledge Bus Explorer

> Also: [docs: Knowledge Bus Explorer](../docs/knowledge-bus-explorer.md)

`@knowledge-bus/explorer` is a read-only viewer for a single Knowledge Bus universe: its artifacts, knowledge elements, frames and factors, and the connections declared between them.

## Where Explorer sits within Knowledge Bus

> Explorer projects what a universe declares.

The Explorer serves as the human-friendly visual aid to Knowledge Bus' agent-first authoring process. It does not author definitions, evaluate context, or replace the checker. Everything it renders comes from a universe that has already passed conformance.

## Outputs

| Output | Contents | Use |
| --- | --- | --- |
| `dist/explorer/<name>.html` | One file with the validated model, styles, icons and viewer inline | Open from `file://`; works offline; fully interactive |
| `dist/explorer/<name>.svg` | Script-free SVG carrying both themes and a `prefers-color-scheme` rule | Embed in a README or a document; follows the reader's colour scheme |
| `dist/explorer/<name>.model.json` | Deterministic portable model (`knowledge-bus/explorer-model/1`) | Input for the library or other tools |
| `explorer/dist/index.js` | ESM library with declarations | Mount the viewer in your own page |

The HTML and SVG have no runtime dependencies: no framework, CDN, icon font, network request, or absolute machine path. A check refuses any artifact that acquires one.

## Commands

Run from the repository root.

```bash
pnpm run build:explorer
pnpm run render:explorer
pnpm run check:explorer
pnpm run test:explorer
```

`render:explorer` renders the bundled product-development universe. For another universe:

```bash
node tools/explorer/render.mjs --input path/to/universe.kbp.yaml --html out/map.html --svg out/map.svg
```

Rendering validates the universe through the existing checker first; a non-conforming universe stops the run with diagnostics rather than producing a partial map. The SVG is measured in a headless browser so its text wraps exactly as it does on screen. Building needs Node, pnpm, uv and a Playwright Chromium (`pnpm exec playwright install chromium`); viewing needs none of them.

## The Visual Map

Three views share one world:

- **Dimensions** shows the frames the universe is indexed by, the ordering frame and its values nested among them, the exceptions that mean no artifact is needed, and any declared factors.
- **Artifacts** places document types by how they connect, rolling element-level relations up onto the artifacts that contain them.
- **Artifacts & Elements** shows both, with elements grouped by the ordering frame.

Connections show as counts on each card by default, or as routed lines with authored phrasing. Routes are orthogonal, avoid crossing cards, and are deterministic for a given board. Composition lines can distinguish required from situational membership.

Selecting a card, a connection, a count or a boundary opens details beside it and frames the selected set in the space the overlay leaves. Details use the universe's own wording: a relation with no authored phrasing is never given an invented one.

## Library

```ts
import { mountUniverseViewer } from '@knowledge-bus/explorer';

const handle = mountUniverseViewer(host, model, { initial: { view: 'artifacts' } });
handle.select('artifact:decision-record');
const svg = await handle.exportSvg({ theme: 'auto' });
handle.destroy();
```

- `host` needs a size. The viewer renders into its own shadow root and installs its own styles.
- `model` is the JSON written by `tools/explorer/prepare_model.py`. Unsupported or malformed shapes throw before anything mounts.
- Importing the package does no DOM work. Several viewers coexist; `destroy()` removes listeners, observers and pending frames.
- `getState()` returns persistent view options, the transient selection and the camera. Changing view options never clears the selection; closing details never resets view options.

## Source Layout

The package follows the CE Pattern with the framework-neutral `none` preset (`tools/ce-pattern/README_COMPONENT_SYSTEM.md`).

```text
explorer/
├── src/
│   ├── index.ts               browser-safe public API
│   ├── standalone.ts          mounts the inline model in the generated HTML
│   ├── component-elements/    native roots: icon, buttons, segmented control, chip, disclosure, card surface, panel, field
│   ├── component-patterns/    compositions: cards, map, overlays, detail copy, options menu, search, minimap, chrome, viewer
│   └── lib/                   no DOM: model guards, layout, routing, rollup, bundles, labels, nubs, camera, phrasing, tokens, icons, scene, export
├── styles/
│   ├── visual-tokens.json     the visual authority
│   ├── tokens.css             generated from it
│   └── patterns.css           consumes tokens only
└── test/
    ├── unit/                  node:test over lib
    ├── adapter/               unittest over the Python model adapter
    ├── fixtures/              the real universe, as a model
    └── browser/               Playwright over the generated artifact and the library
```

## Visual Tokens and Source Rules

`styles/visual-tokens.json` holds every colour, type step, spacing value, control size and interaction state. The viewer stylesheet and the exported SVG palette both derive from it. World coordinates are not theme values: they live as named constants in `src/lib/layout.ts`, where the layout that uses them can be read in one place.

It has two tiers. `roles` are the values parts share — the palette, the type roles, the ladders, and any dimension more than one part draws — and `parts` are one part's own dimensions. A name follows from where the value sits: a `roles.color` entry is bare (`--kb-canvas`), every other role carries its group (`--kb-space-2`), and a part carries its own name (`--kb-count-radius`). A group keeps its name across the move, so a value that turns out to be shared changes tier without renaming its token. `styles/tokens.css` is that flattening, generated.

A role group that is a ladder may declare `base`, the unit its steps are multiples of, and `fineWork`, the finer values the ladder admits by name. `space` declares a base of 4 with 1, 2, 3, 6 and 10 as fine work, so a captured measurement such as 11px cannot land on the ladder unchallenged.

Every part declares `selectors`, the rules it draws, and that declaration is what holds the part's tokens to those rules. A part may also declare `closed`, the separate and stronger claim that its rules read nothing but its own tokens; `label` and `count` are closed, while `card` legitimately reads `--kb-border` and stays open.

Three checks keep that honest:

- `check:explorer:tokens` refuses literal colours and lengths in CSS or TypeScript, unknown or unused tokens, stale generated CSS, any numeric literal that is not a named constant, a part that declares no selectors, a part's token reached from a selector that part does not declare, a foreign token inside a closed part's rules, and a ladder step that is neither a multiple of its declared base nor listed as fine work. Its eight structural exceptions each name an exact expression and why it is structural.
- `check:explorer:source` refuses comments. A claim that matters belongs in a name, a type or a test, where it can fail.
- `check:component-layers` runs the CE checker and refuses unreviewed advisories, DOM work inside `lib`, and imports that cross a layer the wrong way.

The browser suite mutates tokens at runtime and asserts the change reaches controls, cards, icons and an open overlay.

## Limits

- Context evaluation stays in the checker. Frames, gates and conditions are shown as declared; the viewer never decides whether an artifact applies.
- Text measurement uses the local system font stack, so two machines with different fonts may wrap labels differently in the SVG.
- Raster export, clipboard copy and route playback are out of scope; the export menu shows them disabled, as the prototype did.
