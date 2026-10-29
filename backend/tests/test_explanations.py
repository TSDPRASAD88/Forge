import pytest

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import GENERATORS, generate_question


@pytest.mark.parametrize("subtype", sorted(GENERATORS))
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_every_wrong_option_has_a_note(subtype, difficulty):
    for seed in range(200):
        q = generate_question(ExamType.SSC_CGL, difficulty, subtype=subtype, seed=seed)
        wrong = {o for i, o in enumerate(q.options) if i != q.correct_index}
        assert set(q.distractor_notes) == wrong, f"{subtype}/{difficulty} seed={seed}"
        assert all(n.strip() for n in q.distractor_notes.values())