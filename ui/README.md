# Touchline UI

A TypeScript tactical interface. It renders a pitch and shot map, scores shots with
the exported logistic xG model (so it reproduces the server's probabilities with no
external prediction service), shows a data-coverage indicator, flags out-of-support
inputs, and supports keyboard operation.

## Run

```bash
cd ui
npm install
npm run dev        # dev server at http://localhost:5173
npm run build      # production build into dist/
npm run test       # vitest unit tests
npm run typecheck  # tsc --noEmit
```

## Keyboard

- Arrow keys move the cursor on the pitch.
- Space toggles whether the next shot is a goal.
- Enter adds the shot at the cursor and accumulates total xG.

## Model artifact

`src/model.json` is exported from the Python `LogisticXG` trained on the sample
shots (weights, feature means and scales, and the training feature ranges used for
the limited-support check). Regenerate it by running the export snippet in the
project root with the trained model.

## Narrow layouts

The layout adapts below 520px (smaller padding and heading), and the SVG scales to
its container width, so the view remains usable on a narrow screen.

## Tested logic

Pitch geometry, client-side xG, and the app state transitions are unit tested with
vitest (`*.test.ts`), independent of the browser DOM.
