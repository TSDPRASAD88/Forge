from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from app.domain.enums import Difficulty, ExamType, Topic
from app.engine.generator import GENERATORS, generate_question
from app.engine.interest import INT_GENERATORS
from app.engine.solver import solve
from app.engine.validator import validate_question

getcontext().prec = 50

CASES = [
    ("int_si", {"p": 5000, "r": 8, "t": 3}, Fraction(1200)),
    ("int_si_rate", {"p": 5000, "si": 1200, "t": 3}, Fraction(8)),
    ("int_si_time", {"p": 5000, "si": 1200, "r": 8}, Fraction(3)),
    ("int_ci_amount", {"p": 10000, "r": 10, "n": 2}, Fraction(12100)),
    ("int_ci_diff", {"p": 10000, "r": 10, "n": 2}, Fraction(100)),
    ("int_si_multiple", {"k": 2, "r": 10}, Fraction(10)),
    ("int_si_multiple", {"k": 3, "r": 8}, Fraction(25)),
]


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    if subtype == "int_si":
        return D(p["p"]) * D(p["r"]) * D(p["t"]) / 100
    if subtype == "int_si_rate":
        return D(p["si"]) * 100 / (D(p["p"]) * D(p["t"]))
    if subtype == "int_si_time":
        return D(p["si"]) * 100 / (D(p["p"]) * D(p["r"]))
    if subtype == "int_ci_amount":
        return D(p["p"]) * (1 + D(p["r"]) / 100) ** p["n"]
    if subtype == "int_ci_diff":
        amount = D(p["p"]) * (1 + D(p["r"]) / 100) ** p["n"]
        return amount - D(p["p"]) - D(p["p"]) * D(p["r"]) * p["n"] / 100
    if subtype == "int_si_multiple":
        return D(100) * (D(p["k"]) - 1) / D(p["r"])
    raise AssertionError(subtype)


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


@pytest.mark.parametrize("subtype", sorted(INT_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_int_subtype_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.INTEREST, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(INT_GENERATORS))
def test_int_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, topic=Topic.INTEREST, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


@pytest.mark.parametrize("subtype", sorted(INT_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_int_wrong_options_have_notes(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.INTEREST, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())


def test_topic_only_gives_that_topics_subtypes():
    seen = set()
    for seed in range(800):
        q = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, topic=Topic.INTEREST, seed=seed)
        assert q.topic == Topic.INTEREST
        assert validate_question(q).ok, q.text
        seen.add(q.subtype)
    assert seen == set(INT_GENERATORS)
    assert not seen & set(GENERATORS)


def test_subtype_from_another_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, topic=Topic.INTEREST, subtype="ratio_chain")