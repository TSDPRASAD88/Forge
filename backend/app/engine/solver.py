"""Independent solver. Must NOT import the generator."""

from fractions import Fraction
from typing import Callable


class UnknownSubtypeError(ValueError):
    pass


def _sign(direction: str) -> int:
    if direction == "increase":
        return 1
    if direction == "decrease":
        return -1
    raise ValueError(f"bad direction: {direction!r}")


def _percent_of_number(p: dict) -> Fraction:
    return Fraction(p["percent"], 100) * p["base"]


def _what_percent(p: dict) -> Fraction:
    return Fraction(p["x"], p["y"]) * 100


def _percent_change(p: dict) -> Fraction:
    # signed result: a mismatch between direction and numbers shows up as negative
    ratio = Fraction(p["new"], p["old"])
    return (ratio - 1) * _sign(p["direction"]) * 100


def _successive_change(p: dict) -> Fraction:
    m1 = 1 + Fraction(_sign(p["dir1"]) * p["p1"], 100)
    m2 = 1 + Fraction(_sign(p["dir2"]) * p["p2"], 100)
    return (m1 * m2 - 1) * 100


def _find_original(p: dict) -> Fraction:
    return Fraction(p["x"]) / Fraction(p["p"], 100)


def _discount_price(p: dict) -> Fraction:
    return Fraction(p["price"]) * (1 - Fraction(p["discount"], 100))


_SOLVERS: dict[str, Callable[[dict], Fraction]] = {
    "percent_of_number": _percent_of_number,
    "what_percent": _what_percent,
    "percent_change": _percent_change,
    "successive_change": _successive_change,
    "find_original": _find_original,
    "discount_price": _discount_price,
}


def solve(subtype: str, params: dict) -> Fraction:
    try:
        fn = _SOLVERS[subtype]
    except KeyError:
        raise UnknownSubtypeError(subtype) from None
    return fn(params)