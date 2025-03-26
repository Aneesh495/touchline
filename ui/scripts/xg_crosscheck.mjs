// Cross-language differential: score a set of shot locations with the TS xG and
// compare against the Python values in _crosscheck_input.json (produced by the
// Python side). Exits non-zero if any pair disagrees beyond tolerance.
import { build } from "esbuild";
import { readFileSync } from "fs";

const result = await build({
  entryPoints: ["src/xg.ts", "src/pitch.ts"],
  bundle: true,
  format: "esm",
  write: false,
  platform: "node",
  outdir: "out",
});
// Load the bundled xg module from memory.
const xgCode = result.outputFiles.find((f) => f.path.endsWith("xg.js")).text;
const mod = await import("data:text/javascript;base64," + Buffer.from(xgCode).toString("base64"));

const input = JSON.parse(readFileSync("scripts/_crosscheck_input.json", "utf8"));
const model = input.model;
let maxDiff = 0;
for (const row of input.cases) {
  const ctx = {
    location: { x: row.x, y: row.y },
    isHeader: false,
    isPenalty: false,
    isFreeKick: false,
    isCorner: false,
    isCounter: false,
  };
  const ts = mod.predictXg(model, ctx);
  maxDiff = Math.max(maxDiff, Math.abs(ts - row.python_xg));
}
console.log("max |ts - python| =", maxDiff);
process.exit(maxDiff < 1e-9 ? 0 : 1);
