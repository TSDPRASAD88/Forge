from decimal import Decimal, getcontext

import pytest

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import GENERATORS, generate_question
from app.engine.validator import validate_question

getcontext().prec = 50


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    sign = lambda d: 1 if d == "increase" else -1  # noqa: E731
    if subtype == "percent_of_number":
        return D(p["percent"]) / 100 * p["base"]
    if subtype == "what_percent":
        return D(p["x"]) * 100 / D(p["y"])
    if subtype == "percent_change":
        return abs(D(p["new"]) - D(p["old"])) * 100 / D(p["old"])
    if subtype == "successive_change":
        m1 = 1 + sign(p["dir1"]) * D(p["p1"]) / 100
        m2 = 1 + sign(p["dir2"]) * D(p["p2"]) / 100
        return (m1 * m2 - 1) * 100
    if subtype == "find_original":
        return D(p["x"]) * 100 / D(p["p"])
    if subtype == "discount_price":
        return D(p["price"]) * (100 - D(p["discount"])) / 100
    raise AssertionError(subtype)


def test_same_seed_same_question():
    a = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, seed=123)
    b = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, seed=123)
    assert a.model_dump(exclude={"id"}) == b.model_dump(exclude={"id"})


@pytest.mark.parametrize("subtype", sorted(GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_subtype_and_difficulty_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(GENERATORS))
def test_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


def test_mass_generation_is_always_valid():
    seen = set()
    exams, diffs = list(ExamType), list(Difficulty)
    for seed in range(3000):
        q = generate_question(exams[seed % len(exams)], diffs[seed % len(diffs)], seed=seed)
        assert validate_question(q).ok, q.text
        assert len(set(q.options)) == 4
        seen.add(q.subtype)
    assert seen == set(GENERATORS)


def test_unknown_subtype_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, subtype="nope")