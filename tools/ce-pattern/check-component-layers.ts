import { readFileSync } from "node:fs";
import { basename, resolve } from "node:path";

import { classifyLayers, type FileReport } from "./component-layers";

type CePatternConfig = {
  library: { dir: string; preset: string };
  consumers?: Array<{ dir: string }>;
};

const args = process.argv.slice(2);
const configIndex = args.indexOf("--config");
let roots: string[];
let allowSourcelessElements: string[] = [];
if (configIndex >= 0) {
  const configArgument = args[configIndex + 1];
  if (!configArgument) throw new Error("--config requires a path");
  const configPath = resolve(configArgument);
  const config = JSON.parse(
    readFileSync(configPath, "utf8"),
  ) as CePatternConfig;
  if (!config.library?.dir)
    throw new Error(`${configPath}: library.dir is required`);
  roots = [
    config.library.dir,
    ...(config.consumers ?? []).map(({ dir }) => dir),
  ];
  if (config.library.preset === "none")
    allowSourcelessElements = [config.library.dir];
} else {
  roots = args.length > 0 ? args : ["components"];
}
const report = classifyLayers({ roots, allowSourcelessElements });
const multi = report.packages.length > 1;

const verdict = (file: FileReport): string =>
  file.refusals.length > 0
    ? "refused"
    : file.advisories.length > 0
      ? "advisory"
      : "ok";

const header = ["file", "layer", "sources", "in t/v", "out t/v", "verdict"];
const rows = [
  multi ? ["package", ...header] : header,
  ...report.packages.flatMap((pkg) =>
    pkg.files.map((file) => {
      const cells = [
        file.path,
        file.layer,
        String(file.sources.length),
        `${file.imported.types}/${file.imported.values}`,
        `${file.exported.types}/${file.exported.values}`,
        verdict(file),
      ];
      return multi ? [basename(pkg.root), ...cells] : cells;
    }),
  ),
];
const widths = rows[0].map((_, column) =>
  Math.max(...rows.map((row) => row[column].length)),
);
for (const row of rows) {
  console.log(
    row.map((cell, column) => cell.padEnd(widths[column])).join("  "),
  );
}

let count = 0;
for (const pkg of report.packages) {
  const label = (path: string): string =>
    multi ? `${basename(pkg.root)}/${path}` : path;
  for (const file of pkg.files) {
    count += 1;
    for (const message of file.refusals)
      console.log(`refused   ${label(file.path)}: ${message}`);
    for (const message of file.advisories)
      console.log(`advisory  ${label(file.path)}: ${message}`);
  }
  for (const message of pkg.advisories) {
    console.log(`advisory  ${basename(pkg.root)}: ${message}`);
  }
}
console.log(
  `${count} files, ${report.refusals} refusals, ${report.advisories} advisories`,
);
process.exit(report.refusals > 0 ? 1 : 0);
