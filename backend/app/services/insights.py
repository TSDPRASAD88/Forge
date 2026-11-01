"""Insights from the answer history: repeated mistakes and pacing."""

from collections import Counter

from app.domain.enums import ExamType
from app.domain.profiles import get_profile

RUSH_FRACTION = 0.25      # under this share of the exam's time per question = rushed
SLOW_SHARE = 0.25         # flag when this share of timed answers went over the time budget
MIN_FOR_FLAG = 5          # never flag a pattern from fewer answers than this
BIAS_MIN_ANSWERS = 30     # the favourite-letter check needs at least this many answers
BIAS_SHARE = 0.40         # one letter picked this often looks like guessing (random is about 25%)
TOP_PATTERNS = 8


def _is_real_trap(tag: str | None) -> bool:
    return bool(tag) and not tag.endswith(":filler")


def mistake_patterns(answers: list[dict], limit: int = TOP_PATTERNS) -> dict:
    counts: Counter = Counter()
    latest: dict[str, dict] = {}
    untagged = 0
    for a in answers:
        if a["correct"] or a["skipped"]:
            continue
        tag = a.get("trap_tag")
        if not _is_real_trap(tag):
            untagged += 1
            continue
        counts[tag] += 1
        if tag not in latest or a["answered_at"] > latest[tag]["answered_at"]:
            latest[tag] = a

    patterns = []
    for tag, n in counts.most_common(limit):
        a = latest[tag]
        patterns.append(
            {
                "tag": tag,
                "subtype": a["subtype"],
                "count": n,
                "session_id": a["session_id"],          # used to look up an example, then removed
                "question_id": a["question_id"],
                "selected_index": a["selected_index"],
            }
        )
    return {"patterns": patterns, "tagged_wrong": sum(counts.values()), "untagged_wrong": untagged}


def pace(answers: list[dict]) -> dict:
    rows = {"rushed": [0, 0], "steady": [0, 0], "slow": [0, 0]}      # [answers, correct]
    rushed_wrong = 0
    budgets: set[int] = set()
    picks: Counter = Counter()

    for a in answers:
        if a["skipped"] or a.get("selected_index") is None:
            continue
        picks[a["selected_index"]] += 1
        seconds = a.get("time_taken_seconds")
        if seconds is None:
            continue
        budget = get_profile(ExamType(a["exam"])).seconds_per_question
        budgets.add(budget)
        if seconds < RUSH_FRACTION * budget:
            bucket = "rushed"
        elif seconds > budget:
            bucket = "slow"
        else:
            bucket = "steady"
        rows[bucket][0] += 1
        rows[bucket][1] += 1 if a["correct"] else 0
        if bucket == "rushed" and not a["correct"]:
            rushed_wrong += 1

    def row(key: str) -> dict:
        n, c = rows[key]
        return {"count": n, "accuracy": round(c / n, 4) if n else None}

    timed = sum(n for n, _ in rows.values())
    budget_seconds = next(iter(budgets)) if len(budgets) == 1 else None
    rushed, steady, slow = row("rushed"), row("steady"), row("slow")
    flags: list[str] = []

    rest_n = rows["steady"][0] + rows["slow"][0]
    rest_acc = (rows["steady"][1] + rows["slow"][1]) / rest_n if rest_n else None
    if rushed["count"] >= MIN_FOR_FLAG:
        # compare with your slower answers only when there are enough of them to mean something
        threshold = rest_acc - 0.10 if rest_n >= MIN_FOR_FLAG else 0.5
        if rushed["accuracy"] < threshold:
            limit = f"{int(RUSH_FRACTION * budget_seconds)}s" if budget_seconds else "a quarter of the time allowed"
            flags.append(
                f"{rushed['count']} of your {timed} timed answers took under {limit} and only "
                f"{round(rushed['accuracy'] * 100)}% of them were right. Work the question out before you click."
            )

    if slow["count"] >= MIN_FOR_FLAG and slow["count"] / timed >= SLOW_SHARE:
        allowed = f"{budget_seconds}s allowed per question" if budget_seconds else "time allowed per question"
        flags.append(
            f"{slow['count']} of your {timed} timed answers ({round(100 * slow['count'] / timed)}%) took longer "
            f"than the {allowed}. Practise the shortcut methods for your slowest topics."
        )

    total_picks = sum(picks.values())
    if total_picks >= BIAS_MIN_ANSWERS:
        index, n = picks.most_common(1)[0]
        if n / total_picks >= BIAS_SHARE:
            flags.append(
                f"You picked option {'ABCD'[index]} in {round(100 * n / total_picks)}% of your answers. "
                f"Correct answers are spread evenly across A to D, so a favourite letter suggests guessing."
            )

    return {
        "timed_answers": timed,
        "budget_seconds": budget_seconds,
        "rushed": rushed,
        "steady": steady,
        "slow": slow,
        "rushed_wrong": rushed_wrong,
        "option_picks": {letter: picks[i] for i, letter in enumerate("ABCD")},
        "flags": flags,
    }


def compute_insights(answers: list[dict]) -> dict:
    return {**mistake_patterns(answers), "pace": pace(answers)}