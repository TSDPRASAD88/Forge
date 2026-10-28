import pytest

from app.domain.enums import Difficulty, ExamType
from app.domain.models import ExactValue
from app.engine.generator import generate_question
from app.engine.validator import validate_question


@pytest.fixture
def q():
    return generate_question(
        ExamType.SSC_CGL, Difficulty.EASY, subtype="percent_of_number", seed=1
    )


def test_good_question_passes(q):
    assert validate_question(q).ok


def test_wrong_stored_answer_is_caught(q):
    bad = q.model_copy(update={"answer": ExactValue(numerator=999999)})
    assert not validate_question(bad).ok


def test_wrong_correct_index_is_caught(q):
    bad = q.model_copy(update={"correct_index": (q.correct_index + 1) % 4})
    assert not validate_question(bad).ok


def test_text_with_extra_number_is_caught(q):
    bad = q.model_copy(update={"text": q.text + " 123"})
    assert not validate_question(bad).ok


def test_tampered_params_are_caught(q):
    bad = q.model_copy(update={"params": {**q.params, "base": q.params["base"] + 10}})
    assert not validate_question(bad).ok


def test_bad_final_step_is_caught(q):
    steps = [*q.steps[:-1], q.steps[-1].model_copy(update={"result": "bogus"})]
    bad = q.model_copy(update={"steps": steps})
    assert not validate_question(bad).ok


def test_missing_note_is_caught(q):
    bad = q.model_copy(update={"distractor_notes": {}})
    assert not validate_question(bad).ok