"""Ratio and proportion generators. Same structure as the percentage generators."""

import random
from fractions import Fraction
from math import gcd
from typing import Callable

from app.domain.enums import Difficulty
from app.domain.models import SolutionStep
from app.engine.generator import Draft, _show

ITEMS = ["notebooks", "pens", "pencils", "books", "mangoes"]


def _by(d: Difficulty, easy, medium, hard):
    return {Difficulty.EASY: easy, Difficulty.MEDIUM: medium, Difficulty.HARD: hard}[d]


def _pair(rng: random.Random, lo: int, hi: int) -> tuple[int, int]:
    """Two different, coprime ratio terms in [lo, hi]."""
    while True:
        a, b = rng.randint(lo, hi), rng.randint(lo, hi)
        if a != b and gcd(a, b) == 1:
            return a, b


def _ratio_share(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, k_lo, k_hi = _by(d, (1, 5, 2, 20), (2, 9, 10, 90), (3, 13, 20, 200))
    a, b = _pair(rng, lo, hi)
    k = rng.randint(k_lo, k_hi)
    parts = a + b
    total = k * parts
    answer = Fraction(a * k)
    return Draft(
        params={"total": total, "a": a, "b": b},
        text=f"A sum of Rs {total} is divided between two people in the ratio {a}:{b}. How much does the first person get?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Add the ratio terms to find the total number of parts.",
                         expression=f"{a} + {b} = {parts}"),
            SolutionStep(description="Divide the total by the number of parts to get the value of one part.",
                         expression=f"{total} / {parts} = {k}"),
            SolutionStep(description="Multiply by the first person's number of parts.",
                         expression=f"{a} × {k}", result=_show(answer)),
        ],
        traps=[
            (Fraction(b * k), "You gave the second person's share. The first person's share uses the first ratio term."),
            (Fraction(k), "You stopped at the value of ONE part. Multiply it by the number of parts the first person gets."),
            (Fraction(total, a), f"You divided the total by {a} instead of by the total number of parts ({a} + {b})."),
            (Fraction(total * a, b), f"You treated the ratio {a}:{b} as the fraction {a}/{b} of the total. The whole is {a} + {b} parts."),
        ],
    )


def _ratio_missing_term(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, k_lo, k_hi = _by(d, (1, 6, 2, 15), (2, 9, 5, 40), (3, 13, 10, 90))
    a, b = _pair(rng, lo, hi)
    k = rng.randint(k_lo, k_hi)
    x = a * k
    answer = Fraction(b * k)
    return Draft(
        params={"a": a, "b": b, "x": x},
        text=f"The ratio of two numbers is {a}:{b}. If the first number is {x}, what is the second number?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Divide the first number by its ratio term to get the value of one part.",
                         expression=f"{x} / {a} = {k}"),
            SolutionStep(description="Multiply by the second ratio term.",
                         expression=f"{b} × {k}", result=_show(answer)),
        ],
        traps=[
            (Fraction(x * a, b), f"You inverted the ratio: you computed {x} × {a}/{b} instead of {x} × {b}/{a}."),
            (Fraction(x + (b - a)), "You added the difference of the ratio terms. Ratios scale numbers by multiplying, not adding."),
            (Fraction(x * b), f"You multiplied by {b} but forgot to divide by {a}."),
            (Fraction(k), "You stopped at the value of ONE part."),
        ],
    )


def _proportion(rng: random.Random, d: Difficulty) -> Draft:
    a_lo, a_hi, r_lo, r_hi, c_lo, c_hi = _by(
        d, (2, 10, 2, 20, 2, 20), (3, 20, 5, 60, 3, 40), (6, 30, 10, 150, 6, 80)
    )
    a = rng.randint(a_lo, a_hi)
    c = a
    while c == a:
        c = rng.randint(c_lo, c_hi)
    r = rng.randint(r_lo, r_hi)          # cost of one item, chosen first
    b = r * a
    answer = Fraction(r * c)
    item = rng.choice(ITEMS)
    return Draft(
        params={"a": a, "b": b, "c": c},
        text=f"If {a} {item} cost Rs {b}, what is the cost of {c} {item}?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Find the cost of one item by dividing the cost by the number of items.",
                         expression=f"{b} / {a} = {r}"),
            SolutionStep(description="Multiply by the new number of items.",
                         expression=f"{r} × {c}", result=_show(answer)),
        ],
        traps=[
            (Fraction(b * a, c), f"You inverted the proportion: you multiplied by {a}/{c} instead of {c}/{a}. More items always cost more."),
            (Fraction(b + (c - a)), "You added the difference in item counts to the cost. Cost scales by multiplying, not adding."),
            (Fraction(b * c), "You multiplied the cost by the number of items. First divide to get the cost of ONE item."),
            (Fraction(r), "You stopped at the cost of one item."),
        ],
    )


def _ratio_difference(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, k_lo, k_hi = _by(d, (2, 6, 2, 15), (3, 10, 5, 40), (4, 14, 10, 90))
    a, b = _pair(rng, lo, hi)
    if a < b:
        a, b = b, a                       # a is the larger term
    k = rng.randint(k_lo, k_hi)
    diff = (a - b) * k
    answer = Fraction(a * k)
    return Draft(
        params={"a": a, "b": b, "d": diff},
        text=f"Two numbers are in the ratio {a}:{b} and their difference is {diff}. What is the larger number?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Find how many parts make up the difference.",
                         expression=f"{a} − {b} = {a - b}"),
            SolutionStep(description="Divide the given difference by that to get the value of one part.",
                         expression=f"{diff} / {a - b} = {k}"),
            SolutionStep(description="Multiply by the larger ratio term.",
                         expression=f"{a} × {k}", result=_show(answer)),
        ],
        traps=[
            (Fraction(b * k), "You found the smaller number. The larger number uses the bigger ratio term."),
            (Fraction(k), "You stopped at the value of ONE part."),
            (Fraction(diff * a, a + b), f"You added the ratio terms. The difference is {a} − {b} parts, not {a} + {b}."),
        ],
    )


def _ratio_chain(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, k_lo, k_hi = _by(d, (1, 4, 2, 6), (2, 7, 2, 8), (2, 9, 3, 12))
    while True:
        p, q = _pair(rng, lo, hi)
        r, s = _pair(rng, lo, hi)
        if q != r:                        # B terms differ, so they must be matched
            break
    k = rng.randint(k_lo, k_hi)
    x = q * s * k                         # C
    pr, qr, qs = p * r, q * r, q * s
    answer = Fraction(pr * k)             # A
    return Draft(
        params={"p": p, "q": q, "r": r, "s": s, "x": x},
        text=f"The ratio A:B is {p}:{q} and the ratio B:C is {r}:{s}. If C is {x}, what is A?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Make the B terms equal by cross-multiplying each ratio.",
                         expression=f"A:B = {pr}:{qr},  B:C = {qr}:{qs}"),
            SolutionStep(description="Combine them into one three-part ratio.",
                         expression=f"A:B:C = {pr}:{qr}:{qs}"),
            SolutionStep(description=f"C is {qs} parts, so find the value of one part.",
                         expression=f"{x} / {qs} = {k}"),
            SolutionStep(description="Multiply by A's number of parts.",
                         expression=f"{pr} × {k}", result=_show(answer)),
        ],
        traps=[
            (Fraction(qr * k), "You found B, the middle term, instead of A."),
            (Fraction(x * p, q), "You used only the first ratio and treated C as B. Link the two ratios through B."),
            (Fraction(x * p * s, q * r), f"You flipped the second ratio (used {s}:{r} instead of {r}:{s})."),
        ],
    )


RATIO_GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "ratio_share": _ratio_share,
    "ratio_missing_term": _ratio_missing_term,
    "proportion": _proportion,
    "ratio_difference": _ratio_difference,
    "ratio_chain": _ratio_chain,
}