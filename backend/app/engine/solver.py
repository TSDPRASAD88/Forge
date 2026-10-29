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

# ---------- profit and loss ----------

def _pl_profit_percent(p: dict) -> Fraction:
    return (Fraction(p["sp"], p["cp"]) - 1) * 100


def _pl_loss_percent(p: dict) -> Fraction:
    return (1 - Fraction(p["sp"], p["cp"])) * 100


def _pl_selling_price(p: dict) -> Fraction:
    return Fraction(p["cp"]) * (1 + Fraction(p["p"], 100))


def _pl_cost_price(p: dict) -> Fraction:
    return Fraction(p["sp"]) / (1 - Fraction(p["l"], 100))


def _pl_markup_discount(p: dict) -> Fraction:
    marked = 1 + Fraction(p["m"], 100)
    after_discount = marked * (1 - Fraction(p["d"], 100))
    return (after_discount - 1) * 100


def _pl_two_articles(p: dict) -> Fraction:
    # derive from cost prices: each article sells for 1 unit
    cp_gain = Fraction(100, 100 + p["p"])
    cp_loss = Fraction(100, 100 - p["p"])
    total_cp = cp_gain + cp_loss
    return (total_cp - 2) / total_cp * 100


_SOLVERS.update(
    {
        "pl_profit_percent": _pl_profit_percent,
        "pl_loss_percent": _pl_loss_percent,
        "pl_selling_price": _pl_selling_price,
        "pl_cost_price": _pl_cost_price,
        "pl_markup_discount": _pl_markup_discount,
        "pl_two_articles": _pl_two_articles,
    }
)

# ---------- time and work ----------

def _tw_together(p: dict) -> Fraction:
    return 1 / (Fraction(1, p["x"]) + Fraction(1, p["y"]))


def _tw_alone(p: dict) -> Fraction:
    return 1 / (Fraction(1, p["t"]) - Fraction(1, p["x"]))


def _tw_leaving(p: dict) -> Fraction:
    done = p["d"] * (Fraction(1, p["x"]) + Fraction(1, p["y"]))
    return (1 - done) * p["y"]


def _tw_wages(p: dict) -> Fraction:
    rate_a, rate_b = Fraction(1, p["x"]), Fraction(1, p["y"])
    return Fraction(p["w"]) * rate_a / (rate_a + rate_b)


def _tw_pipes(p: dict) -> Fraction:
    return 1 / (Fraction(1, p["f"]) - Fraction(1, p["e"]))


_SOLVERS.update(
    {
        "tw_together": _tw_together,
        "tw_alone": _tw_alone,
        "tw_leaving": _tw_leaving,
        "tw_wages": _tw_wages,
        "tw_pipes": _tw_pipes,
    }
)

# ---------- averages and mixtures ----------

def _avg_new_member(p: dict) -> Fraction:
    # new number = new average + n x (change in average)
    return Fraction(p["b"]) + p["n"] * (p["b"] - p["a"])


def _avg_replace(p: dict) -> Fraction:
    # recompute the total, swap the number, divide again
    return Fraction(p["n"] * p["a"] - p["p"] + p["q"], p["n"])


def _avg_combined(p: dict) -> Fraction:
    return Fraction(p["n1"] * p["m1"] + p["n2"] * p["m2"], p["n1"] + p["n2"])


def _avg_speed(p: dict) -> Fraction:
    # total distance / total time, taking a one-way distance of 1
    return 2 / (Fraction(1, p["x"]) + Fraction(1, p["y"]))


def _mix_quantity(p: dict) -> Fraction:
    # q*x + w*y = z*(q + w)  =>  w = q*(z - x)/(y - z)
    return Fraction(p["q"] * (p["z"] - p["x"]), p["y"] - p["z"])


def _mix_replace(p: dict) -> Fraction:
    return Fraction(p["v"]) * (1 - Fraction(p["a"], p["v"])) ** 2


_SOLVERS.update(
    {
        "avg_new_member": _avg_new_member,
        "avg_replace": _avg_replace,
        "avg_combined": _avg_combined,
        "avg_speed": _avg_speed,
        "mix_quantity": _mix_quantity,
        "mix_replace": _mix_replace,
    }
)

# ---------- simple and compound interest ----------

def _int_si(p: dict) -> Fraction:
    return Fraction(p["p"]) * Fraction(p["r"], 100) * p["t"]


def _int_si_rate(p: dict) -> Fraction:
    return Fraction(p["si"]) / (p["p"] * Fraction(p["t"], 100))


def _int_si_time(p: dict) -> Fraction:
    return Fraction(p["si"]) / (p["p"] * Fraction(p["r"], 100))


def _int_ci_amount(p: dict) -> Fraction:
    return Fraction(p["p"]) * (1 + Fraction(p["r"], 100)) ** p["n"]


def _int_ci_diff(p: dict) -> Fraction:
    principal, rate = Fraction(p["p"]), Fraction(p["r"], 100)
    compound = principal * ((1 + rate) ** p["n"] - 1)
    simple = principal * rate * p["n"]
    return compound - simple


def _int_si_multiple(p: dict) -> Fraction:
    return (p["k"] - 1) / Fraction(p["r"], 100)


_SOLVERS.update(
    {
        "int_si": _int_si,
        "int_si_rate": _int_si_rate,
        "int_si_time": _int_si_time,
        "int_ci_amount": _int_ci_amount,
        "int_ci_diff": _int_ci_diff,
        "int_si_multiple": _int_si_multiple,
    }
)