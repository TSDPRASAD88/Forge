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
GENERIC_NOTE = "This value is close to the answer but not correct. Recheck each calculation step."


class GenerationError(RuntimeError):
    pass


@dataclass
class Draft:
    params: dict[str, int | str]
    text: str
    unit: str
    answer: Fraction
    steps: list[SolutionStep]
    traps: list[tuple[Fraction, str]] = field(default_factory=list)  # (wrong value, why it's wrong)
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
        traps=[
            (answer * 10, "The decimal point slipped: this is 10 times too big. Remember % means divide by 100."),
            (answer / 10, "The decimal point slipped: this is 10 times too small. Remember % means divide by 100."),
            (Fraction(b) - answer, "You subtracted the percentage from the number instead of just finding the percentage."),
            (Fraction(b) + answer, "You added the percentage to the number instead of just finding the percentage."),
        ],
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
        traps=[
            (Fraction(100 * y, x), "You flipped the fraction. Divide the part by the whole, not the whole by the part."),
            (100 - answer, "You found the remaining percentage (100 minus the answer) instead of the percentage asked."),
            (Fraction(100 * x, x + y), "You divided by the sum of both numbers. The whole is the number after 'of'."),
        ],
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
        traps=[
            (Fraction(diff * 100, new), "You divided by the NEW value. Percentage change is always measured against the ORIGINAL value."),
            (Fraction(diff * 100, old + new), "You divided by the sum of old and new. Divide by the original value only."),
            (Fraction(diff), "You gave the raw change in value and forgot to convert it into a percentage."),
        ],
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
        traps=[
            (Fraction(s1 * p1 + s2 * p2), "You only added the two percentages. The second change applies to the already-changed price, so use multipliers."),
            (-answer, "The sign is flipped. Check whether the combined multiplier is above or below 1."),
            (Fraction(s1 * p1 + s2 * p2) - Fraction(s1 * s2 * p1 * p2, 100),
             "You got the sign of the combined (ab/100) term wrong. Multiplying the two multipliers avoids this."),
        ],
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
    traps = [
        (Fraction(x * p, 100), f"You took {p}% of {x}. You need the number whose {p}% is {x}, so divide instead."),
        (x + Fraction(x * p, 100), f"You added {p}% of {x} to {x}. The given value is the part, not the original."),
        (Fraction(x * 100, 100 + p), f"You treated {x} as the result of an increase by {p}%. Here {x} is {p}% OF the original."),
    ]
    if p != 100:
        traps.append(
            (Fraction(x * 100, 100 - p), f"You treated {x} as the result of a decrease by {p}%. Here {x} is {p}% OF the original.")
        )
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
        traps=[
            (amount, "You stopped at the discount amount. The selling price is the marked price minus the discount."),
            (Fraction(price * (100 + dsc), 100), "You added the discount instead of subtracting it."),
            (Fraction(price - dsc), f"You subtracted {dsc} rupees. The discount is {dsc}% of the price, not {dsc} rupees."),
        ],
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
    rng: random.Random,
    answer: Fraction,
    traps: list[tuple[Fraction, str]],
    allow_negative: bool,
) -> tuple[list[str], int, dict[str, str]]:
    seen = {_show(answer)}
    distractors: list[tuple[Fraction, str]] = []

    def consider(c: Fraction, note: str) -> None:
        if len(distractors) >= 3 or not _is_clean(c):
            return
        if c < 0 and not allow_negative:
            return
        s = _show(c)
        if s in seen:
            return
        seen.add(s)
        distractors.append((c, note))

    shuffled = list(traps)
    rng.shuffle(shuffled)
    for value, note in shuffled:                 # 1) realistic mistakes first
        consider(value, note)
    for q in (10, -10, 20, -20, 5, -5):          # 2) nearby values
        consider(answer * Fraction(100 + q, 100), GENERIC_NOTE)
    for k in range(1, 100):                      # 3) guaranteed fallback
        consider(answer + k, GENERIC_NOTE)
        consider(answer - k, GENERIC_NOTE)

    choices = [answer, *(c for c, _ in distractors)]
    rng.shuffle(choices)
    notes = {_show(c): note for c, note in distractors}
    return [_show(c) for c in choices], choices.index(answer), notes


# ---------- public API ----------

def _generators_for(topic: Topic) -> dict[str, Callable[[random.Random, Difficulty], Draft]]:
    if topic == Topic.PERCENTAGES:
        return GENERATORS
    if topic == Topic.RATIOS:
        from app.engine.ratios import RATIO_GENERATORS  # imported here to avoid a circular import

        return RATIO_GENERATORS
    raise ValueError(f"no generators for topic {topic}")


def all_subtypes() -> dict[str, Topic]:
    """Every subtype name mapped to the topic it belongs to."""
    return {
        name: topic
        for topic in (Topic.PERCENTAGES, Topic.RATIOS)
        for name in _generators_for(topic)
    }


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
    registry = _generators_for(topic)
    if subtype is not None and subtype not in registry:
        raise ValueError(f"unknown subtype for {topic}: {subtype}")

    if seed is None:
        seed = random.SystemRandom().randrange(2**32)
    rng = random.Random(seed)
    name = subtype or rng.choice(sorted(registry))

    for _ in range(MAX_TRIES):
        draft = registry[name](rng, difficulty)
        if _is_clean(draft.answer):
            break
    else:
        raise GenerationError(f"could not generate a clean {name} question")

    options, idx, notes = _build_options(rng, draft.answer, draft.traps, draft.allow_negative)
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
        distractor_notes=notes,
    )