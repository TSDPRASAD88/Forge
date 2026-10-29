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


# ---------- ratios and proportion ----------

def _ratio_share(p: dict) -> Fraction:
    # first person's share = total x a/(a+b)
    return Fraction(p["total"]) * Fraction(p["a"], p["a"] + p["b"])


def _ratio_missing_term(p: dict) -> Fraction:
    return Fraction(p["x"]) * Fraction(p["b"], p["a"])


def _proportion(p: dict) -> Fraction:
    # cross-multiplication: cost2 = cost1 x (items2 / items1)
    return Fraction(p["b"]) * Fraction(p["c"], p["a"])


def _ratio_difference(p: dict) -> Fraction:
    return Fraction(p["d"]) * Fraction(p["a"], p["a"] - p["b"])


def _ratio_chain(p: dict) -> Fraction:
    # A/C = (A/B) x (B/C) = (p/q) x (r/s)
    return Fraction(p["x"]) * Fraction(p["p"], p["q"]) * Fraction(p["r"], p["s"])


_SOLVERS.update(
    {
        "ratio_share": _ratio_share,
        "ratio_missing_term": _ratio_missing_term,
        "proportion": _proportion,
        "ratio_difference": _ratio_difference,
        "ratio_chain": _ratio_chain,
    }
)