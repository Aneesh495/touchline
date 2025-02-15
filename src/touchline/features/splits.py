"""Chronological and competition splits with group integrity.

Evaluation must respect time. A model is trained on matches strictly before a cut
date and tested on matches after it, so no future information leaks. For transfer
studies we also split by competition, holding out a whole competition the model
never trained on. Both splits preserve group integrity: a competition-season is a
group, and no group straddles the train/test boundary, so duplicated feeds and
within-group correlation cannot leak across the split.

Rolling-origin evaluation yields several (train, test) folds with increasing cut
dates, which is the right protocol for longitudinal forecasting: each fold trains
only on the past and tests on the next window.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class DatedItem(Generic[T]):
    item: T
    when: date
    group: str  # competition-season, used for group-integrity checks
    competition: str


@dataclass(frozen=True)
class Split(Generic[T]):
    train: list[T]
    test: list[T]
    cut: date | None
    held_out_competition: str | None = None

    def group_integrity_ok(
        self, items: Sequence[DatedItem[T]]
    ) -> bool:
        """No group appears in both train and test."""
        by_item = {id(d.item): d.group for d in items}
        train_groups = {by_item[id(x)] for x in self.train if id(x) in by_item}
        test_groups = {by_item[id(x)] for x in self.test if id(x) in by_item}
        return not (train_groups & test_groups)


def chronological_split(items: Sequence[DatedItem[T]], cut: date) -> Split[T]:
    """Train on items strictly before ``cut``, test on items on or after it."""
    train = [d.item for d in items if d.when < cut]
    test = [d.item for d in items if d.when >= cut]
    return Split(train, test, cut)


def competition_holdout_split(
    items: Sequence[DatedItem[T]], held_out: str
) -> Split[T]:
    """Hold out an entire competition for a transfer experiment."""
    train = [d.item for d in items if d.competition != held_out]
    test = [d.item for d in items if d.competition == held_out]
    return Split(train, test, None, held_out_competition=held_out)


def rolling_origin_splits(
    items: Sequence[DatedItem[T]], cuts: Sequence[date]
) -> list[Split[T]]:
    """One split per cut date, each training on the past and testing the next window.

    For cut i, train on items before cut i and test on items in [cut i, cut i+1).
    The final cut tests on everything at or after it.
    """
    ordered = sorted(cuts)
    splits: list[Split[T]] = []
    for i, cut in enumerate(ordered):
        upper = ordered[i + 1] if i + 1 < len(ordered) else None
        train = [d.item for d in items if d.when < cut]
        if upper is not None:
            test = [d.item for d in items if cut <= d.when < upper]
        else:
            test = [d.item for d in items if d.when >= cut]
        splits.append(Split(train, test, cut))
    return splits
