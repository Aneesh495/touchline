"""Expected assists (xA) under a stated target.

A pass's expected assists is the probability that it leads to a goal on the very
next shot, credited to the passer. The stated target is explicit: xA of a pass is
the xG of the shot it directly sets up, and zero for a pass not followed by a shot
by the same team before possession ends. This avoids the ambiguity of crediting a
passer for a goal several actions later.

The computation composes with any xG model: given the sequence of events and an
xG scorer for shots, each pass that is immediately followed by a shot from the same
possession is credited with that shot's xG.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from touchline.domain.events import Event, EventType, Shot
from touchline.features.shots import shot_features


@dataclass(frozen=True)
class AssistCredit:
    pass_event_index: int
    shot_event_index: int
    xa: float


def expected_assists(
    events: list[Event],
    shots_by_index: dict[int, Shot],
    xg_scorer: Callable[[list[float]], float],
) -> list[AssistCredit]:
    """Credit each key pass with the xG of the shot it directly sets up.

    A pass is a key pass when the next event by the same team is a shot. Only the
    immediately preceding pass is credited, so a goal is not double-credited across
    several passers.
    """
    credits: list[AssistCredit] = []
    for i, ev in enumerate(events):
        if ev.type is not EventType.PASS:
            continue
        # find the next same-team event
        for j in range(i + 1, len(events)):
            nxt = events[j]
            if nxt.team != ev.team:
                break  # possession changed before a shot
            if nxt.type is EventType.SHOT and nxt.index in shots_by_index:
                row = shot_features(shots_by_index[nxt.index])
                xa = xg_scorer(row.dense_vector())
                credits.append(AssistCredit(ev.index, nxt.index, xa))
                break
            if nxt.type is EventType.SHOT:
                break
    return credits


def total_xa_by_player(
    events: list[Event],
    shots_by_index: dict[int, Shot],
    xg_scorer: Callable[[list[float]], float],
) -> dict[str, float]:
    """Sum xA per passing player."""
    credits = expected_assists(events, shots_by_index, xg_scorer)
    index_to_player = {e.index: (e.player.value if e.player else None) for e in events}
    totals: dict[str, float] = {}
    for c in credits:
        pid = index_to_player.get(c.pass_event_index)
        if pid is None:
            continue
        totals[pid] = totals.get(pid, 0.0) + c.xa
    return totals
