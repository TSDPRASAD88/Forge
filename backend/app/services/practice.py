import random

from app.domain.enums import Difficulty, ExamType, Topic
from app.domain.models import Question
from app.domain.profiles import get_profile
from app.engine.generator import all_subtypes, generate_question
from app.engine.validator import validate_question

MAX_ATTEMPTS_PER_QUESTION = 50


class QuestionBuildError(RuntimeError):
    pass


def fingerprint(subtype: str, params: dict) -> tuple:
    """Identity of a question's numbers, independent of how it is worded."""
    return (subtype, tuple(sorted(params.items())))


def pick_difficulty(exam: ExamType, rng: random.Random) -> Difficulty:
    mix = get_profile(exam).difficulty_mix
    return rng.choices(list(mix), weights=list(mix.values()))[0]


def build_questions(
    exam: ExamType,
    count: int,
    difficulty: Difficulty | None = None,
    subtype: str | None = None,
    topic: Topic | None = None,
    avoid: set[tuple] | None = None,
    weights: dict[tuple[str, Difficulty | None], float] | None = None,
) -> list[Question]:
    """Generate `count` validated questions.

    With `weights`, every slot first picks a (subtype, difficulty) pair at random, weighted.
    Preference order inside a slot: numbers never seen, then seen in a recent session (`avoid`),
    then a repeat from this session. The fallbacks keep tiny question pools working.
    """
    rng = random.SystemRandom()
    avoid = avoid or set()
    owners = all_subtypes()
    profile_topics = get_profile(exam).topics
    if subtype is not None:
        owner = owners.get(subtype)
        if owner is None:
            raise ValueError(f"unknown subtype: {subtype}")
        topic = owner                      # a subtype belongs to exactly one topic

    questions: list[Question] = []
    seen: set[tuple] = set()

    for _ in range(count):
        slot_subtype, slot_topic, slot_difficulty = subtype, topic, difficulty
        if weights:
            slot_subtype, key_difficulty = rng.choices(list(weights), weights=list(weights.values()))[0]
            slot_topic = owners[slot_subtype]
            slot_difficulty = key_difficulty or difficulty

        fresh: Question | None = None
        recent: Question | None = None
        repeat: Question | None = None
        for _attempt in range(MAX_ATTEMPTS_PER_QUESTION):
            q = generate_question(
                exam,
                slot_difficulty or pick_difficulty(exam, rng),
                topic=slot_topic or rng.choice(profile_topics),
                subtype=slot_subtype,
            )
            if not validate_question(q).ok:
                continue
            fp = fingerprint(q.subtype, q.params)
            if fp in seen:
                repeat = repeat or q
            elif fp in avoid:
                recent = recent or q
            else:
                fresh = q
                break
        chosen = fresh or recent or repeat
        if chosen is None:
            raise QuestionBuildError("could not build a valid question")
        seen.add(fingerprint(chosen.subtype, chosen.params))
        questions.append(chosen)
    return questions