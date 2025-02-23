"""Loader for the machine-readable statistical dictionary.

The dictionary at ``docs/statistical_dictionary.json`` is the single source of
truth for measure definitions. Code that computes a measure can look up its
definition here so the implementation and the documented contract cannot drift. A
small validation routine checks that every measure has the required fields.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Measure:
    name: str
    grain: str
    unit: str
    numerator: str
    denominator: str | None
    exclusions: list[str]
    notes: str


def _default_path() -> Path:
    # docs/ sits next to src/ at the repository root.
    here = Path(__file__).resolve()
    root = here.parents[2]
    return root / "docs" / "statistical_dictionary.json"


def load_dictionary(path: Path | None = None) -> dict[str, Measure]:
    path = path or _default_path()
    data = json.loads(Path(path).read_text())
    out: dict[str, Measure] = {}
    for m in data["measures"]:
        measure = Measure(
            name=m["name"],
            grain=m["grain"],
            unit=m["unit"],
            numerator=m["numerator"],
            denominator=m.get("denominator"),
            exclusions=list(m.get("exclusions", [])),
            notes=m.get("notes", ""),
        )
        out[measure.name] = measure
    return out


def validate_dictionary(path: Path | None = None) -> list[str]:
    """Return a list of problems; empty when the dictionary is well formed."""
    problems: list[str] = []
    measures = load_dictionary(path)
    for name, m in measures.items():
        if not m.grain:
            problems.append(f"{name}: missing grain")
        if not m.unit:
            problems.append(f"{name}: missing unit")
        if m.unit == "ratio" and not m.denominator:
            problems.append(f"{name}: ratio measure without a denominator")
    return problems
