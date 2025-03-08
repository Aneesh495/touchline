// The tactical interface entry point. It renders a pitch, a shot map scored by the
// exported xG model, a coverage indicator, and an interactive scorer that lets a
// user place a shot and read its xG. Keyboard operation is supported: arrow keys
// move the cursor, space toggles goal, and Enter adds the shot.

import { Point } from "./pitch";
import {
  CoverageBadge,
  coverageBadgeText,
  pitchSvg,
  ShotMarker,
  shotMarkersSvg,
} from "./render";
import { predictXg, ShotContext, withinSupport, XgModel } from "./xg";

export interface AppState {
  model: XgModel;
  trainMin: number[];
  trainMax: number[];
  shots: ShotMarker[];
  cursor: Point;
  isGoal: boolean;
  coverage: CoverageBadge[];
}

const W = 680;
const H = 440;

export function scoreCursor(state: AppState): ShotMarker {
  const ctx: ShotContext = {
    location: state.cursor,
    isHeader: false,
    isPenalty: false,
    isFreeKick: false,
    isCorner: false,
    isCounter: false,
  };
  const xg = predictXg(state.model, ctx);
  const supported = withinSupport(ctx, state.trainMin, state.trainMax);
  return {
    location: { ...state.cursor },
    xg,
    isGoal: state.isGoal,
    label: `shot at (${state.cursor.x.toFixed(2)}, ${state.cursor.y.toFixed(2)})`,
    limitedSupport: !supported,
  };
}

export function moveCursor(state: AppState, dx: number, dy: number): void {
  state.cursor.x = clamp01(state.cursor.x + dx);
  state.cursor.y = clamp01(state.cursor.y + dy);
}

function clamp01(v: number): number {
  return v < 0 ? 0 : v > 1 ? 1 : v;
}

export function renderApp(state: AppState): string {
  const preview = scoreCursor(state);
  const markers = [...state.shots, preview];
  const totalXg = state.shots.reduce((a, s) => a + s.xg, 0);
  const goals = state.shots.filter((s) => s.isGoal).length;
  const coverage = state.coverage.map(coverageBadgeText).join(" | ");
  return `
    <section>
      <h1>Touchline tactical view</h1>
      <p class="coverage" role="status">${coverage || "no coverage loaded"}</p>
      <svg width="${W}" height="${H}" role="img" aria-label="pitch and shot map">
        ${pitchSvg(W, H)}
        ${shotMarkersSvg(markers, W, H)}
      </svg>
      <p>cursor xG <strong>${preview.xg.toFixed(3)}</strong>${preview.limitedSupport ? ' <span class="warn">(limited support)</span>' : ""
    }</p>
      <p>shots ${state.shots.length}, goals ${goals}, total xG ${totalXg.toFixed(2)}</p>
      <p class="hint">arrow keys move, space toggles goal, enter adds the shot</p>
    </section>`;
}

export function addCursorShot(state: AppState): void {
  state.shots.push(scoreCursor(state));
}

// Browser wiring is kept out of the pure functions above so they can be unit
// tested. main.ts attaches the keyboard handlers and mounts renderApp.
