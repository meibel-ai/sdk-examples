/**
 * Patches the meibel SDK after install from GitHub.
 *
 * The GitHub-published source is missing:
 *   1. tsconfig.json (needed to build dist/)
 *   2. The artifactSchemaFromZod re-export from the package index
 *
 * This script adds both so that `tsc --noCheck` can produce working
 * declaration files and JS output.
 */
import { writeFileSync, readFileSync } from "node:fs";

const root = "node_modules/meibel";

// 1. Write a tsconfig.json for the SDK build
writeFileSync(
  `${root}/tsconfig.json`,
  JSON.stringify(
    {
      compilerOptions: {
        target: "ES2022",
        module: "Node16",
        moduleResolution: "Node16",
        outDir: "./dist",
        rootDir: "./src",
        declaration: true,
        strict: true,
        skipLibCheck: true,
        esModuleInterop: true,
      },
      include: ["src"],
    },
    null,
    2
  ) + "\n"
);

// 2. Append the missing artifactSchemaFromZod export to src/index.ts
const indexPath = `${root}/src/index.ts`;
const index = readFileSync(indexPath, "utf8");
const exportLine = "export { artifactSchemaFromZod } from './artifacts.js';";
if (!index.includes("artifactSchemaFromZod")) {
  writeFileSync(indexPath, index.trimEnd() + "\n" + exportLine + "\n");
}
