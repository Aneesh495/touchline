"""Carry and dribble value under observed-event eligibility.

A carry moves the ball while a player retains control; a dribble is a take-on
against an opponent. Both are valued by the territory they gain toward the goal and
by their action value (the change in score-minus-concede probability). We do not
infer movement distance from sparse events as if tracking measured it: a carry's
gain is the difference between its recorded start and end locations only.

Dribble success is modelled as a logistic function of location and context, with
the denominator being take-on attempts. The value of a successful carry/dribble is
read from the action-value model, so this module composes with it rather than
reinventing a target.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.domain.events import Event, EventType


@dataclass(frozen=True)
class CarryGain:
    start_x: float
    end_x: float
    forward_gain: float  # toward the attacking goal, canonical frame
    lateral: float

    @property
    def is_progressive(self) -> bool:
        remaining = max(1.0 - self.start_x, 1e-6)
        return self.forward_gain >= 0.10 * remaining


def carry_gain(ev: Event) -> CarryGain | None:
    """Territory gained by a carry from its recorded endpoints only."""
    if ev.type is not EventType.CARRY or ev.location is None:
        return None
    end = ev.end_location or ev.location
    return CarryGain(
        start_x=ev.location.x,
        end_x=end.x,
        forward_gain=end.x - ev.location.x,
        lateral=abs(end.y - ev.location.y),
    )


@dataclass
class DribbleOutcome:
    attempts: int
    successes: int

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts else 0.0


def dribble_outcomes(events: list[Event]) -> DribbleOutcome:
    """Count dribble attempts and successes from observed events only.

    Success uses the event's ``outcome_success`` when the provider supplies it;
    events without a recorded outcome are counted as attempts but not successes,
    and that missingness is visible in the ratio's denominator.
    """
    attempts = 0
    successes = 0
    for ev in events:
        if ev.type is EventType.DRIBBLE:
            attempts += 1
            if ev.outcome_success:
                successes += 1
    return DribbleOutcome(attempts, successes)
