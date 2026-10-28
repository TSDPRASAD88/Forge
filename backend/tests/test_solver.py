from fractions import Fraction

import pytest

from app.engine.solver import UnknownSubtypeError, solve

CASES = [
    ("percent_of_number", {"percent": 20, "base": 150}, Fraction(30)),
    ("percent_of_number", {"percent": 12, "base": 250}, Fraction(30)),
    ("what_percent", {"x": 30, "y": 120}, Fraction(25)),
    ("what_percent", {"x": 1, "y": 8}, Fraction(25, 2)),
    ("percent_change", {"old": 200, "new": 250, "direction": "increase"}, Fraction(25)),
    ("percent_change", {"old": 250, "new": 200, "direction": "decrease"}, Fraction(20)),
    ("successive_change", {"p1": 20, "p2": 10, "dir1": "increase", "dir2": "decrease"}, Fraction(8)),
    ("successive_change", {"p1": 20, "p2": 20, "dir1": "decrease", "dir2": "increase"}, Fraction(-4)),
    ("successive_change", {"p1": 25, "p2": 20, "dir1": "increase", "dir2": "decrease"}, Fraction(0)),
    ("find_original", {"x": 30, "p": 20}, Fraction(150)),
    ("discount_price", {"price": 800, "discount": 15}, Fraction(680)),
]


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


def test_wrong_direction_gives_negative():
    # numbers went up but direction says decrease -> negative, which the validator flags
    assert solve("percent_change", {"old": 200, "new": 250, "direction": "decrease"}) == Fraction(-25)


def test_unknown_subtype():
    with pytest.raises(UnknownSubtypeError):
        solve("nope", {})


def test_bad_direction():
    with pytest.raises(ValueError):
        solve("percent_change", {"old": 1, "new": 2, "direction": "sideways"})