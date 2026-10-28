import random
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd
from typing import Callable

from app.domain.enums import Difficulty, ExamType, Topic
from app.domain.models import ExactValue, Question, SolutionStep
from app.domain.profiles import get_profile

MAX_TRIES = 200
DIRECTIONS = ["increase", "decrease"]
# bases where 100/base has a denominator dividing 100 (so answers display exactly)
CLEAN_BASES = [8, 16, 20, 25, 40, 50, 80, 125, 200, 250, 400, 500, 1000]


class GenerationError(RuntimeError):
    pass


@dataclass
class Draft:
    params: dict[str, int | str]
    text: str
    unit: str
    answer: Fraction
    steps: list[SolutionStep]
    traps: list[Fraction] = field(default_factory=list)  # common wrong answers
    allow_negative: bool = False


def _show(f: Fraction) -> str:
    return ExactValue.from_fraction(f).display()


def _is_clean(f: Fraction) -> bool:
    """True if f is exactly representable with at most 2 decimals."""
    return (f * 100).denominator == 1


def _unit(p: int) -> int:
    """Smallest n such that p% of any multiple of n is a whole number."""
    return 100 // gcd(p, 100)


# ---------- subtype generators ----------

def _percent_of_number(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        p = rng.choice([5, 10, 20, 25, 50])
        b = _unit(p) * rng.randint(2, 20)
    elif d == Difficulty.MEDIUM:
        p = rng.randint(2, 98)
        b = rng.randrange(50, 1001, 10)
    else:
        p = rng.randint(3, 149)
        b = rng.randrange(40, 2001, 20)
    answer = Fraction(p * b, 100)
    return Draft(
        params={"percent": p, "base": b},
        text=f"What is {p}% of {b}?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Write the percentage as a fraction of 100.",
                         expression=f"{p}% = {p}/100"),
            SolutionStep(description="Multiply the fraction by the number.",
                         expression=f"({p}/100) × {b}", result=_show(answer)),
        ],
        traps=[answer * 10, answer / 10, Fraction(b) - answer, Fraction(b) + answer],
    )


def _what_percent(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.HARD:
        y = rng.choice(CLEAN_BASES)
        x = rng.randint(1, 2 * y)
        answer = Fraction(100 * x, y)
    else:
        a = rng.choice([10, 20, 25, 50, 75]) if d == Difficulty.EASY else rng.randint(2, 98)
        y = _unit(a) * (rng.randint(2, 20) if d == Difficulty.EASY else rng.randint(1, 10))
        x = a * y // 100
        answer = Fraction(a)  # chosen first; solver must re-derive it from x and y
    return Draft(
        params={"x": x, "y": y},
        text=f"{x} is what percent of {y}?",
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Write the part as a fraction of the whole.",
                         expression=f"{x}/{y}"),
            SolutionStep(description="Multiply by 100 to convert to a percentage.",
                         expression=f"({x}/{y}) × 100", result=_show(answer)),
        ],
        traps=[Fraction(100 * y, x), 100 - answer, Fraction(100 * x, x + y)],
    )


def _percent_change(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.HARD:
        old = rng.choice(CLEAN_BASES)
        new = old
        while new == old:
            new = rng.randint(max(1, old // 2), old * 2)
        direction = "increase" if new > old else "decrease"
        answer = Fraction(abs(new - old) * 100, old)
    else:
        direction = rng.choice(DIRECTIONS)
        a = rng.choice([10, 20, 25, 50]) if d == Difficulty.EASY else rng.randrange(5, 96, 5)
        old = _unit(a) * rng.randint(2, 20)
        change = a * old // 100
        new = old + change if direction == "increase" else old - change
        answer = Fraction(a)
    diff = abs(new - old)
    diff_expr = f"{new} − {old} = {diff}" if direction == "increase" else f"{old} − {new} = {diff}"
    return Draft(
        params={"old": old, "new": new, "direction": direction},
        text=f"The value of an item changes from {old} to {new}. What is the percentage {direction}?",
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Find the absolute change.", expression=diff_expr),
            SolutionStep(description="Divide by the ORIGINAL value and multiply by 100.",
                         expression=f"({diff}/{old}) × 100", result=_show(answer)),
        ],
        traps=[Fraction(diff * 100, new), Fraction(diff * 100, old + new), Fraction(diff)],
    )


def _successive_change(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        pool = [10, 20, 25, 50]
    elif d == Difficulty.MEDIUM:
        pool = list(range(5, 51, 5))
    else:
        pool = list(range(2, 76))
    p1, p2 = rng.choice(pool), rng.choice(pool)
    dir1, dir2 = rng.choice(DIRECTIONS), rng.choice(DIRECTIONS)
    s1 = 1 if dir1 == "increase" else -1
    s2 = 1 if dir2 == "increase" else -1
    # shortcut formula a + b + ab/100 (the solver uses multipliers instead)
    answer = Fraction(s1 * p1 + s2 * p2) + Fraction(s1 * s2 * p1 * p2, 100)
    n1, n2 = 100 + s1 * p1, 100 + s2 * p2
    return Draft(
        params={"p1": p1, "p2": p2, "dir1": dir1, "dir2": dir2},
        text=(f"A price is {dir1}d by {p1}% and then {dir2}d by {p2}%. "
              f"What is the net percentage change? (Use a negative value for a net decrease.)"),
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Convert the first change into a multiplier.",
                         expression=f"{n1}/100"),
            SolutionStep(description="Convert the second change into a multiplier.",
                         expression=f"{n2}/100"),
            SolutionStep(description="Multiply the multipliers to get the combined multiplier.",
                         expression=f"{n1} × {n2} / 10000 = {n1 * n2}/10000"),
            SolutionStep(description="Subtract 1 and convert to a percentage.",
                         expression=f"({n1 * n2}/10000 − 1) × 100", result=_show(answer)),
        ],
        traps=[Fraction(s1 * p1 + s2 * p2), -answer,
               Fraction(s1 * p1 + s2 * p2) - Fraction(s1 * s2 * p1 * p2, 100)],
        allow_negative=True,
    )


def _find_original(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        p = rng.choice([10, 20, 25, 50])
        n = _unit(p) * rng.randint(2, 20)
    elif d == Difficulty.MEDIUM:
        p = rng.randint(2, 98)
        n = _unit(p) * rng.randint(1, 10)
    else:
        p = rng.randrange(105, 251, 5)
        n = _unit(p) * rng.randint(5, 50)
    x = p * n // 100
    answer = Fraction(n)  # chosen first; solver re-derives it from x and p
    traps = [Fraction(x * p, 100), x + Fraction(x * p, 100), Fraction(x * 100, 100 + p)]
    if p != 100:
        traps.append(Fraction(x * 100, 100 - p))
    return Draft(
        params={"x": x, "p": p},
        text=f"{x} is {p}% of what number?",
        unit="",
        answer=answer,
        steps=[
            SolutionStep(description="Let the number be N and write the condition.",
                         expression=f"({p}/100) × N = {x}"),
            SolutionStep(description="Solve for N.",
                         expression=f"N = {x} × 100 / {p}", result=_show(answer)),
        ],
        traps=traps,
    )


def _discount_price(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        dsc = rng.choice([10, 20, 25, 50])
        price = rng.randrange(100, 2001, 100)
    elif d == Difficulty.MEDIUM:
        dsc = rng.randrange(5, 46, 5)
        price = rng.randrange(200, 5001, 20)
    else:
        dsc = rng.randint(1, 75)
        price = rng.randrange(250, 9001, 20)
    amount = Fraction(price * dsc, 100)
    answer = price - amount
    return Draft(
        params={"price": price, "discount": dsc},
        text=f"An article is marked at Rs {price}. A discount of {dsc}% is given on it. What is the selling price?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Find the discount amount.",
                         expression=f"{price} × {dsc}/100 = {_show(amount)}"),
            SolutionStep(description="Subtract the discount from the marked price.",
                         expression=f"{price} − {_show(amount)}", result=_show(answer)),
        ],
        traps=[amount, Fraction(price * (100 + dsc), 100), Fraction(price - dsc)],
    )


GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "percent_of_number": _percent_of_number,
    "what_percent": _what_percent,
    "percent_change": _percent_change,
    "successive_change": _successive_change,
    "find_original": _find_original,
    "discount_price": _discount_price,
}


# ---------- options ----------

def _build_options(
    rng: random.Random, answer: Fraction, traps: list[Fraction], allow_negative: bool
) -> tuple[list[str], int]:
    seen = {_show(answer)}
    distractors: list[Fraction] = []

    def consider(c: Fraction) -> None:
        if len(distractors) >= 3 or not _is_clean(c):
            return
        if c < 0 and not allow_negative:
            return
        s = _show(c)
        if s in seen:
            return
        seen.add(s)
        distractors.append(c)

    shuffled = list(traps)
    rng.shuffle(shuffled)
    for t in shuffled:                       # 1) realistic mistakes first
        consider(t)
    for q in (10, -10, 20, -20, 5, -5):      # 2) nearby values
        consider(answer * Fraction(100 + q, 100))
    for k in range(1, 100):                  # 3) guaranteed fallback
        consider(answer + k)
        consider(answer - k)

    choices = [answer, *distractors]
    rng.shuffle(choices)
    return [_show(c) for c in choices], choices.index(answer)


# ---------- public API ----------

def generate_question(
    exam: ExamType,
    difficulty: Difficulty,
    topic: Topic = Topic.PERCENTAGES,
    subtype: str | None = None,
    seed: int | None = None,
) -> Question:
    profile = get_profile(exam)
    if topic not in profile.topics:
        raise ValueError(f"{topic} is not part of {exam}")
    if subtype is not None and subtype not in GENERATORS:
        raise ValueError(f"unknown subtype: {subtype}")

    if seed is None:
        seed = random.SystemRandom().randrange(2**32)
    rng = random.Random(seed)
    name = subtype or rng.choice(sorted(GENERATORS))

    for _ in range(MAX_TRIES):
        draft = GENERATORS[name](rng, difficulty)
        if _is_clean(draft.answer):
            break
    else:
        raise GenerationError(f"could not generate a clean {name} question")

    options, idx = _build_options(rng, draft.answer, draft.traps, draft.allow_negative)
    return Question(
        exam=exam,
        topic=topic,
        subtype=name,
        difficulty=difficulty,
        text=draft.text,
        unit=draft.unit,
        options=options,
        correct_index=idx,
        answer=ExactValue.from_fraction(draft.answer),
        params=draft.params,
        steps=draft.steps,
        seed=seed,
    )