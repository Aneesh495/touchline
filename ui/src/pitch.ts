// Canonical pitch geometry, mirroring the Python domain so the UI speaks the same
// language. Coordinates are in the canonical [0,1]x[0,1] attacking frame: x grows
// toward the attacking goal, y to the attacking team's right. Distances are metres
// on a nominal 105x68 pitch.

export const PITCH_LENGTH_M = 105.0;
export const PITCH_WIDTH_M = 68.0;
export const GOAL_X = 1.0;
export const GOAL_Y = 0.5;
export const GOAL_HALF_WIDTH = 7.32 / 2.0 / PITCH_WIDTH_M;

export interface Point {
  x: number;
  y: number;
}

/** Euclidean distance to the goal centre in metres. */
export function distanceToGoalM(p: Point): number {
  const dx = (GOAL_X - p.x) * PITCH_LENGTH_M;
  const dy = (GOAL_Y - p.y) * PITCH_WIDTH_M;
  return Math.hypot(dx, dy);
}

/** Angle subtended by the goal mouth from a point, in radians. */
export function shotAngleRad(p: Point): number {
  const halfW = GOAL_HALF_WIDTH * PITCH_WIDTH_M;
  const dx = Math.max((GOAL_X - p.x) * PITCH_LENGTH_M, 1e-6);
  const dy = (GOAL_Y - p.y) * PITCH_WIDTH_M;
  const a1 = Math.atan2(dy + halfW, dx);
  const a2 = Math.atan2(dy - halfW, dx);
  return Math.abs(a1 - a2);
}

/** Map a canonical point to SVG pixel coordinates for a pitch of given size. */
export function toSvg(p: Point, width: number, height: number): Point {
  // x grows left-to-right toward the goal on the right; y grows downward in SVG,
  // so flip y to keep "up" as the attacking team's right side rendered upward.
  return { x: p.x * width, y: (1 - p.y) * height };
}
