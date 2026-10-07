# Explorer Contributions

The explorer draws a universe as an offline map: one HTML page and an SVG export. This path suits frontend developers and people who work on accessibility or design.

## When to Open an Issue First

For a bug, open a pull request with a screenshot; you don't need an issue. For a new view or a change to what the map shows, open an issue first.

## What You Can Change

You can change the viewer in `explorer/src/`, its tests in `explorer/test/`, its design tokens in `explorer/styles/visual-tokens.json`, and the scripts in `tools/explorer/`.

Every change must follow these rules:

- Write no comments in explorer source. `just explorer-check` fails on any comment.
- Take every colour and length from the design tokens. `just explorer-check` fails on literal values.
- Keep the page and SVG self-contained: no runtime dependency, framework, CDN, icon font, network request or path from your own machine.
- Label a relation only with the universe's own wording. If the universe gives none, leave it unlabelled.
- Draw only what the files declare. Leave it to the checker to decide which documents apply.

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

## Run It Locally

`just explorer-build`, then `just explorer-render`, writes the page to `dist/explorer/product-development.html`; open it in a browser. `just explorer-check` and `just explorer-test` run the checks.

## Proof to Bring

Fix one bug or add one view per pull request.

| Change | Add |
| --- | --- |
| Bug fix | A test that fails before the fix, in `explorer/test/unit/` for layout and logic or `explorer/test/browser/` for page behaviour |
| Anything visible | Before-and-after shots |
| Token change | The stylesheet regenerated with `just explorer-tokens` |
| An exception you add to `tools/explorer/component-advisories.json` or `tools/explorer/visual-geometry-exceptions.json` | A `note` or `reason` field that says why |

Take the shots, then paste the compare summary and the changed shots into the pull request:

```sh
# On main, before your change
just explorer-build
just explorer-render
node tools/explorer/shots.mjs --out dist/explorer-shots/before --tier step

# On your branch
just explorer-build
just explorer-render
just explorer-capture-step

# Compare
just explorer-compare dist/explorer-shots/before dist/explorer-shots/step
```

For every change:

- [ ] After editing `explorer/src/`: `just explorer-build`, then `just skills-build`, rebuilt files included.
- [ ] `just explorer-gallery` run, redrawn README map included.

## Handing Over

Commit with the `explorer` [scope](../../CONTRIBUTING.md#commits). Open the pull request from the template and bring what [every pull request](../../CONTRIBUTING.md#every-pull-request) needs.

---

Adapted from [Archify's CONTRIBUTING](https://github.com/tt-a1i/archify/blob/fae6186f20bf56106e68252a607aa8a9fb0e8f9e/CONTRIBUTING.md).
