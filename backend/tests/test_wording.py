import random

import pytest

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import _generators_for, all_subtypes, generate_question
from app.engine.validator import validate_question
from app.engine.wording import WORDINGS

SUBTYPES = sorted(all_subtypes().items())


def test_every_subtype_has_wordings():
    assert set(WORDINGS) == set(all_subtypes())
    assert all(len(v) >= 2 for v in WORDINGS.values())


@pytest.mark.parametrize("subtype,topic", SUBTYPES)
def test_first_template_is_the_original_wording(subtype, topic):
    gen = _generators_for(topic)[subtype]
    for difficulty in Difficulty:
        for seed in range(20):
            draft = gen(random.Random(seed), difficulty)
            assert WORDINGS[subtype][0].format(**draft.params) == draft.text


@pytest.mark.parametrize("subtype,topic", SUBTYPES)
def test_every_template_passes_the_validator(subtype, topic):
    for difficulty in Difficulty:
        for seed in range(20):
            q = generate_question(ExamType.SSC_CGL, difficulty, topic=topic, subtype=subtype, seed=seed)
            for template in WORDINGS[subtype]:
                variant = q.model_copy(update={"text": template.format(**q.params)})
                result = validate_question(variant)
                assert result.ok, f"{subtype}: {template!r} -> {result.errors}"