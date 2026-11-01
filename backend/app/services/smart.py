"""Smart practice modes: choose WHAT to practise from the answer history."""

from collections import Counter

from app.domain.enums import Difficulty

MIN_WEIGHT = 0.1        # even strong topics keep appearing now and then
RETRY_WINDOW = 100      # how many of the newest answers count as "recent"

Weights = dict[tuple[str, Difficulty | None], float]


def weak_weights(answers: list[dict], subtypes: set[str]) -> Weights:
    """Weight every question type by how weak you are at it (answers: any order)."""
    attempted: Counter = Counter()
    correct: Counter = Counter()
    for a in answers:
        if a["subtype"] in subtypes:
            attempted[a["subtype"]] += 1
            correct[a["subtype"]] += 1 if a["correct"] else 0
    weights: Weights = {}
    for s in subtypes:
        accuracy = (correct[s] + 1) / (attempted[s] + 2)       # smoothed: no history = 50%
        weights[(s, None)] = max(MIN_WEIGHT, 1 - accuracy)
    return weights


def retry_weights(answers: list[dict], subtypes: set[str]) -> Weights:
    """Open mistakes per (subtype, difficulty). `answers` must be newest first."""
    net: Counter = Counter()
    for a in answers[:RETRY_WINDOW]:
        if a["subtype"] not in subtypes or a["skipped"]:
            continue
        net[(a["subtype"], Difficulty(a["difficulty"]))] += -1 if a["correct"] else 1
    return {key: float(v) for key, v in net.items() if v > 0}


def retry_session_size(weights: Weights) -> int:
    """Three questions per open mistake, at least three."""
    return max(3, int(sum(weights.values()) * 3))