"""Simple and compound interest generators.

Principals are chosen so every answer is exact with at most 2 decimals.
"""

import random
from fractions import Fraction
from math import gcd
from typing import Callable

from app.domain.enums import Difficulty
from app.domain.models import SolutionStep
from app.engine.generator import Draft, _show
from app.engine.ratios import _by


def _si(rng: random.Random, d: Difficulty) -> Draft:
    r_pool, t_pool, step, lo, hi = _by(
        d,
        ([5, 10, 20], [1, 2, 3, 4, 5], 500, 1000, 10000),
        (list(range(3, 16)), list(range(2, 9)), 100, 1000, 20000),
        (list(range(3, 19)), list(range(2, 11)), 50, 500, 50000),
    )
    r, t = rng.choice(r_pool), rng.choice(t_pool)
    p = rng.randrange(lo, hi + 1, step)
    si = Fraction(p * r * t, 100)
    return Draft(
        params={"p": p, "r": r, "t": t},
        text=f"What is the simple interest on Rs {p} for {t} years at {r}% per annum?",
        unit="Rs",
        answer=si,
        steps=[
            SolutionStep(description="Simple interest = Principal × Rate × Time / 100.",
                         expression=f"SI = {p} × {r} × {t} / 100"),
            SolutionStep(description="Multiply and divide by 100.",
                         expression=f"{p * r * t} / 100", result=_show(si)),
        ],
        traps=[
            (Fraction(p * r * t), "You forgot to divide by 100. The rate is a percentage, so the formula ends with ÷ 100."),
            (p + si, "You gave the amount (principal + interest). The question asks only for the interest."),
            (Fraction(p * r, 100), "You calculated only ONE year's interest. Multiply by the number of years."),
        ],
    )


def _si_rate(rng: random.Random, d: Difficulty) -> Draft:
    r_pool, t_pool, lo, hi = _by(
        d,
        ([5, 10, 20, 25], [1, 2, 3, 4, 5], 1000, 10000),
        (list(range(3, 16)), list(range(2, 9)), 1000, 30000),
        (list(range(3, 19)), list(range(2, 11)), 500, 60000),
    )
    r, t = rng.choice(r_pool), rng.choice(t_pool)
    p = rng.randrange(lo, hi + 1, 100)
    si = p * r * t // 100
    answer = Fraction(r)                  # chosen first; the solver re-derives it from p, si and t
    return Draft(
        params={"p": p, "si": si, "t": t},
        text=f"A sum of Rs {p} earns a simple interest of Rs {si} in {t} years. What is the rate of interest per annum?",
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Rearrange SI = P × R × T / 100 to find the rate.",
                         expression="R = SI × 100 / (P × T)"),
            SolutionStep(description="Substitute the values.",
                         expression=f"R = {si} × 100 / ({p} × {t}) = {si * 100}/{p * t}", result=_show(answer)),
        ],
        traps=[
            (Fraction(si * 100, p), "You forgot to divide by the number of years. SI × 100 ÷ P gives rate × time, not the rate."),
            (Fraction(p * 100, si * t), "You inverted the fraction. The interest goes on top and the principal × time goes below."),
            (Fraction(si * 100, (p + si) * t), "You used the amount (principal + interest) as the principal."),
            (Fraction(si, p * t), "You forgot to multiply by 100. The rate is a percentage."),
        ],
    )


def _si_time(rng: random.Random, d: Difficulty) -> Draft:
    r_pool, t_pool, lo, hi = _by(
        d,
        ([5, 10, 20, 25], [1, 2, 3, 4, 5], 1000, 10000),
        (list(range(3, 16)), list(range(2, 9)), 1000, 30000),
        (list(range(3, 19)), list(range(2, 11)), 500, 60000),
    )
    r, t = rng.choice(r_pool), rng.choice(t_pool)
    p = rng.randrange(lo, hi + 1, 100)
    si = p * r * t // 100
    answer = Fraction(t)
    return Draft(
        params={"p": p, "si": si, "r": r},
        text=f"A sum of Rs {p} earns a simple interest of Rs {si} at {r}% per annum. For how many years was it invested?",
        unit="years",
        answer=answer,
        steps=[
            SolutionStep(description="Rearrange SI = P × R × T / 100 to find the time.",
                         expression="T = SI × 100 / (P × R)"),
            SolutionStep(description="Substitute the values.",
                         expression=f"T = {si} × 100 / ({p} × {r}) = {si * 100}/{p * r}", result=_show(answer)),
        ],
        traps=[
            (Fraction(si * 100, p), "You stopped at rate × time. Divide by the rate as well to get the time."),
            (Fraction(p * r, si * 100), "You inverted the fraction. The interest × 100 goes on top."),
            (Fraction(si * 100, (p + si) * r), "You used the amount (principal + interest) as the principal."),
            (Fraction(si, p * r), "You forgot to multiply by 100. The rate is a percentage."),
        ],
    )


def _ci_amount(rng: random.Random, d: Difficulty) -> Draft:
    r_pool, n_pool, cap = _by(
        d,
        ([10, 20], [2], 2000),
        ([5, 10, 20, 25], [2, 3], 10000),
        ([4, 8, 12, 15, 16, 24], [2, 3], 20000),
    )
    while True:
        r, n = rng.choice(r_pool), rng.choice(n_pool)
        base = Fraction(100 + r, 100).denominator ** n      # P must be a multiple of this for a whole amount
        m_lo, m_hi = max(1, -(-200 // base)), cap // base
        if m_lo <= m_hi:
            break
    p = base * rng.randint(m_lo, m_hi)
    factor = Fraction(100 + r, 100)
    amount = p * factor**n
    return Draft(
        params={"p": p, "n": n, "r": r},
        text=f"What is the amount on Rs {p} for {n} years at {r}% per annum, compounded annually?",
        unit="Rs",
        answer=amount,
        steps=[
            SolutionStep(description="Compound amount = P × (1 + R/100)^n.",
                         expression=f"A = {p} × (1 + {r}/100)^{n}"),
            SolutionStep(description="Write the bracket as a single fraction.",
                         expression=f"1 + {r}/100 = {100 + r}/100"),
            SolutionStep(description=f"Multiply by the same factor once for each of the {n} years.",
                         expression=f"{p} × " + " × ".join([f"({100 + r}/100)"] * n), result=_show(amount)),
        ],
        traps=[
            (p * (1 + Fraction(n * r, 100)), "You used simple interest. Compound interest earns interest on the interest, so multiply by (1 + R/100) once per year."),
            (amount - p, "You gave the compound interest only. The question asks for the AMOUNT (principal + interest)."),
            (p * factor ** (n - 1), "You compounded for one year too few."),
            (p * factor ** (n + 1), "You compounded for one year too many."),
        ],
    )


def _ci_diff(rng: random.Random, d: Difficulty) -> Draft:
    r_pool, cap = _by(
        d,
        ([10, 20], 5000),
        ([5, 10, 15, 20, 25], 20000),
        ([4, 6, 8, 12, 15, 16, 24], 50000),
    )
    r = rng.choice(r_pool)
    unit = 10000 // gcd(r * r, 10000)                      # P must be a multiple of this for a clean answer
    m_lo = max(1, -(-200 // unit))
    p = unit * rng.randint(m_lo, max(m_lo, cap // unit))
    n = 2
    answer = Fraction(p * r * r, 10000)                    # shortcut P(R/100)^2; the solver computes CI and SI separately
    factor = Fraction(100 + r, 100)
    return Draft(
        params={"p": p, "n": n, "r": r},
        text=f"What is the difference between the compound interest and the simple interest on Rs {p} "
             f"for {n} years at {r}% per annum, compounded annually?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Over 2 years, compound interest exceeds simple interest by the interest earned on the first year's interest: P × (R/100)².",
                         expression=f"difference = {p} × ({r}/100)²"),
            SolutionStep(description="Calculate.",
                         expression=f"{p} × {r * r} / 10000 = {p * r * r}/10000", result=_show(answer)),
        ],
        traps=[
            (p * factor**2 - p, "You gave the compound interest itself. The question asks for the DIFFERENCE between compound and simple interest."),
            (Fraction(2 * p * r, 100), "You gave the simple interest for 2 years, not the difference."),
            (Fraction(p * r * r, 100), "You divided by 100 only once. The formula needs (R/100)², so divide by 10000."),
            (Fraction(p * r, 100), "You used one year's simple interest instead of the difference."),
        ],
    )


def _si_multiple(rng: random.Random, d: Difficulty) -> Draft:
    k_pool, r_pool = _by(
        d,
        ([2], [5, 10, 20, 25]),
        ([2, 3], [2, 4, 5, 8, 10, 20, 25]),
        ([2, 3, 4, 5], [2, 4, 5, 8, 10, 16, 20, 25]),
    )
    k, r = rng.choice(k_pool), rng.choice(r_pool)
    answer = Fraction((k - 1) * 100, r)
    return Draft(
        params={"k": k, "r": r},
        text=f"In how many years will a sum of money become {k} times itself at {r}% per annum simple interest?",
        unit="years",
        answer=answer,
        steps=[
            SolutionStep(description="The total becomes k times the principal, so the interest alone equals (k − 1) times the principal.",
                         expression=f"interest = ({k} − 1) × P = {k - 1}P"),
            SolutionStep(description="Use SI = P × R × T / 100 and cancel P.",
                         expression=f"{k - 1} = {r} × T / 100"),
            SolutionStep(description="Solve for T.",
                         expression=f"T = {k - 1} × 100 / {r}", result=_show(answer)),
        ],
        traps=[
            (Fraction(k * 100, r), f"You used {k} instead of ({k} − 1). The principal is already part of the total, so the interest is only ({k} − 1) times the principal."),
            (Fraction((k - 1) * r, 100), "You inverted the fraction. T = (k − 1) × 100 / R."),
            (Fraction(100, r * (k - 1)), "You divided by (k − 1) instead of multiplying by it."),
        ],
    )


INT_GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "int_si": _si,
    "int_si_rate": _si_rate,
    "int_si_time": _si_time,
    "int_ci_amount": _ci_amount,
    "int_ci_diff": _ci_diff,
    "int_si_multiple": _si_multiple,
}