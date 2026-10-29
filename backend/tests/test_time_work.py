from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from app.domain.enums import Difficulty, ExamType, Topic
from app.engine.generator import GENERATORS, generate_question
from app.engine.solver import solve
from app.engine.time_work import TW_GENERATORS
from app.engine.validator import validate_question

getcontext().prec = 50

CASES = [
    ("tw_together", {"x": 15, "y": 10}, Fraction(6)),
    ("tw_alone", {"t": 6, "x": 15}, Fraction(10)),
    ("tw_leaving", {"x": 15, "y": 10, "d": 3}, Fraction(5)),
    ("tw_wages", {"x": 15, "y": 10, "w": 500}, Fraction(200)),
    ("tw_pipes", {"f": 6, "e": 10}, Fraction(15)),
]


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    one = D(1)
    if subtype == "tw_together":
        return one / (one / D(p["x"]) + one / D(p["y"]))
    if subtype == "tw_alone":
        return one / (one / D(p["t"]) - one / D(p["x"]))
    if subtype == "tw_leaving":
        return (one - D(p["d"]) * (one / D(p["x"]) + one / D(p["y"]))) * D(p["y"])
    if subtype == "tw_wages":
        return D(p["w"]) * D(p["y"]) / D(p["x"] + p["y"])       # inverse-days shortcut
    if subtype == "tw_pipes":
        return D(p["f"]) * D(p["e"]) / D(p["e"] - p["f"])
    raise AssertionError(subtype)


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


@pytest.mark.parametrize("subtype", sorted(TW_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_tw_subtype_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.TIME_WORK, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(TW_GENERATORS))
def test_tw_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, topic=Topic.TIME_WORK, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


@pytest.mark.parametrize("subtype", sorted(TW_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_tw_wrong_options_have_notes(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.TIME_WORK, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())


def test_topic_only_gives_that_topics_subtypes():
    seen = set()
    for seed in range(800):
        q = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, topic=Topic.TIME_WORK, seed=seed)
        assert q.topic == Topic.TIME_WORK
        assert validate_question(q).ok, q.text
        seen.add(q.subtype)
    assert seen == set(TW_GENERATORS)
    assert not seen & set(GENERATORS)


def test_subtype_from_another_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, topic=Topic.TIME_WORK, subtype="ratio_chain")