from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from app.domain.enums import Difficulty, ExamType, Topic
from app.engine.generator import GENERATORS, generate_question
from app.engine.profit_loss import PL_GENERATORS
from app.engine.solver import solve
from app.engine.validator import validate_question

getcontext().prec = 50

CASES = [
    ("pl_profit_percent", {"cp": 400, "sp": 500}, Fraction(25)),
    ("pl_loss_percent", {"cp": 500, "sp": 400}, Fraction(20)),
    ("pl_selling_price", {"cp": 800, "p": 25}, Fraction(1000)),
    ("pl_cost_price", {"sp": 720, "l": 10}, Fraction(800)),
    ("pl_markup_discount", {"m": 20, "d": 10}, Fraction(8)),
    ("pl_markup_discount", {"m": 10, "d": 20}, Fraction(-12)),
    ("pl_two_articles", {"p": 10}, Fraction(1)),
]


def oracle(subtype: str, p: dict) -> Decimal:
    """A third, Decimal-based implementation used only by tests."""
    D = Decimal
    if subtype == "pl_profit_percent":
        return (D(p["sp"]) - D(p["cp"])) * 100 / D(p["cp"])
    if subtype == "pl_loss_percent":
        return (D(p["cp"]) - D(p["sp"])) * 100 / D(p["cp"])
    if subtype == "pl_selling_price":
        return D(p["cp"]) * (100 + D(p["p"])) / 100
    if subtype == "pl_cost_price":
        return D(p["sp"]) * 100 / (100 - D(p["l"]))
    if subtype == "pl_markup_discount":
        return (100 + D(p["m"])) * (100 - D(p["d"])) / 100 - 100
    if subtype == "pl_two_articles":
        pp = D(p["p"])
        cost = 100 / (100 + pp) + 100 / (100 - pp)
        return (cost - 2) / cost * 100
    raise AssertionError(subtype)


@pytest.mark.parametrize("subtype,params,expected", CASES)
def test_known_answers(subtype, params, expected):
    assert solve(subtype, params) == expected


@pytest.mark.parametrize("subtype", sorted(PL_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_pl_subtype_validates(subtype, difficulty):
    for seed in range(300):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.PROFIT_LOSS, subtype=subtype, seed=seed)
        result = validate_question(q)
        assert result.ok, f"{subtype}/{difficulty} seed={seed}: {result.errors}\n{q.text}"


@pytest.mark.parametrize("subtype", sorted(PL_GENERATORS))
def test_pl_answers_match_decimal_oracle(subtype):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.GATE_CSE, difficulty, topic=Topic.PROFIT_LOSS, subtype=subtype, seed=seed)
            stored = Decimal(q.answer.numerator) / Decimal(q.answer.denominator)
            assert abs(stored - oracle(subtype, q.params)) < Decimal("1e-30"), q.text


@pytest.mark.parametrize("subtype", sorted(PL_GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_pl_wrong_options_have_notes(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, topic=Topic.PROFIT_LOSS, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())


def test_topic_only_gives_that_topics_subtypes():
    seen = set()
    for seed in range(800):
        q = generate_question(ExamType.SSC_CGL, Difficulty.MEDIUM, topic=Topic.PROFIT_LOSS, seed=seed)
        assert q.topic == Topic.PROFIT_LOSS
        assert validate_question(q).ok, q.text
        seen.add(q.subtype)
    assert seen == set(PL_GENERATORS)
    assert not seen & set(GENERATORS)


def test_subtype_from_another_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_question(ExamType.SSC_CGL, Difficulty.EASY, topic=Topic.PROFIT_LOSS, subtype="ratio_chain")