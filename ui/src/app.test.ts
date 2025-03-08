import { describe, expect, it } from "vitest";

import { addCursorShot, AppState, moveCursor, renderApp, scoreCursor } from "./app";
import { XgModel } from "./xg";

const model: XgModel = {
  weight: [-1.5, 0.5, 0, 0, 0, 0, 0],
  bias: 0.5,
  mean: [0, 0, 0, 0, 0, 0, 0],
  scale: [1, 1, 1, 1, 1, 1, 1],
};

function state(): AppState {
  return {
    model,
    trainMin: [0, 0, 0, 0, 0, 0, 0],
    trainMax: [40, 1.5, 1, 1, 1, 1, 1],
    shots: [],
    cursor: { x: 0.85, y: 0.5 },
    isGoal: false,
    coverage: [{ competition: "SAMPLE", season: "2023-2024", level: "events", matches: 90 }],
  };
}

describe("tactical app logic", () => {
  it("scores the cursor position", () => {
    const s = scoreCursor(state());
    expect(s.xg).toBeGreaterThan(0);
    expect(s.xg).toBeLessThan(1);
  });

  it("clamps cursor movement to the pitch", () => {
    const s = state();
    moveCursor(s, 1, 1); // large step beyond the edge
    expect(s.cursor.x).toBeLessThanOrEqual(1);
    expect(s.cursor.y).toBeLessThanOrEqual(1);
    moveCursor(s, -5, -5);
    expect(s.cursor.x).toBeGreaterThanOrEqual(0);
    expect(s.cursor.y).toBeGreaterThanOrEqual(0);
  });

  it("adds a shot and renders coverage and totals", () => {
    const s = state();
    addCursorShot(s);
    expect(s.shots.length).toBe(1);
    const html = renderApp(s);
    expect(html).toContain("SAMPLE 2023-2024");
    expect(html).toContain("shots 1");
  });
});
