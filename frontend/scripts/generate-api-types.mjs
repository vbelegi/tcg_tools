/**
 * Generates TypeScript types from FastAPI OpenAPI schema.
 * Run from frontend/: npm run generate:api
 */
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const backend = join(root, "backend");
const openapi = join(backend, "openapi.json");
const out = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "api", "openapi.d.ts");

const py = process.platform === "win32" ? "py -3.13" : "python3";
execSync(`${py} scripts/export_openapi.py`, { cwd: backend, stdio: "inherit" });

if (!existsSync(openapi)) {
  throw new Error(`OpenAPI schema not found: ${openapi}`);
}

execSync(`npx openapi-typescript "${openapi}" -o "${out}"`, {
  cwd: join(dirname(fileURLToPath(import.meta.url)), ".."),
  stdio: "inherit",
});

console.log(`Generated ${out}`);
