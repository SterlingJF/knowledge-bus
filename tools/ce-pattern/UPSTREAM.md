# Upstream

Provenance for the vendored CE pattern tooling. Updates follow the kit's `references/update.md`
as a three-way merge; this directory is never replaced wholesale.

## Source

- Repository: SterlingJF/ce-pattern-kit
- Ref: 1585615483cb9ca68506aabc99987d24b603f310
- Commit: 1585615483cb9ca68506aabc99987d24b603f310
- Skill: install-ce-pattern

## Installed paths

- Tooling: `tools/ce-pattern/`
- Library: `explorer/` (`@knowledge-bus/explorer`, preset none)
- Consumer: none; the generated page is output, not a consuming application

## Deviations

- Framework-neutral `none` preset: native TypeScript, DOM, SVG, and Custom Elements; no React. The
  explicit preset permits native root component-elements with no component-layer import.
- No component registry and therefore no `component-core` directory. Core appears only if untouched
  vendor components are introduced later.
- The package keeps buildable source under `explorer/src`; the token authority and stylesheet live under
  `explorer/styles`, outside the component layers, and are checked by `tools/explorer/check-tokens.mjs`.
- `tools/explorer/check-layers.ts` wraps the stock checker: refusals fail, advisories must carry a written
  review in `tools/explorer/component-advisories.json`, and `lib` is refused DOM work or component imports.

## Verification

```bash
pnpm run check:component-layers
```
