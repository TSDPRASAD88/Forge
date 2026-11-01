import pytest

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import all_subtypes, generate_question

SUBTYPES = sorted(all_subtypes().items())


@pytest.mark.parametrize("subtype,topic", SUBTYPES)
def test_every_wrong_option_has_a_tag_and_the_right_one_has_none(subtype, topic):
    for difficulty in Difficulty:
        for seed in range(100):
            q = generate_question(ExamType.SSC_CGL, difficulty, topic=topic, subtype=subtype, seed=seed)
            wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
            assert set(q.distractor_tags) == wrong, f"{subtype}/{difficulty} seed={seed}"
            assert all(t.startswith(f"{subtype}:") for t in q.distractor_tags.values())
            assert q.options[q.correct_index] not in q.distractor_tags


@pytest.mark.parametrize("subtype,topic", SUBTYPES)
def test_most_questions_have_a_real_trap(subtype, topic):
    for difficulty in Difficulty:
        without = 0
        for seed in range(100):
            q = generate_question(ExamType.SSC_CGL, difficulty, topic=topic, subtype=subtype, seed=seed)
            if all(t.endswith(":filler") for t in q.distractor_tags.values()):
                without += 1
        assert without <= 10, f"{subtype}/{difficulty}: {without}% of questions have no real trap"