import random

from app.domain.enums import Difficulty, ExamType, Topic
from app.domain.models import Question
from app.domain.profiles import get_profile
from app.engine.generator import all_subtypes, generate_question
from app.engine.validator import validate_question

MAX_ATTEMPTS_PER_QUESTION = 50


class QuestionBuildError(RuntimeError):
    pass


def pick_difficulty(exam: ExamType, rng: random.Random) -> Difficulty:
    mix = get_profile(exam).difficulty_mix
    return rng.choices(list(mix), weights=list(mix.values()))[0]


def build_questions(
    exam: ExamType,
    count: int,
    difficulty: Difficulty | None = None,
    subtype: str | None = None,
    topic: Topic | None = None,
) -> list[Question]:
    """Generate `count` questions. Every one is validated; invalid or duplicate ones are discarded."""
    rng = random.SystemRandom()
    profile_topics = get_profile(exam).topics
    if subtype is not None:
        owner = all_subtypes().get(subtype)
        if owner is None:
            raise ValueError(f"unknown subtype: {subtype}")
        topic = owner                      # a subtype belongs to exactly one topic

    questions: list[Question] = []
    seen_texts: set[str] = set()

    for _ in range(count):
        for _attempt in range(MAX_ATTEMPTS_PER_QUESTION):
            q = generate_question(
                exam,
                difficulty or pick_difficulty(exam, rng),
                topic=topic or rng.choice(profile_topics),
                subtype=subtype,
            )
            if q.text in seen_texts or not validate_question(q).ok:
                continue
            seen_texts.add(q.text)
            questions.append(q)
            break
        else:
            raise QuestionBuildError("could not build a valid, unique question")
    return questions