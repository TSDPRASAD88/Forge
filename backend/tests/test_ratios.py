from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from app.domain.enums import Difficulty, ExamType, Topic
from app.engine.generator import GENERATORS, generate_question
from app.engine.ratios import RATIO_GENERATORS
from app.engine.solver import solve
from app.engine.validator import validate_question

getcontext().prec = 50

CASES = [
    ("ratio_share", {"total": 4500, "a": 2, "b": 3}, Fraction(1800)),
    ("ratio_missing_term", {"a": 3, "b": 5, "x": 36}, Fraction(60)),
    ("proportion", {"a": 6, "b": 90, "c": 14}, Fraction(210)),
    ("ratio_difference", {"a": 7, "b": 4, "d": 51}, Fraction(119)),
    ("ratio_chain", {"p": 2, "q": 3, "r": 4, "s": 5, "x": 60}, Fraction(32)),
]


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    if subtype == "ratio_share":
        return D(p["total"]) * D(p["a"]) / D(p["a"] + p["b"])
    if subtype == "ratio_missing_term":
        return D(p["x"]) * D(p["b"]) / D(p["a"])
    if subtype == "proportion":
        return D(p["b"]) * D(p["c"]) / D(p["a"])
    if subtype == "ratio_difference":
        return D(p["d"]) * D(p["a"]) / D(p["a"] - p["b"])
    if subtype == "ratio_chain":
        return D(p["x"]) * D(p["p"]) * D(p["r"]) / D(p["q"] * p["s"])
    raise AssertionError(subtype)


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


@pytest.mark.parametrize("subtype", sorted(RATIO_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_ratio_subtype_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.RATIOS, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(RATIO_GENERATORS))
def test_ratio_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, topic=Topic.RATIOS, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


@pytest.mark.parametrize("subtype", sorted(RATIO_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_ratio_wrong_options_have_notes(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.RATIOS, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())


def test_topic_only_gives_that_topics_subtypes():
    seen = set()
    for seed in range(600):
        q = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, topic=Topic.RATIOS, seed=seed)
        assert q.topic == Topic.RATIOS
        assert validate_question(q).ok, q.text
        seen.add(q.subtype)
    assert seen == set(RATIO_GENERATORS)
    assert not seen & set(GENERATORS)


def test_subtype_from_another_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, topic=Topic.RATIOS, subtype="percent_of_number")