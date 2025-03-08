// Client-side xG scoring from exported logistic weights. The weights, feature
// means, and scales are produced by the Python LogisticXG and shipped as a JSON
// model artifact, so the UI reproduces the same probabilities the server computed,
// with no external prediction service.

import { distanceToGoalM, Point, shotAngleRad } from "./pitch";

export interface XgModel {
  weight: number[];
  bias: number;
  mean: number[];
  scale: number[];
}

export interface ShotContext {
  location: Point;
  isHeader: boolean;
  isPenalty: boolean;
  isFreeKick: boolean;
  isCorner: boolean;
  isCounter: boolean;
}

/** Build the dense feature vector in the same order as the Python model. */
export function shotFeatures(s: ShotContext): number[] {
  return [
    distanceToGoalM(s.location),
    shotAngleRad(s.location),
    s.isHeader ? 1 : 0,
    s.isPenalty ? 1 : 0,
    s.isFreeKick ? 1 : 0,
    s.isCorner ? 1 : 0,
    s.isCounter ? 1 : 0,
  ];
}

function sigmoid(z: number): number {
  const c = Math.max(-30, Math.min(30, z));
  return 1 / (1 + Math.exp(-c));
}

/** Predict xG for a shot context using the exported model. */
export function predictXg(model: XgModel, s: ShotContext): number {
  const x = shotFeatures(s);
  let z = model.bias;
  for (let i = 0; i < x.length; i++) {
    const standardised = (x[i] - model.mean[i]) / model.scale[i];
    z += standardised * model.weight[i];
  }
  return sigmoid(z);
}

/** Whether an input is within the model's training support on every feature. */
export function withinSupport(
  s: ShotContext,
  trainMin: number[],
  trainMax: number[]
): boolean {
  const x = shotFeatures(s);
  for (let i = 0; i < x.length; i++) {
    if (x[i] < trainMin[i] || x[i] > trainMax[i]) return false;
  }
  return true;
}
