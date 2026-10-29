"""Question validator. Uses only the independent solver, never the generator."""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from app.domain.models import Question
from app.engine.solver import solve

# order in which params appear as numbers in the question text
TEXT_PARAM_ORDER: dict[str, list[str]] = {
    "percent_of_number": ["percent", "base"],
    "what_percent": ["x", "y"],
    "percent_change": ["old", "new"],
    "successive_change": ["p1", "p2"],
    "find_original": ["x", "p"],
    "discount_price": ["price", "discount"],
}

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_CHANGE_WORDS = re.compile(r"\b(increased|decreased)\b")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_question(q: Question) -> ValidationResult:
    errors: list[str] = []
    answer = q.answer.to_fraction()

    # 1) independent solver must agree with the stored answer
    try:
        solved = solve(q.subtype, q.params)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        errors.append(f"solver failed: {exc!r}")
    else:
        if solved != answer:
            errors.append(f"solver says {solved}, question stores {answer}")

    # 2) options: exactly one correct, at correct_index, shown exactly
    parsed: list[Fraction | None] = []
    for opt in q.options:
        try:
            parsed.append(Fraction(Decimal(opt)))
        except (InvalidOperation, ValueError):
            errors.append(f"option {opt!r} is not a number")
            parsed.append(None)
    matches = [i for i, v in enumerate(parsed) if v == answer]
    if matches != [q.correct_index]:
        errors.append(f"correct option positions {matches}, expected [{q.correct_index}]")
    if q.options[q.correct_index] != q.answer.display():
        errors.append("correct option text differs from the displayed answer")

    # 3) numbers in the text must match params
    order = TEXT_PARAM_ORDER.get(q.subtype)
    if order is None:
        errors.append(f"no text rules for subtype {q.subtype!r}")
    else:
        try:
            expected = [str(q.params[k]) for k in order]
        except KeyError as exc:
            errors.append(f"missing param {exc}")
        else:
            found = _NUMBER.findall(q.text)
            if found != expected:
                errors.append(f"text numbers {found} do not match params {expected}")

    # 4) direction words must match params
    if q.subtype == "percent_change":
        d = q.params.get("direction")
        flags = ("increase" in q.text, "decrease" in q.text)
        if (d, flags) not in {("increase", (True, False)), ("decrease", (False, True))}:
            errors.append("direction word in text does not match params")
    if q.subtype == "successive_change":
        expected_words = [f"{q.params.get('dir1')}d", f"{q.params.get('dir2')}d"]
        if _CHANGE_WORDS.findall(q.text) != expected_words:
            errors.append("increase/decrease words in text do not match params")

    # 5) steps must exist and end on the answer
    if not q.steps:
        errors.append("no solution steps")
    else:
        if any(not s.description.strip() for s in q.steps):
            errors.append("a solution step has an empty description")
        if q.steps[-1].result != q.answer.display():
            errors.append("last step result does not match the answer")

    # 6) every wrong option must have a note; the correct one must not
    wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
    if set(q.distractor_notes) != wrong:
        errors.append("distractor_notes do not match the wrong options")
    elif any(not n.strip() for n in q.distractor_notes.values()):
        errors.append("a distractor note is empty")

    return ValidationResult(errors)


TEXT_PARAM_ORDER.update(
    {
        "ratio_share": ["total", "a", "b"],
        "ratio_missing_term": ["a", "b", "x"],
        "proportion": ["a", "b", "c"],
        "ratio_difference": ["a", "b", "d"],
        "ratio_chain": ["p", "q", "r", "s", "x"],
    }
)

TEXT_PARAM_ORDER.update(
    {
        "pl_profit_percent": ["cp", "sp"],
        "pl_loss_percent": ["cp", "sp"],
        "pl_selling_price": ["cp", "p"],
        "pl_cost_price": ["sp", "l"],
        "pl_markup_discount": ["m", "d"],
        "pl_two_articles": ["p", "p"],
    }
)

TEXT_PARAM_ORDER.update(
    {
        "tw_together": ["x", "y"],
        "tw_alone": ["t", "x"],
        "tw_leaving": ["x", "y", "d"],
        "tw_wages": ["x", "y", "w"],
        "tw_pipes": ["f", "e"],
    }
)

TEXT_PARAM_ORDER.update(
    {
        "avg_new_member": ["n", "a", "b"],
        "avg_replace": ["n", "a", "p", "q"],
        "avg_combined": ["n1", "m1", "n2", "m2"],
        "avg_speed": ["x", "y"],
        "mix_quantity": ["y", "q", "x", "z"],
        "mix_replace": ["v", "a"],
    }
)

TEXT_PARAM_ORDER.update(
    {
        "int_si": ["p", "t", "r"],
        "int_si_rate": ["p", "si", "t"],
        "int_si_time": ["p", "si", "r"],
        "int_ci_amount": ["p", "n", "r"],
        "int_ci_diff": ["p", "n", "r"],
        "int_si_multiple": ["k", "r"],
    }
)