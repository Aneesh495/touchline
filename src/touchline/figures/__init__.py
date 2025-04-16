"""Research figures generated from frozen artifacts.

Figures are generated deterministically from saved results, not from a live model,
so a figure in the report corresponds to an exact run. The generators here emit SVG
directly (no plotting dependency) so they run anywhere and the output is diffable
and small. Every figure carries the run identity it was generated from.
"""

from touchline.figures.svg_charts import (
    bar_chart_svg,
    reliability_diagram_svg,
)

__all__ = ["reliability_diagram_svg", "bar_chart_svg"]
