"""Minimal SVG chart generators for research figures.

Pure functions that take data and return an SVG string. Kept dependency-free so
figure generation is reproducible and the output is small and reviewable. Each
accepts a ``run_id`` that is embedded as a caption so a figure is traceable to the
run that produced it.
"""

from __future__ import annotations


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def reliability_diagram_svg(
    mean_pred: list[float],
    observed: list[float],
    counts: list[int],
    run_id: str,
    width: int = 360,
    height: int = 360,
) -> str:
    """A reliability diagram: observed rate vs mean prediction per bin.

    The diagonal is perfect calibration. Point area scales with bin count so sparse
    bins are visibly less certain. ``run_id`` is captioned for traceability.
    """
    pad = 40
    plot_w = width - 2 * pad
    plot_h = height - 2 * pad

    def px(v: float) -> float:
        return pad + v * plot_w

    def py(v: float) -> float:
        return pad + (1 - v) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        # axes
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height - pad}" stroke="#333"/>',
        f'<line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" stroke="#333"/>',
        # perfect-calibration diagonal
        f'<line x1="{px(0)}" y1="{py(0)}" x2="{px(1)}" y2="{py(1)}" '
        f'stroke="#bbb" stroke-dasharray="4 4"/>',
    ]
    max_count = max(counts) if counts else 1
    for mp, ob, c in zip(mean_pred, observed, counts, strict=True):
        if c == 0:
            continue
        r = 2 + 6 * (c / max_count) ** 0.5
        parts.append(
            f'<circle cx="{px(mp):.1f}" cy="{py(ob):.1f}" r="{r:.1f}" '
            f'fill="#2563eb" fill-opacity="0.7"/>'
        )
    parts.append(
        f'<text x="{pad}" y="{height - 10}" font-size="11" fill="#555">'
        f"predicted -&gt; observed | {_escape(run_id)}</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def bar_chart_svg(
    labels: list[str],
    values: list[float],
    run_id: str,
    width: int = 420,
    height: int = 300,
) -> str:
    """A horizontal bar chart (e.g. title probabilities), labelled with run_id."""
    pad = 100
    plot_w = width - pad - 20
    n = len(values)
    if n == 0:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"></svg>'
    bar_h = (height - 40) / n
    vmax = max(values) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    for i, (lab, v) in enumerate(zip(labels, values, strict=True)):
        y = 10 + i * bar_h
        w = (v / vmax) * plot_w
        parts.append(
            f'<rect x="{pad}" y="{y:.1f}" width="{w:.1f}" height="{bar_h * 0.7:.1f}" '
            f'fill="#0ea5e9"/>'
        )
        parts.append(
            f'<text x="{pad - 6}" y="{y + bar_h * 0.45:.1f}" font-size="11" '
            f'text-anchor="end" fill="#333">{_escape(lab)}</text>'
        )
        parts.append(
            f'<text x="{pad + w + 4:.1f}" y="{y + bar_h * 0.45:.1f}" font-size="11" '
            f'fill="#333">{v:.3f}</text>'
        )
    parts.append(
        f'<text x="10" y="{height - 6}" font-size="11" fill="#555">{_escape(run_id)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)
