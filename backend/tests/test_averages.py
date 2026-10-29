from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from app.domain.enums import Difficulty, ExamType, Topic
from app.engine.averages import AM_GENERATORS
from app.engine.generator import GENERATORS, generate_question
from app.engine.solver import solve
from app.engine.validator import validate_question

getcontext().prec = 50

CASES = [
    ("avg_new_member", {"n": 5, "a": 20, "b": 22}, Fraction(32)),
    ("avg_replace", {"n": 5, "a": 20, "p": 10, "q": 35}, Fraction(25)),
    ("avg_combined", {"n1": 20, "m1": 50, "n2": 30, "m2": 70}, Fraction(62)),
    ("avg_speed", {"x": 40, "y": 60}, Fraction(48)),
    ("mix_quantity", {"y": 60, "q": 30, "x": 40, "z": 48}, Fraction(20)),
    ("mix_replace", {"v": 100, "a": 20}, Fraction(64)),
]


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    if subtype == "avg_new_member":
        return (D(p["n"]) + 1) * D(p["b"]) - D(p["n"]) * D(p["a"])
    if subtype == "avg_replace":
        return D(p["a"]) + (D(p["q"]) - D(p["p"])) / D(p["n"])
    if subtype == "avg_combined":
        return (D(p["n1"]) * D(p["m1"]) + D(p["n2"]) * D(p["m2"])) / (D(p["n1"]) + D(p["n2"]))
    if subtype == "avg_speed":
        return D(200) / (D(100) / D(p["x"]) + D(100) / D(p["y"]))   # 100 km each way
    if subtype == "mix_quantity":
        return D(p["q"]) * (D(p["z"]) - D(p["x"])) / (D(p["y"]) - D(p["z"]))
    if subtype == "mix_replace":
        return D(p["v"]) * (1 - D(p["a"]) / D(p["v"])) ** 2
    raise AssertionError(subtype)


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


@pytest.mark.parametrize("subtype", sorted(AM_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_am_subtype_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.AVERAGES_MIXTURES, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(AM_GENERATORS))
def test_am_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, topic=Topic.AVERAGES_MIXTURES, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


@pytest.mark.parametrize("subtype", sorted(AM_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_am_wrong_options_have_notes(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.AVERAGES_MIXTURES, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())


def test_topic_only_gives_that_topics_subtypes():
    seen = set()
    for seed in range(800):
        q = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, topic=Topic.AVERAGES_MIXTURES, seed=seed)
        assert q.topic == Topic.AVERAGES_MIXTURES
        assert validate_question(q).ok, q.text
        seen.add(q.subtype)
    assert seen == set(AM_GENERATORS)
    assert not seen & set(GENERATORS)


def test_subtype_from_another_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, topic=Topic.AVERAGES_MIXTURES, subtype="ratio_chain")