"""Discipline and manpower-state effects.

A red card changes a match: the reduced team usually concedes more and scores less
for the remaining minutes. This module tracks the manpower state over a match from
dismissal events and estimates the association between going a player down and the
subsequent action value, using only information known at each moment (the card has
happened; the rest of the match has not).

It does not claim a causal effect of a specific referee decision; it reports the
association between manpower state and subsequent outcomes, with the confounders
(score state, match time, team strength) named as limitations.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.domain.events import Event, EventType


@dataclass
class ManpowerState:
    """Players on the pitch per team, updated by dismissals in time order."""

    home_players: int = 11
    away_players: int = 11

    def differential(self, home: bool) -> int:
        """Manpower advantage from a team's perspective (positive = advantage)."""
        return (
            self.home_players - self.away_players
            if home
            else self.away_players - self.home_players
        )


def track_manpower(
    events: list[Event], home_team, dismissal_predicate=None
) -> list[tuple[int, ManpowerState]]:
    """Return (event_index, manpower_state) after each dismissal.

    A dismissal is a CARD event flagged as a red in its raw payload (or detected by
    a supplied predicate). The state is carried forward so any later event can read
    the manpower differential that applied when it occurred.
    """
    if dismissal_predicate is None:
        def dismissal_predicate(ev: Event) -> bool:
            card = ev.raw.get("card", {}) if ev.raw else {}
            name = card.get("name", "") if isinstance(card, dict) else ""
            return ev.type is EventType.CARD and "Red" in name

    state = ManpowerState()
    timeline: list[tuple[int, ManpowerState]] = []
    for ev in events:
        if dismissal_predicate(ev):
            if ev.team == home_team:
                state = ManpowerState(state.home_players - 1, state.away_players)
            else:
                state = ManpowerState(state.home_players, state.away_players - 1)
            timeline.append((ev.index, ManpowerState(state.home_players, state.away_players)))
    return timeline


def post_dismissal_window(
    events: list[Event], dismissal_index: int, window: int = 50
) -> list[Event]:
    """Events in a window after a dismissal, for measuring its association."""
    out = []
    for ev in events:
        if dismissal_index < ev.index <= dismissal_index + window:
            out.append(ev)
    return out
