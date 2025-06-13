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

export function setCursor(state: AppState, x: number, y: number): void {
  state.cursor = { x: clamp01(x), y: clamp01(y) };
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
      <p class="eyebrow">TOUCHLINE / SHOT MODEL</p>
      <h1>Explore expected goals</h1>
      <p>Place an open-play shot to see its probability from the exported logistic model. The attacking goal is on the right.</p>
      <p class="coverage" role="status">${coverage || "no coverage loaded"}</p>
      <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" tabindex="0" aria-label="Pitch and shot map" aria-describedby="pitch-help">
        ${pitchSvg(W, H)}
        ${shotMarkersSvg(markers, W, H)}
      </svg>
      <p class="score" aria-live="polite">Shot estimate <strong>${preview.xg.toFixed(3)}</strong>${preview.limitedSupport ? ' <span class="warn">(limited support)</span>' : ""
    }</p>
      <div class="actions">
        <button data-action="shot" type="button">Add shot</button>
        <button data-action="goal" type="button" aria-pressed="${state.isGoal}">Mark as goal</button>
        <button data-action="clear" type="button" ${state.shots.length ? "" : "disabled"}>Clear shots</button>
      </div>
      <p role="status">Shots ${state.shots.length} · Goals ${goals} · Total xG ${totalXg.toFixed(2)}</p>
      <p id="pitch-help" class="hint">Tap the pitch to aim. On the focused pitch, use arrow keys to move, Space to toggle goal, and Enter to add a shot.</p>
      <p class="hint">Red outlines mark shots outside the model's training range. <a href="https://github.com/Aneesh495/touchline/tree/main/ui">Model export and source</a></p>
    </section>`;
}

export function addCursorShot(state: AppState): void {
  state.shots.push(scoreCursor(state));
}

// Browser wiring is kept out of the pure functions above so they can be unit
// tested. main.ts attaches the keyboard handlers and mounts renderApp.
