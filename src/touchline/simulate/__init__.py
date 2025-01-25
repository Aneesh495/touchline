"""Competition rules and Monte Carlo season/tournament simulation.

The rules engine encodes how results become a table: points per result (which has
changed historically), tie-break order (which is competition- and season-specific),
and point deductions. The simulator draws many complete seasons from a match-outcome
model to produce distributions over final position, title, qualification, and
relegation, with Monte Carlo error bars. Small tournaments can be enumerated
exactly as an independent check on the sampler.
"""

from touchline.simulate.monte_carlo import (
    SeasonSimulator,
    SimulationResult,
)
from touchline.simulate.rules import (
    LeagueRules,
    TableRow,
    TieBreak,
    compute_table,
)

__all__ = [
    "LeagueRules",
    "TableRow",
    "compute_table",
    "TieBreak",
    "SeasonSimulator",
    "SimulationResult",
]
