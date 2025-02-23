"""Statistical dictionary loads, validates, and stays consistent with prose."""

from touchline.dictionary import load_dictionary, validate_dictionary


def test_dictionary_loads_and_has_core_measures():
    d = load_dictionary()
    for name in ("xg", "action_value", "expected_threat", "points"):
        assert name in d


def test_dictionary_is_well_formed():
    assert validate_dictionary() == []


def test_ratio_measures_have_denominators():
    d = load_dictionary()
    for m in d.values():
        if m.unit == "ratio":
            assert m.denominator, f"{m.name} is a ratio without a denominator"


def test_xg_excludes_shootouts():
    d = load_dictionary()
    assert "shootout kicks" in d["xg"].exclusions
