"""Competition-season-field coverage accounting.

The coverage matrix is the honest record of what data the project actually has: for
each competition and season, how many matches are present, which fields are
available (results only, event data, 360/tracking), and which matches are missing
or carry delayed revisions. The interface reads this matrix so it can show genuine
differences between match-level, event-level, and tracking coverage rather than
implying uniform depth.
"""

from touchline.coverage.matrix import (
    CoverageCell,
    CoverageMatrix,
    FieldLevel,
)

__all__ = ["CoverageCell", "CoverageMatrix", "FieldLevel"]
