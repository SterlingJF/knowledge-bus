import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, dirname, join, relative, resolve, sep } from "node:path";

import { parseSync } from "oxc-parser";

export type Layer = "core" | "elements" | "patterns";
export type Kind = "types" | "values";
export type KindCount = Record<Kind, number>;

export interface FileReport {
  path: string;
  layer: Layer;
  sources: string[];
  imported: KindCount;
  exported: KindCount;
  refusals: string[];
  advisories: string[];
}

export interface PackageReport {
  root: string;
  alias: string;
  base: string;
  files: FileReport[];
  advisories: string[];
}

export interface LayersReport {
  packages: PackageReport[];
  refusals: number;
  advisories: number;
}

export interface LayersOptions {
  roots: string[];
  allowSourcelessElements?: string[];
}

export const layerDirectories: Record<Layer, string> = {
  core: "component-core",
  elements: "component-elements",
  patterns: "component-patterns",
};

const layers: Layer[] = ["core", "elements", "patterns"];
const kinds: Kind[] = ["types", "values"];
const layerOfDirectory = new Map(
  layers.map((layer) => [layerDirectories[layer], layer] as const),
);
const permittedImports: Record<Layer, ReadonlySet<Layer>> = {
  core: new Set(["core"]),
  elements: new Set(["core", "elements"]),
  patterns: new Set(["core", "elements", "patterns"]),
};
const moduleFile = /\.[cm]?[jt]sx?$/;
const supportFile =
  /\.(stories|story|test|spec|fixture|fixtures|d)\.[cm]?[jt]sx?$/;
const supportDirectories = new Set([
  "fixtures",
  "__fixtures__",
  "stories",
  "__tests__",
  "__mocks__",
]);
const resolutions = [
  "",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  "/index.ts",
  "/index.tsx",
];
const barrelFiles = ["index.ts", "index.tsx"];

interface Package {
  root: string;
  alias: string;
  base: string;
  elements: boolean;
  allowSourcelessElements: boolean;
}

interface ImportEntry {
  name: string | null;
  kind: string;
  isType: boolean;
}

interface ImportRecord {
  specifier: string;
  entries: ImportEntry[];
}

interface ExportEntry {
  kind: Kind;
  request: string | null;
  importName: string | null;
}

interface ParsedModule {
  exports: Map<string, ExportEntry>;
  stars: string[];
  imports: ImportRecord[];
}

interface Located {
  pkg: Package;
  file: string;
  layer: Layer | null;
}

interface Traced extends Located {
  layer: Layer;
  name: string;
}

type Resolution = Located | "missing" | null;

interface Context {
  packages: Package[];
  parsed: (file: string) => ParsedModule;
}

const posix = (path: string): string => path.split(sep).join("/");

function readAlias(root: string): string {
  const manifest = join(root, "package.json");
  if (!existsSync(manifest)) return "";
  const name: unknown = JSON.parse(readFileSync(manifest, "utf8")).name;
  return typeof name === "string" ? name : "";
}

function hasLayers(directory: string): boolean {
  return layers.some((layer) =>
    existsSync(join(directory, layerDirectories[layer])),
  );
}

function describePackage(
  root: string,
  allowSourcelessElements: ReadonlySet<string>,
): Package {
  if (!existsSync(root) || !statSync(root).isDirectory()) {
    throw new Error(`${root} is not a directory`);
  }
  const source = join(root, "src");
  const base = hasLayers(root) ? root : hasLayers(source) ? source : root;
  const elementsDir = join(base, layerDirectories.elements);
  const elements =
    existsSync(elementsDir) && listModules(elementsDir).length > 0;
  return {
    root,
    alias: readAlias(root),
    base,
    elements,
    allowSourcelessElements: allowSourcelessElements.has(root),
  };
}

function packageOf(path: string, packages: Package[]): Package | null {
  let match: Package | null = null;
  for (const pkg of packages) {
    const inside = relative(pkg.root, path);
    if (inside.startsWith("..") || inside === "") continue;
    if (!match || pkg.root.length > match.root.length) match = pkg;
  }
  return match;
}

function layerOf(pkg: Package, path: string): Layer | null {
  const inside = relative(pkg.base, path);
  if (inside.startsWith("..")) return null;
  return layerOfDirectory.get(inside.split(sep)[0]) ?? null;
}

function findFile(base: string): string | null {
  for (const suffix of resolutions) {
    const candidate = `${base}${suffix}`;
    if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  }
  return null;
}

function listModules(directory: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(directory, { withFileTypes: true }).sort(
    (a, b) => a.name.localeCompare(b.name),
  )) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      if (!supportDirectories.has(entry.name)) files.push(...listModules(path));
    } else if (moduleFile.test(entry.name) && !supportFile.test(entry.name)) {
      files.push(path);
    }
  }
  return files;
}

function countFiles(directory: string): number {
  let count = 0;
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory()) count += countFiles(join(directory, entry.name));
    else if (entry.isFile()) count += 1;
  }
  return count;
}

function parseModule(file: string): ParsedModule {
  const parsed = parseSync(file, readFileSync(file, "utf8"));
  if (parsed.errors.length > 0) {
    throw new Error(`${file}: ${parsed.errors[0].message}`);
  }
  const typeDeclarations = new Set<string>();
  for (const node of parsed.program.body) {
    const declaration =
      node.type === "ExportNamedDeclaration" ? node.declaration : node;
    if (
      declaration &&
      (declaration.type === "TSInterfaceDeclaration" ||
        declaration.type === "TSTypeAliasDeclaration")
    ) {
      typeDeclarations.add(declaration.id.name);
    }
  }
  const exports = new Map<string, ExportEntry>();
  const stars: string[] = [];
  const imports: ImportRecord[] = parsed.module.staticImports.map((record) => ({
    specifier: record.moduleRequest.value,
    entries: record.entries.map((entry) => ({
      name: entry.importName.name,
      kind: entry.importName.kind,
      isType: entry.isType,
    })),
  }));
  for (const record of parsed.module.staticExports) {
    const reexports = new Map<string, ImportEntry[]>();
    for (const entry of record.entries) {
      const request = entry.moduleRequest?.value ?? null;
      if (request !== null && !reexports.has(request))
        reexports.set(request, []);
      if (entry.exportName.kind === "None") {
        if (request !== null) stars.push(request);
        continue;
      }
      const name =
        entry.exportName.kind === "Default" ? "default" : entry.exportName.name;
      if (name === null) continue;
      const local = entry.localName.name ?? name;
      const isType =
        entry.isType || (request === null && typeDeclarations.has(local));
      const importName =
        entry.importName.kind === "Name" ? entry.importName.name : null;
      exports.set(name, {
        kind: isType ? "types" : "values",
        request,
        importName,
      });
      if (request !== null) {
        reexports.get(request)?.push({
          name: importName,
          kind: entry.importName.kind === "Name" ? "Name" : "NamespaceObject",
          isType: entry.isType,
        });
      }
    }
    for (const [specifier, entries] of reexports)
      imports.push({ specifier, entries });
  }
  return { exports, stars, imports };
}

function resolveModule(
  specifier: string,
  from: string,
  context: Context,
): Resolution {
  let pkg: Package | null = null;
  let base: string | null = null;
  if (specifier.startsWith("./") || specifier.startsWith("../")) {
    base = resolve(dirname(from), specifier);
    pkg = packageOf(base, context.packages);
  } else {
    for (const candidate of context.packages) {
      if (!candidate.alias) continue;
      if (specifier === candidate.alias) {
        pkg = candidate;
        for (const directory of [candidate.root, candidate.base]) {
          for (const barrel of barrelFiles) {
            const file = join(directory, barrel);
            if (existsSync(file)) return { pkg, file, layer: null };
          }
        }
        return null;
      }
      if (specifier.startsWith(`${candidate.alias}/`)) {
        pkg = candidate;
        base = resolve(
          candidate.base,
          specifier.slice(candidate.alias.length + 1),
        );
        break;
      }
    }
  }
  if (!pkg || base === null) return null;
  const layer = layerOf(pkg, base);
  const file = findFile(base);
  if (file === null) return layer === null ? null : "missing";
  return { pkg, file, layer };
}

function exportsName(
  file: string,
  name: string,
  context: Context,
  seen: Set<string>,
): boolean {
  if (seen.has(file)) return false;
  seen.add(file);
  const module = context.parsed(file);
  if (module.exports.has(name)) return true;
  for (const request of module.stars) {
    const target = resolveModule(request, file, context);
    if (target === null || target === "missing") continue;
    if (exportsName(target.file, name, context, seen)) return true;
  }
  return false;
}

function traceExport(
  file: string,
  name: string,
  context: Context,
  seen: Set<string>,
): Traced | null {
  if (seen.has(file)) return null;
  seen.add(file);
  const pkg = packageOf(file, context.packages);
  if (!pkg) return null;
  const layer = layerOf(pkg, file);
  if (layer !== null) return { pkg, file, layer, name };
  const module = context.parsed(file);
  const entry = module.exports.get(name);
  if (entry) {
    if (entry.request === null || entry.importName === null) return null;
    const target = resolveModule(entry.request, file, context);
    if (target === null || target === "missing") return null;
    if (target.layer !== null) {
      return { ...target, layer: target.layer, name: entry.importName };
    }
    return traceExport(target.file, entry.importName, context, seen);
  }
  for (const request of module.stars) {
    const target = resolveModule(request, file, context);
    if (target === null || target === "missing") continue;
    if (target.layer !== null) {
      if (exportsName(target.file, name, context, new Set())) {
        return { ...target, layer: target.layer, name };
      }
      continue;
    }
    const traced = traceExport(target.file, name, context, seen);
    if (traced) return traced;
  }
  return null;
}

function describeSource(source: Located, from: Package): string {
  if (source.pkg === from) return posix(relative(from.root, source.file));
  const label = source.pkg.alias || basename(source.pkg.root);
  return `${label}/${posix(relative(source.pkg.base, source.file))}`;
}

function classifyFile(
  file: string,
  layer: Layer,
  pkg: Package,
  context: Context,
): FileReport {
  const module = context.parsed(file);
  const sources = new Map<string, Located>();
  const imported: KindCount = { types: 0, values: 0 };
  const refusals: string[] = [];
  const advisories: string[] = [];
  let hasMissingLayerSource = false;
  const addSource = (source: Located & { layer: Layer }): void => {
    if (sources.has(source.file)) return;
    sources.set(source.file, source);
    if (!permittedImports[layer].has(source.layer)) {
      refusals.push(
        `Rule 5: ${layer} imports ${source.layer} (${describeSource(source, pkg)})`,
      );
    }
  };
  const kindOf = (entry: ImportEntry, target: string, name: string): Kind =>
    entry.isType
      ? "types"
      : (context.parsed(target).exports.get(name)?.kind ?? "values");
  for (const record of module.imports) {
    const target = resolveModule(record.specifier, file, context);
    if (target === null) continue;
    if (target === "missing") {
      hasMissingLayerSource = true;
      refusals.push(`import "${record.specifier}" resolves to no file`);
      continue;
    }
    if (target.layer !== null) {
      addSource({ ...target, layer: target.layer });
      for (const entry of record.entries) {
        const kind =
          entry.kind === "Name" && entry.name !== null
            ? kindOf(entry, target.file, entry.name)
            : entry.isType
              ? "types"
              : "values";
        imported[kind] += 1;
      }
      continue;
    }
    for (const entry of record.entries) {
      if (entry.kind !== "Name" || entry.name === null) continue;
      const traced = traceExport(target.file, entry.name, context, new Set());
      if (!traced) continue;
      addSource(traced);
      imported[kindOf(entry, traced.file, traced.name)] += 1;
    }
  }
  const exported: KindCount = { types: 0, values: 0 };
  for (const entry of module.exports.values()) exported[entry.kind] += 1;
  const star = module.stars.length > 0;
  if (layer === "elements") {
    if (
      sources.size === 0 &&
      !hasMissingLayerSource &&
      !pkg.allowSourcelessElements
    ) {
      refusals.push(
        "Rule 2: 0 sources; elements import from exactly one unless the framework-neutral preset explicitly permits native root elements",
      );
    }
    if (sources.size > 1) {
      refusals.push(
        `Rule 2: ${sources.size} sources; elements import from exactly one`,
      );
    }
    if (star) refusals.push("Rule 2: star export cannot be counted");
    for (const kind of kinds) {
      if (exported[kind] < imported[kind]) {
        refusals.push(
          `Rule 2: exports ${exported[kind]} ${kind}, imports ${imported[kind]}`,
        );
      }
    }
  }
  if (layer === "patterns" && pkg.elements && sources.size <= 1 && !star) {
    const [source] = sources.values();
    if (
      (source === undefined || source.layer !== "patterns") &&
      kinds.every((kind) => exported[kind] >= imported[kind])
    ) {
      advisories.push(
        source === undefined
          ? "Rule 6: no layer source; a prototype candidate, or an element if settled"
          : "Rule 6 path 4: single-source enrichment; move to elements once settled",
      );
    }
  }
  return {
    path: posix(relative(pkg.root, file)),
    layer,
    sources: [...sources.values()]
      .map((source) => describeSource(source, pkg))
      .sort(),
    imported,
    exported,
    refusals,
    advisories,
  };
}

function packageAdvisories(pkg: Package): string[] {
  const advisories: string[] = [];
  const candidates = new Set([
    join(pkg.root, "components"),
    join(pkg.root, "src", "components"),
    join(pkg.base, "components"),
  ]);
  for (const directory of candidates) {
    if (!existsSync(directory) || !statSync(directory).isDirectory()) continue;
    advisories.push(
      `${posix(relative(pkg.root, directory))}/ holds ${countFiles(directory)} files outside the layers`,
    );
  }
  return advisories;
}

export function classifyLayers(options: LayersOptions): LayersReport {
  const roots = [...new Set(options.roots.map((root) => resolve(root)))];
  const allowSourcelessElements = new Set(
    (options.allowSourcelessElements ?? []).map((root) => resolve(root)),
  );
  const packages = roots.map((root) =>
    describePackage(root, allowSourcelessElements),
  );
  const cache = new Map<string, ParsedModule>();
  const context: Context = {
    packages,
    parsed: (file) => {
      let module = cache.get(file);
      if (!module) {
        module = parseModule(file);
        cache.set(file, module);
      }
      return module;
    },
  };
  const reports: PackageReport[] = packages.map((pkg) => {
    const files: FileReport[] = [];
    for (const layer of layers) {
      const directory = join(pkg.base, layerDirectories[layer]);
      if (!existsSync(directory)) continue;
      for (const file of listModules(directory)) {
        files.push(classifyFile(file, layer, pkg, context));
      }
    }
    return {
      root: pkg.root,
      alias: pkg.alias,
      base: pkg.base,
      files,
      advisories: packageAdvisories(pkg),
    };
  });
  const files = reports.flatMap((report) => report.files);
  return {
    packages: reports,
    refusals: files.reduce((sum, file) => sum + file.refusals.length, 0),
    advisories:
      files.reduce((sum, file) => sum + file.advisories.length, 0) +
      reports.reduce((sum, report) => sum + report.advisories.length, 0),
  };
}
