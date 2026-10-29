"""Averages and mixtures generators."""

import random
from fractions import Fraction
from typing import Callable

from app.domain.enums import Difficulty
from app.domain.models import SolutionStep
from app.engine.generator import Draft, _show
from app.engine.ratios import _by, _pair


def _new_member(rng: random.Random, d: Difficulty) -> Draft:
    n_lo, n_hi, a_lo, a_hi, shift = _by(d, (3, 8, 10, 40, 4), (5, 15, 20, 90, 8), (8, 25, 30, 150, 12))
    n = rng.randint(n_lo, n_hi)
    a = rng.randint(a_lo, a_hi)
    while True:
        b = a + rng.choice([-1, 1]) * rng.randint(1, shift)
        x = (n + 1) * b - n * a
        if b >= 1 and x >= 1:
            break
    total_old, total_new = n * a, (n + 1) * b
    answer = Fraction(x)
    return Draft(
        params={"n": n, "a": a, "b": b},
        text=f"The average of {n} numbers is {a}. When a new number is added, the average becomes {b}. "
             f"What is the new number?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Find the total of the original numbers.",
                         expression=f"{n} × {a} = {total_old}"),
            SolutionStep(description=f"Find the total of all {n + 1} numbers after adding the new one.",
                         expression=f"{n + 1} × {b} = {total_new}"),
            SolutionStep(description="The new number is the difference between the two totals.",
                         expression=f"{total_new} − {total_old}", result=_show(answer)),
        ],
        traps=[
            (Fraction(b), "You gave the new average. The new number is what must be added to move the old total to the new total."),
            (Fraction(n * (b - a)), "You forgot the new average itself: the new number is b + n × (change in average)."),
            (Fraction((n + 1) * (b - a)), "You forgot the old average: the new number is a + (n + 1) × (change in average)."),
            (Fraction((n + 1) * a - n * b), "You swapped the two averages when finding the difference of the totals."),
        ],
    )


def _replace(rng: random.Random, d: Difficulty) -> Draft:
    n = rng.choice(_by(d, [2, 4, 5, 10], [4, 5, 10, 20], [4, 5, 10, 20, 25]))
    a_lo, a_hi, span = _by(d, (10, 40, 20), (20, 90, 50), (30, 150, 120))
    a = rng.randint(a_lo, a_hi)
    p = rng.randint(max(1, a // 2), a * 2)
    while True:
        delta = rng.choice([-1, 1]) * rng.randint(1, span)
        q = p + delta
        if q >= 1:
            break
    change = Fraction(delta, n)
    answer = a + change
    return Draft(
        params={"n": n, "a": a, "p": p, "q": q},
        text=f"The average of {n} numbers is {a}. If one of the numbers, {p}, is replaced by {q}, "
             f"what is the new average?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Find how much the total changes.",
                         expression=f"{q} − {p} = {delta}"),
            SolutionStep(description="Share that change equally over all the numbers to get the change in the average.",
                         expression=f"{delta} / {n} = {_show(change)}"),
            SolutionStep(description="Add it to the old average.",
                         expression=f"{a} + ({_show(change)})", result=_show(answer)),
        ],
        traps=[
            (a + Fraction(delta), "You forgot to divide the change by the number of values. Only 1/n of the change reaches the average."),
            (a - change, "The direction is reversed. If the new number is larger than the old one, the average goes UP."),
            (a + Fraction(q, n), "You added the new number without removing the old one."),
            (a - Fraction(p, n), "You removed the old number but forgot to add the new one."),
            (change, "You gave only the change in the average, not the new average."),
        ],
    )


def _combined(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, t_hi, g_lo, g_hi = _by(d, (2, 6, 3, 20, 60), (3, 12, 5, 30, 90), (4, 20, 8, 40, 150))
    while True:
        b1, b2 = rng.randint(lo, hi), rng.randint(lo, hi)
        if b1 == b2:
            continue
        t = rng.randint(1, t_hi) * rng.choice([-1, 1])
        g = rng.randint(g_lo, g_hi)
        m1, m2 = g - b2 * t, g + b1 * t          # b1*(m1-g) + b2*(m2-g) = 0, so the mean is exactly g
        if m1 >= 1 and m2 >= 1:
            break
    f = rng.choice(_by(d, [5, 10], [5, 10, 20], [5, 10, 20, 25]))
    n1, n2 = b1 * f, b2 * f                      # scaling both sizes keeps the weighted mean
    t1, t2 = n1 * m1, n2 * m2
    answer = Fraction(g)                         # chosen first; the solver re-derives it from the four numbers
    return Draft(
        params={"n1": n1, "m1": m1, "n2": n2, "m2": m2},
        text=f"One class of {n1} students has an average score of {m1}, and another class of {n2} students "
             f"has an average score of {m2}. What is the average score of all the students together?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Find the total score of the first class.",
                         expression=f"{n1} × {m1} = {t1}"),
            SolutionStep(description="Find the total score of the second class.",
                         expression=f"{n2} × {m2} = {t2}"),
            SolutionStep(description="Divide the combined total by the total number of students.",
                         expression=f"({t1} + {t2}) / ({n1} + {n2}) = {t1 + t2}/{n1 + n2}",
                         result=_show(answer)),
        ],
        traps=[
            (Fraction(m1 + m2, 2), "You took the simple average of the two averages. The classes have different sizes, so they carry different weight."),
            (Fraction(n1 * m2 + n2 * m1, n1 + n2), "You swapped the weights: each average must be multiplied by ITS OWN class size."),
            (Fraction(t1 + t2, 2), "You divided the total by 2 (the number of classes) instead of the total number of students."),
        ],
    )


def _avg_speed(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi = _by(d, (1, 4), (2, 6), (3, 9))
    while True:
        a, b = _pair(rng, lo, hi)
        t = rng.randint(1, 12)
        x, y = a * (a + b) * t, b * (a + b) * t     # then 2xy/(x+y) = 2abt exactly
        if min(x, y) >= 20 and max(x, y) <= 120:
            break
    answer = Fraction(2 * a * b * t)
    return Draft(
        params={"x": x, "y": y},
        text=f"A vehicle travels from city A to city B at {x} km/h and returns along the same route at "
             f"{y} km/h. What is its average speed for the whole round trip?",
        unit="km/h",
        answer=answer,
        steps=[
            SolutionStep(description="Let the one-way distance be d. The total distance is 2d.",
                         expression="total distance = 2d"),
            SolutionStep(description="Add the times for the two journeys.",
                         expression=f"d/{x} + d/{y} = d × {x + y}/{x * y}"),
            SolutionStep(description="Average speed = total distance ÷ total time.",
                         expression=f"2 × {x} × {y} / ({x} + {y}) = {2 * x * y}/{x + y}",
                         result=_show(answer)),
        ],
        traps=[
            (Fraction(x + y, 2), "You took the simple average of the two speeds. More time is spent at the slower speed, so the true average is lower."),
            (Fraction(x * y, x + y), "You forgot the factor of 2: average speed = 2xy/(x + y)."),
        ],
    )


def _mix_quantity(rng: random.Random, d: Difficulty) -> Draft:
    lo, hi, k_hi, p_lo, p_hi = _by(d, (1, 4, 6, 20, 60), (2, 7, 10, 30, 90), (3, 10, 15, 40, 120))
    u, v = _pair(rng, lo, hi)
    s = rng.choice(_by(d, [5, 10], [2, 5, 10], [1, 2, 5]))
    k = rng.randint(2, k_hi)
    x = rng.randint(p_lo, p_hi)                  # cheaper price
    z = x + s * v                                # mixture price
    y = z + s * u                                # dearer price
    q = u * k                                    # kg of the cheaper sugar
    answer = Fraction(v * k)                     # kg of the dearer sugar (ratio route; solver uses algebra)
    return Draft(
        params={"y": y, "q": q, "x": x, "z": z},
        text=f"How many kg of sugar costing Rs {y} per kg must be mixed with {q} kg of sugar costing "
             f"Rs {x} per kg to get a mixture worth Rs {z} per kg?",
        unit="kg",
        answer=answer,
        steps=[
            SolutionStep(description="By alligation, the quantities are in the inverse ratio of the price gaps from the mixture price: cheap : dear = (dear − mean) : (mean − cheap).",
                         expression=f"({y} − {z}) : ({z} − {x}) = {s * u} : {s * v} = {u} : {v}"),
            SolutionStep(description=f"The cheaper sugar is {q} kg, which is {u} parts, so find the value of one part.",
                         expression=f"{q} / {u} = {k}"),
            SolutionStep(description=f"The dearer sugar is {v} parts.",
                         expression=f"{v} × {k}", result=_show(answer)),
        ],
        traps=[
            (Fraction(q * u, v), "You inverted the ratio. The cheaper sugar gets the part equal to (dear price − mean), not (mean − cheap price)."),
            (Fraction(q), "You assumed equal quantities of both. The mean price sits closer to one of them, so the quantities differ."),
            (Fraction(k), "You stopped at the value of ONE part."),
            (Fraction(q * (z - x), y - x), "You divided by the full price gap (dear − cheap) instead of (dear − mean)."),
        ],
    )


def _mix_replace(rng: random.Random, d: Difficulty) -> Draft:
    p_lo, p_hi, c_hi = _by(d, (4, 10, 1), (5, 12, 3), (6, 15, 5))
    while True:
        c, p = rng.randint(1, c_hi), rng.randint(p_lo, p_hi)
        if c * p * p <= 1000:
            break
    r = rng.randint(1, p - 1)
    v, a = c * p * p, c * p * (p - r)            # milk left = v * (r/p)^2 = c*r^2
    answer = Fraction(c * r * r)
    return Draft(
        params={"v": v, "a": a},
        text=f"A vessel contains {v} litres of pure milk. {a} litres are removed and replaced with water. "
             f"The same operation is then repeated once more. How many litres of milk are now in the vessel?",
        unit="litres",
        answer=answer,
        steps=[
            SolutionStep(description="After one replacement, the fraction of the vessel that is still milk is the volume left divided by the total.",
                         expression=f"({v} − {a})/{v} = {v - a}/{v}"),
            SolutionStep(description="The same fraction survives the second replacement, so multiply the original milk by it twice.",
                         expression=f"{v} × ({v - a}/{v}) × ({v - a}/{v})", result=_show(answer)),
        ],
        traps=[
            (Fraction(v - 2 * a), "You removed the same amount of milk twice. The second time, part of what is taken out is water, so less milk leaves."),
            (Fraction(v - a), "You stopped after the first replacement. The operation is repeated once more."),
            (Fraction(v) - answer, "You gave the amount of water in the vessel, not the milk."),
            (Fraction((v - a) ** 2), "You forgot to divide by the original volume."),
        ],
    )


AM_GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "avg_new_member": _new_member,
    "avg_replace": _replace,
    "avg_combined": _combined,
    "avg_speed": _avg_speed,
    "mix_quantity": _mix_quantity,
    "mix_replace": _mix_replace,
}