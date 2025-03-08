// Browser entry: mount the app, load the exported model artifact, and wire the
// keyboard. Falls back to a bundled default model so the UI runs without a server.

import { addCursorShot, AppState, moveCursor, renderApp } from "./app";
import defaultModel from "./model.json";

async function loadState(): Promise<AppState> {
  const m = defaultModel as {
    weight: number[];
    bias: number;
    mean: number[];
    scale: number[];
    train_min: number[];
    train_max: number[];
  };
  return {
    model: { weight: m.weight, bias: m.bias, mean: m.mean, scale: m.scale },
    trainMin: m.train_min,
    trainMax: m.train_max,
    shots: [],
    cursor: { x: 0.85, y: 0.5 },
    isGoal: false,
    coverage: [
      { competition: "SAMPLE", season: "2023-2024", level: "events", matches: 90 },
    ],
  };
}

function mount(root: HTMLElement, state: AppState): void {
  root.innerHTML = renderApp(state);
}

async function main(): Promise<void> {
  const root = document.getElementById("app");
  if (!root) return;
  const state = await loadState();
  mount(root, state);
  window.addEventListener("keydown", (e) => {
    const step = 0.02;
    if (e.key === "ArrowLeft") moveCursor(state, -step, 0);
    else if (e.key === "ArrowRight") moveCursor(state, step, 0);
    else if (e.key === "ArrowUp") moveCursor(state, 0, step);
    else if (e.key === "ArrowDown") moveCursor(state, 0, -step);
    else if (e.key === " ") state.isGoal = !state.isGoal;
    else if (e.key === "Enter") addCursorShot(state);
    else return;
    e.preventDefault();
    mount(root, state);
  });
}

main();
