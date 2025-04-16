"""Figure generation oracles: valid SVG, traceable run id."""

from touchline.figures.svg_charts import bar_chart_svg, reliability_diagram_svg


def test_reliability_diagram_is_valid_svg_with_run_id():
    svg = reliability_diagram_svg(
        mean_pred=[0.1, 0.3, 0.5, 0.7, 0.9],
        observed=[0.08, 0.33, 0.48, 0.72, 0.85],
        counts=[100, 80, 60, 40, 20],
        run_id="xg_logistic_s0",
    )
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "xg_logistic_s0" in svg
    # a circle per non-empty bin
    assert svg.count("<circle") == 5


def test_empty_bins_are_skipped():
    svg = reliability_diagram_svg(
        mean_pred=[0.1, 0.5],
        observed=[0.1, 0.5],
        counts=[0, 10],
        run_id="r",
    )
    assert svg.count("<circle") == 1


def test_bar_chart_shows_values_and_run_id():
    svg = bar_chart_svg(
        labels=["Club A", "Club B"],
        values=[0.6, 0.3],
        run_id="forecast_point",
    )
    assert "Club A" in svg
    assert "0.600" in svg
    assert "forecast_point" in svg
    assert svg.count("<rect") >= 3  # background + two bars


def test_bar_chart_handles_empty():
    svg = bar_chart_svg([], [], run_id="r")
    assert svg.startswith("<svg")
