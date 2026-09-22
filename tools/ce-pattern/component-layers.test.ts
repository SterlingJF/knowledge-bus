import assert from "node:assert/strict";
import { basename, relative, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  classifyLayers,
  type FileReport,
  type LayersReport,
} from "./component-layers";

const fixtures = fileURLToPath(
  new URL("./test-fixtures/component-layers/", import.meta.url),
);

const scenario = (name: string, ...roots: string[]): LayersReport =>
  classifyLayers({
    roots: (roots.length > 0 ? roots : [""]).map((root) =>
      resolve(fixtures, name, root),
    ),
  });

const scenarioAllowingNativeRootElements = (name: string): LayersReport => {
  const root = resolve(fixtures, name);
  return classifyLayers({
    roots: [root],
    allowSourcelessElements: [root],
  });
};

const files = (report: LayersReport): FileReport[] =>
  report.packages.flatMap((pkg) => pkg.files);

const file = (report: LayersReport, path: string): FileReport | undefined =>
  files(report).find((candidate) => candidate.path === path);

const refusals = (report: LayersReport): string[] =>
  files(report).flatMap((entry) =>
    entry.refusals.map((message) => `${entry.path}: ${message}`),
  );

const advisories = (report: LayersReport): string[] =>
  files(report).flatMap((entry) =>
    entry.advisories.map((message) => `${entry.path}: ${message}`),
  );

const packageAdvisories = (report: LayersReport): string[] =>
  report.packages.flatMap((pkg) =>
    pkg.advisories.map((message) => `${basename(pkg.root)}: ${message}`),
  );

test("a valid tree classifies clean", () => {
  const report = scenario("valid");
  assert.equal(report.packages[0].alias, "@fixture/components");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), []);
  assert.deepEqual(
    files(report).map((entry) => entry.path),
    [
      "component-core/button.tsx",
      "component-core/separator.tsx",
      "component-elements/nav-link.tsx",
      "component-elements/prose.tsx",
      "component-patterns/search-bar.tsx",
      "component-patterns/toc.tsx",
      "component-patterns/toolbar.tsx",
    ],
  );
  const navLink = file(report, "component-elements/nav-link.tsx");
  assert.deepEqual(navLink?.sources, ["component-core/button.tsx"]);
  assert.deepEqual(navLink?.imported, { types: 1, values: 2 });
  assert.deepEqual(navLink?.exported, { types: 1, values: 2 });
  const searchBar = file(report, "component-patterns/search-bar.tsx");
  assert.deepEqual(searchBar?.sources, [
    "component-core/button.tsx",
    "component-core/separator.tsx",
    "component-elements/nav-link.tsx",
  ]);
});

test("an element with two sources is refused", () => {
  assert.deepEqual(refusals(scenario("elements-two-sources")), [
    "component-elements/split.tsx: Rule 2: 2 sources; elements import from exactly one",
  ]);
});

test("a zero-source element requires an explicit native-root exception", () => {
  assert.deepEqual(refusals(scenario("elements-zero-source")), [
    "component-elements/plain.tsx: Rule 2: 0 sources; elements import from exactly one unless the framework-neutral preset explicitly permits native root elements",
  ]);
  assert.deepEqual(
    refusals(scenarioAllowingNativeRootElements("elements-zero-source")),
    [],
  );
});

test("an element exporting fewer values than it imports is refused", () => {
  assert.deepEqual(refusals(scenario("elements-fewer-exports")), [
    "component-elements/primary.tsx: Rule 2: exports 1 values, imports 2",
  ]);
});

test("an element exporting fewer types than it imports is refused", () => {
  assert.deepEqual(refusals(scenario("elements-kind-mismatch")), [
    "component-elements/typed.tsx: Rule 2: exports 0 types, imports 1",
  ]);
});

test("an element importing a pattern is refused", () => {
  assert.deepEqual(refusals(scenario("elements-imports-pattern")), [
    "component-elements/wrapped.tsx: Rule 5: elements imports patterns (component-patterns/card.tsx)",
  ]);
});

test("a core file importing an element is refused", () => {
  assert.deepEqual(refusals(scenario("core-imports-element")), [
    "component-core/bad.tsx: Rule 5: core imports elements (component-elements/thing.tsx)",
  ]);
});

test("a pattern that meets the element criteria is advised, not refused", () => {
  const report = scenario("pattern-reclassifiable");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), [
    "component-patterns/fancy-button.tsx: Rule 6 path 4: single-source enrichment; move to elements once settled",
  ]);
});

test("a pattern with no layer source is advised as a prototype candidate", () => {
  const report = scenario("pattern-prototype");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), [
    "component-patterns/toc.tsx: Rule 6: no layer source; a prototype candidate, or an element if settled",
  ]);
});

test("patterns are not advised where the package has no elements layer", () => {
  const report = scenario("pattern-no-elements-layer");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), []);
});

test("a layer import that resolves to no file is refused", () => {
  assert.deepEqual(refusals(scenario("missing-import")), [
    'component-elements/ghost.tsx: import "../component-core/missing" resolves to no file',
  ]);
});

test("a consumer's layers are checked beside the shared package", () => {
  const report = scenario("consumer-valid", "components", "app");
  assert.deepEqual(
    report.packages.map((pkg) => [
      basename(pkg.root),
      relative(pkg.root, pkg.base),
    ]),
    [
      ["components", ""],
      ["app", "src"],
    ],
  );
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), []);
  assert.deepEqual(packageAdvisories(report), []);
  assert.deepEqual(
    report.packages[1].files.map((entry) => entry.path),
    [
      "src/component-core/index.ts",
      "src/component-elements/link-button.tsx",
      "src/component-patterns/hero.tsx",
    ],
  );
  const core = file(report, "src/component-core/index.ts");
  assert.deepEqual(core?.sources, [
    "@fixture/components/component-core/button.tsx",
    "@fixture/components/component-core/separator.tsx",
  ]);
  assert.deepEqual(core?.imported, { types: 1, values: 2 });
  assert.deepEqual(core?.exported, { types: 1, values: 2 });
  const linkButton = file(report, "src/component-elements/link-button.tsx");
  assert.deepEqual(linkButton?.sources, [
    "@fixture/components/component-core/button.tsx",
  ]);
  assert.deepEqual(linkButton?.imported, { types: 1, values: 1 });
  assert.deepEqual(linkButton?.exported, { types: 1, values: 1 });
  const hero = file(report, "src/component-patterns/hero.tsx");
  assert.deepEqual(hero?.sources, [
    "@fixture/components/component-core/separator.tsx",
    "@fixture/components/component-elements/nav-link.tsx",
    "@fixture/components/component-patterns/card.tsx",
    "src/component-core/index.ts",
  ]);
});

test("a consumer components directory is advised, never refused", () => {
  const report = scenario("consumer-stray-components", "components", "app");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(packageAdvisories(report), [
    "app: src/components/ holds 2 files outside the layers",
  ]);
  assert.equal(report.advisories, 1);
});

test("a consumer element importing a shared pattern through the barrel is refused", () => {
  assert.deepEqual(
    refusals(
      scenario("consumer-elements-imports-shared-pattern", "components", "app"),
    ),
    [
      "src/component-elements/wrapped.tsx: Rule 5: elements imports patterns (@fixture/components/component-patterns/card.tsx)",
    ],
  );
});

test("a barrel of star exports is traced to its layer files", () => {
  const report = scenario("consumer-barrel-star", "components", "app");
  assert.deepEqual(refusals(report), []);
  assert.deepEqual(advisories(report), []);
  const fancyLink = file(report, "src/component-elements/fancy-link.tsx");
  assert.deepEqual(fancyLink?.sources, [
    "@fixture/components/component-elements/nav-link.tsx",
  ]);
  assert.deepEqual(fancyLink?.imported, { types: 1, values: 1 });
  const toolbar = file(report, "src/component-patterns/toolbar.tsx");
  assert.deepEqual(toolbar?.sources, [
    "@fixture/components/component-core/button.tsx",
    "@fixture/components/component-core/separator.tsx",
  ]);
  assert.deepEqual(toolbar?.imported, { types: 0, values: 2 });
});

test("a root that is not a directory throws", () => {
  assert.throws(() => scenario("no-such-scenario"), /is not a directory/);
});
