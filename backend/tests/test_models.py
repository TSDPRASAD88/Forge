from fractions import Fraction

import pytest
from pydantic import ValidationError

from app.domain.enums import Difficulty, ExamType, Topic
from app.domain.models import ExactValue, Question


def make_question(**overrides):
    data = dict(
        exam=ExamType.SSC_CGL,
        topic=Topic.PERCENTAGES,
        subtype="percent_of_number",
        difficulty=Difficulty.EASY,
        text="What is 20% of 150?",
        options=["20", "25", "30", "35"],
        correct_index=2,
        answer=ExactValue(numerator=30),
        params={"percent": 20, "base": 150},
    )
    data.update(overrides)
    return Question(**data)


def test_exact_value_roundtrip():
    f = Fraction(7, 3)
    assert ExactValue.from_fraction(f).to_fraction() == f


def test_exact_value_rejects_unreduced():
    with pytest.raises(ValidationError):
        ExactValue(numerator=2, denominator=4)


def test_exact_value_display():
    assert ExactValue(numerator=30).display() == "30"
    assert ExactValue(numerator=1, denominator=3).display() == "0.33"
    assert ExactValue(numerator=5, denominator=2).display() == "2.5"


def test_valid_question():
    assert make_question().correct_index == 2


def test_rejects_duplicate_options():
    with pytest.raises(ValidationError):
        make_question(options=["20", "20", "30", "35"])


def test_rejects_wrong_option_count():
    with pytest.raises(ValidationError):
        make_question(options=["20", "25", "30"])


def test_rejects_bad_correct_index():
    with pytest.raises(ValidationError):
        make_question(correct_index=4)