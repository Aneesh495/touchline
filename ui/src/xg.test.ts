import { describe, expect, it } from "vitest";

import { predictXg, ShotContext, withinSupport, XgModel } from "./xg";

// A small hand-built model: strong negative distance weight, positive angle weight,
// zero elsewhere, with identity standardisation.
const model: XgModel = {
  weight: [-1.5, 0.5, 0, 0, 0, 0, 0],
  bias: 0.5,
  mean: [0, 0, 0, 0, 0, 0, 0],
  scale: [1, 1, 1, 1, 1, 1, 1],
};

function ctx(x: number, y: number): ShotContext {
  return {
    location: { x, y },
    isHeader: false,
    isPenalty: false,
    isFreeKick: false,
    isCorner: false,
    isCounter: false,
  };
}

describe("client-side xG", () => {
  it("returns a probability in (0,1)", () => {
    const p = predictXg(model, ctx(0.9, 0.5));
    expect(p).toBeGreaterThan(0);
    expect(p).toBeLessThan(1);
  });

  it("scores a close central shot above a far wide one", () => {
    const close = predictXg(model, ctx(0.97, 0.5));
    const far = predictXg(model, ctx(0.55, 0.9));
    expect(close).toBeGreaterThan(far);
  });

  it("flags out-of-support inputs", () => {
    const trainMin = [0, 0, 0, 0, 0, 0, 0];
    const trainMax = [40, 1.5, 1, 1, 1, 1, 1];
    // A distance of 200 m is impossible and outside support.
    const inSupport = withinSupport(ctx(0.9, 0.5), trainMin, trainMax);
    expect(inSupport).toBe(true);
    const farCtx = ctx(-5, 0.5); // distance will exceed train max
    const out = withinSupport(farCtx, trainMin, trainMax);
    expect(out).toBe(false);
  });
});
