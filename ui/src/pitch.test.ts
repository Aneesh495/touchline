import { describe, expect, it } from "vitest";

import { distanceToGoalM, PITCH_LENGTH_M, shotAngleRad, toSvg } from "./pitch";

describe("pitch geometry", () => {
  it("penalty spot is 11 m from goal", () => {
    const x = 1.0 - 11.0 / PITCH_LENGTH_M;
    expect(distanceToGoalM({ x, y: 0.5 })).toBeCloseTo(11.0, 5);
  });

  it("angle is larger closer and more central", () => {
    const close = shotAngleRad({ x: 1 - 6 / PITCH_LENGTH_M, y: 0.5 });
    const far = shotAngleRad({ x: 1 - 30 / PITCH_LENGTH_M, y: 0.5 });
    expect(close).toBeGreaterThan(far);
    const central = shotAngleRad({ x: 1 - 18 / PITCH_LENGTH_M, y: 0.5 });
    const wide = shotAngleRad({ x: 1 - 18 / PITCH_LENGTH_M, y: 0.9 });
    expect(central).toBeGreaterThan(wide);
  });

  it("maps canonical goal mouth to the right edge, centre height", () => {
    const p = toSvg({ x: 1, y: 0.5 }, 100, 50);
    expect(p.x).toBeCloseTo(100, 5);
    expect(p.y).toBeCloseTo(25, 5);
  });
});
