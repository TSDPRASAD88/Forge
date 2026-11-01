from app.domain.enums import Difficulty, ExamType
from app.engine.validator import validate_question
from app.services.practice import build_questions, fingerprint


def _prints(qs):
    return {fingerprint(q.subtype, q.params) for q in qs}


def test_tiny_question_space_still_builds():
    # int_si_multiple at easy has only a handful of possible questions, so repeats must be allowed
    qs = build_questions(ExamType.SSC_CGL, 12, Difficulty.EASY, subtype="int_si_multiple")
    assert len(qs) == 12
    assert all(validate_question(q).ok for q in qs)


def test_recent_questions_are_avoided_when_possible():
    first = build_questions(ExamType.SSC_CGL, 5, Difficulty.EASY, subtype="percent_of_number")
    second = build_questions(
        ExamType.SSC_CGL, 5, Difficulty.EASY, subtype="percent_of_number", avoid=_prints(first)
    )
    assert not _prints(first) & _prints(second)


def test_no_duplicate_numbers_within_a_session():
    qs = build_questions(ExamType.SSC_CGL, 20, Difficulty.MEDIUM, subtype="percent_of_number")
    assert len(_prints(qs)) == 20

def test_weights_choose_the_subtype_and_difficulty():
    qs = build_questions(ExamType.SSC_CGL, 6, weights={("percent_of_number", Difficulty.EASY): 1.0})
    assert {(q.subtype, q.difficulty) for q in qs} == {("percent_of_number", Difficulty.EASY)}


def test_weights_without_a_difficulty_use_the_given_one():
    qs = build_questions(ExamType.SSC_CGL, 6, Difficulty.HARD, weights={("ratio_chain", None): 1.0})
    assert {(q.subtype, q.difficulty) for q in qs} == {("ratio_chain", Difficulty.HARD)}