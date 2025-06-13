// Browser entry: mount the app, load the exported model artifact, and wire the
// keyboard. Falls back to a bundled default model so the UI runs without a server.

import { addCursorShot, AppState, moveCursor, renderApp, setCursor } from "./app";
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
  const active = document.activeElement;
  const action = active instanceof HTMLElement ? active.dataset.action : undefined;
  const pitchFocused = active instanceof SVGElement && active.matches("svg[tabindex]");
  root.innerHTML = renderApp(state);
  if (pitchFocused) root.querySelector<SVGElement>("svg")?.focus({ preventScroll: true });
  if (action) {
    const button = root.querySelector<HTMLButtonElement>(`[data-action="${action}"]`);
    (button?.disabled ? root.querySelector<HTMLButtonElement>('[data-action="shot"]') : button)
      ?.focus({ preventScroll: true });
  }
}

async function main(): Promise<void> {
  const root = document.getElementById("app");
  if (!root) return;
  const state = await loadState();
  mount(root, state);
  root.addEventListener("click", (e) => {
    if (!(e.target instanceof Element)) return;
    const button = e.target.closest<HTMLButtonElement>("button[data-action]");
    const pitch = e.target.closest<SVGSVGElement>("svg");
    if (pitch) {
      const box = pitch.getBoundingClientRect();
      setCursor(state, (e.clientX - box.left) / box.width, 1 - (e.clientY - box.top) / box.height);
    } else if (button?.dataset.action === "shot") addCursorShot(state);
    else if (button?.dataset.action === "goal") state.isGoal = !state.isGoal;
    else if (button?.dataset.action === "clear") state.shots = [];
    else return;
    mount(root, state);
  });
  root.addEventListener("keydown", (e) => {
    if (!(e.target instanceof SVGElement) || !e.target.matches("svg[tabindex]")) return;
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
