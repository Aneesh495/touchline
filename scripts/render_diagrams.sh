#!/usr/bin/env bash
# Render all Mermaid diagrams under docs/diagrams to SVG next to their source.
# Requires node/npx; uses @mermaid-js/mermaid-cli via npx.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/diagrams/svg
for f in docs/diagrams/*.mmd; do
  base="$(basename "$f" .mmd)"
  echo "rendering $base"
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "docs/diagrams/svg/${base}.svg" -b transparent
done
echo "done"
