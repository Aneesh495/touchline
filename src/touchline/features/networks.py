"""Passing networks from event streams.

A passing network summarises who passed to whom and the average position of each
player, which the interface renders as a graph. Edges are directed pass counts
between a passer and the receiver (the next controlling event's player on the same
team), and node positions are the mean canonical location of a player's actions.
Only completed passes with an identifiable receiver contribute an edge; a pass
without a known receiver contributes to the passer's position but to no edge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from touchline.domain.events import Event, EventType
from touchline.domain.identifiers import PlayerId, TeamId


@dataclass
class PassingNetwork:
    team: str
    node_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    node_counts: dict[str, int] = field(default_factory=dict)
    edges: dict[tuple[str, str], int] = field(default_factory=dict)

    def edge_count(self, passer: str, receiver: str) -> int:
        return self.edges.get((passer, receiver), 0)

    def total_passes(self) -> int:
        return sum(self.edges.values())


def build_passing_network(events: list[Event], team: TeamId) -> PassingNetwork:
    net = PassingNetwork(team=str(team.value))
    # accumulate positions from all located team actions
    positions: dict[str, list[tuple[float, float]]] = {}
    for e in events:
        if e.team == team and e.player is not None and e.location is not None:
            positions.setdefault(_pid(e.player), []).append((e.location.x, e.location.y))
    for pid, locs in positions.items():
        n = len(locs)
        net.node_positions[pid] = (
            sum(p[0] for p in locs) / n,
            sum(p[1] for p in locs) / n,
        )
        net.node_counts[pid] = n

    # edges: a completed pass by the team, followed by the next team action's player
    for i, e in enumerate(events):
        if (
            e.team == team
            and e.type is EventType.PASS
            and e.player is not None
            and (e.outcome_success is None or e.outcome_success)
        ):
            receiver = _next_team_player(events, i, team)
            if receiver is not None and receiver != _pid(e.player):
                key = (_pid(e.player), receiver)
                net.edges[key] = net.edges.get(key, 0) + 1
    return net


def _next_team_player(events: list[Event], i: int, team: TeamId) -> str | None:
    for j in range(i + 1, len(events)):
        if events[j].team == team and events[j].player is not None:
            return _pid(events[j].player)
        if events[j].team != team:
            return None  # possession changed; the pass did not reach a teammate
    return None


def _pid(player: PlayerId) -> str:
    return player.value
