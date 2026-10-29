"""Time and work generators.

Every question is built from one family of numbers (a, b coprime, m a multiplier):
    x = b*m*(a+b)    y = a*m*(a+b)    t = a*b*m
so that 1/x + 1/y = 1/t holds exactly and every answer is a whole number.
"""

import random
from fractions import Fraction
from typing import Callable

from app.domain.enums import Difficulty
from app.domain.models import SolutionStep
from app.engine.generator import Draft, _show
from app.engine.ratios import _by, _pair

MAX_DAYS = 120


def _family(rng: random.Random, d: Difficulty, need_leaver: bool = False):
    lo, hi, m_lo, m_hi = _by(d, (1, 4, 1, 2), (2, 6, 1, 2), (3, 8, 1, 1))
    while True:
        a, b = _pair(rng, lo, hi)
        m = rng.randint(m_lo, m_hi)
        x, y, t = b * m * (a + b), a * m * (a + b), a * b * m
        if max(x, y) > MAX_DAYS:
            continue
        if need_leaver and a * m < 2:     # need at least one valid "days worked together" value
            continue
        return a, b, m, x, y, t


def _together(rng: random.Random, d: Difficulty) -> Draft:
    a, b, m, x, y, t = _family(rng, d)
    answer = Fraction(t)
    return Draft(
        params={"x": x, "y": y},
        text=f"A can complete a piece of work in {x} days and B can complete it in {y} days. "
             f"In how many days will they finish it working together?",
        unit="days",
        answer=answer,
        steps=[
            SolutionStep(description="Find the part of the work each person does in one day.",
                         expression=f"A: 1/{x},  B: 1/{y}"),
            SolutionStep(description="Add the daily work rates.",
                         expression=f"1/{x} + 1/{y} = ({y} + {x})/({x} × {y}) = {x + y}/{x * y}"),
            SolutionStep(description="Take the reciprocal to get the number of days.",
                         expression=f"{x * y}/{x + y}", result=_show(answer)),
        ],
        traps=[
            (Fraction(x + y, 2), "You averaged the two times. Working together is faster than either person alone, so the answer must be smaller than both."),
            (Fraction(x + y), "You added the days. Together they work faster. Add the daily work (1/days), never the days."),
            (Fraction(abs(x - y)), "You subtracted the days. Add the work done per day (1/x + 1/y), then take the reciprocal."),
        ],
    )


def _alone(rng: random.Random, d: Difficulty) -> Draft:
    a, b, m, x, y, t = _family(rng, d)
    given, asked = (x, y) if rng.random() < 0.5 else (y, x)
    answer = Fraction(asked)              # chosen first; the solver re-derives it from t and the given time
    return Draft(
        params={"t": t, "x": given},
        text=f"A and B together can finish a piece of work in {t} days. A alone can finish it in {given} days. "
             f"In how many days can B alone finish it?",
        unit="days",
        answer=answer,
        steps=[
            SolutionStep(description="Find the work done per day together and by A alone.",
                         expression=f"Together: 1/{t},  A alone: 1/{given}"),
            SolutionStep(description="Subtract A's rate from the combined rate to get B's rate.",
                         expression=f"1/{t} − 1/{given} = {given - t}/{t * given}"),
            SolutionStep(description="Take the reciprocal to get the days B needs alone.",
                         expression=f"{t * given}/{given - t}", result=_show(answer)),
        ],
        traps=[
            (Fraction(given - t), "You subtracted the days directly. Subtract the work RATES (1/t − 1/x), then take the reciprocal."),
            (Fraction(t * given, t + given), "You added A's rate to the combined rate. B's rate is the combined rate MINUS A's rate."),
            (Fraction(given + t), "You added the days. Work with daily rates (1/days) instead."),
        ],
    )


def _leaving(rng: random.Random, d: Difficulty) -> Draft:
    a, b, m, x, y, t = _family(rng, d, need_leaver=True)
    j = rng.randint(1, a * m - 1)
    days_together = b * j                 # multiple of b, so the answer stays a whole number
    answer = Fraction((a + b) * (a * m - j))
    left = t - days_together
    return Draft(
        params={"x": x, "y": y, "d": days_together},
        text=f"A can finish a piece of work in {x} days and B in {y} days. They start working together, "
             f"but A leaves after {days_together} days. In how many more days will B finish the remaining work?",
        unit="days",
        answer=answer,
        steps=[
            SolutionStep(description="Find the work done per day by both together.",
                         expression=f"1/{x} + 1/{y} = 1/{t}"),
            SolutionStep(description=f"Find the fraction of the work left after {days_together} days together.",
                         expression=f"1 − {days_together}/{t} = {left}/{t}"),
            SolutionStep(description="B finishes the rest alone: multiply the remaining fraction by B's full time.",
                         expression=f"({left}/{t}) × {y}", result=_show(answer)),
        ],
        traps=[
            (Fraction(y - days_together), "You subtracted the days worked from B's solo time. A also did part of the work, so B has less left than that."),
            (Fraction(t - days_together), "You found the days left if BOTH kept working. After A leaves, B works alone and is slower."),
            (Fraction(y * (x - days_together), x), "You counted only A's work as done in those days. B was working too, so more of the job was finished."),
        ],
    )


def _wages(rng: random.Random, d: Difficulty) -> Draft:
    a, b, m, x, y, t = _family(rng, d)
    w = (a + b) * rng.randrange(20, 201, 10)
    answer = Fraction(w * a, a + b)
    return Draft(
        params={"x": x, "y": y, "w": w},
        text=f"A can do a piece of work in {x} days and B in {y} days. They work together and are paid "
             f"Rs {w} in total. How much does A receive?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Wages are shared in proportion to the work done, which is proportional to each person's daily work rate.",
                         expression=f"A : B = 1/{x} : 1/{y}"),
            SolutionStep(description="Simplify the ratio (the person who takes fewer days does more work).",
                         expression=f"A : B = {y} : {x} = {a} : {b}"),
            SolutionStep(description="A's share is A's parts out of all the parts.",
                         expression=f"{w} × {a}/({a} + {b})", result=_show(answer)),
        ],
        traps=[
            (Fraction(w * b, a + b), "You gave A the share that belongs to B. Wages follow work done, which is the INVERSE of days taken."),
            (Fraction(w, 2), "You split the amount equally. They work at different speeds, so they did different amounts of work."),
            (Fraction(w * a, b), f"You used the ratio {a}:{b} as the fraction {a}/{b} of the total. The whole is {a} + {b} parts."),
        ],
    )


def _pipes(rng: random.Random, d: Difficulty) -> Draft:
    a, b, m, x, y, t = _family(rng, d)
    e, q = (x, y) if rng.random() < 0.5 else (y, x)   # outlet time, and the net filling time
    f = t                                             # inlet time (1/t - 1/e = 1/q exactly)
    answer = Fraction(q)
    return Draft(
        params={"f": f, "e": e},
        text=f"A pipe can fill an empty tank in {f} hours, and a drain can empty the full tank in {e} hours. "
             f"If both are opened together, in how many hours will the empty tank be filled?",
        unit="hours",
        answer=answer,
        steps=[
            SolutionStep(description="Find the part of the tank the pipe fills and the drain empties in one hour.",
                         expression=f"Pipe: 1/{f},  Drain: 1/{e}"),
            SolutionStep(description="The drain works against the pipe, so subtract the rates.",
                         expression=f"1/{f} − 1/{e} = {e - f}/{f * e}"),
            SolutionStep(description="Take the reciprocal to get the hours needed.",
                         expression=f"{f * e}/{e - f}", result=_show(answer)),
        ],
        traps=[
            (Fraction(f * e, f + e), "You added the rates as if both pipes were filling. The drain works against the inlet, so subtract."),
            (Fraction(e - f), "You subtracted the times directly. Subtract the RATES (1/time), then take the reciprocal."),
            (Fraction(f + e), "You added the two times. Always combine work rates (1/time), never the times."),
        ],
    )


TW_GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "tw_together": _together,
    "tw_alone": _alone,
    "tw_leaving": _leaving,
    "tw_wages": _wages,
    "tw_pipes": _pipes,
}