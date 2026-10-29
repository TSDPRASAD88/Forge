from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

MIN_ATTEMPTS_FOR_WEAK = 5
WEAK_ACCURACY_THRESHOLD = 0.6
ACTIVITY_DAYS = 14


def _bucket() -> dict[str, Any]:
    return {"attempted": 0, "correct": 0, "skipped": 0, "marks": 0.0, "time_sum": 0.0, "time_n": 0}


def _add(b: dict[str, Any], a: dict) -> None:
    b["attempted"] += 1
    b["correct"] += 1 if a["correct"] else 0
    b["skipped"] += 1 if a["skipped"] else 0
    b["marks"] += a["marks"]
    if a.get("time_taken_seconds") is not None:
        b["time_sum"] += a["time_taken_seconds"]
        b["time_n"] += 1


def _finish(key: str, b: dict[str, Any]) -> dict[str, Any]:
    attempted = b["attempted"]
    return {
        "key": key,
        "attempted": attempted,
        "correct": b["correct"],
        "skipped": b["skipped"],
        "accuracy": round(b["correct"] / attempted, 4) if attempted else 0.0,
        "marks": round(b["marks"], 4),
        "avg_time_seconds": round(b["time_sum"] / b["time_n"], 2) if b["time_n"] else None,
    }


def compute_stats(answers: list[dict], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    overall = _bucket()
    by_subtype: dict[str, dict] = defaultdict(_bucket)
    by_difficulty: dict[str, dict] = defaultdict(_bucket)
    per_day: dict[str, dict] = defaultdict(lambda: {"attempted": 0, "correct": 0})

    for a in answers:
        _add(overall, a)
        _add(by_subtype[a["subtype"]], a)
        _add(by_difficulty[a["difficulty"]], a)
        day = a["answered_at"].strftime("%Y-%m-%d")
        per_day[day]["attempted"] += 1
        per_day[day]["correct"] += 1 if a["correct"] else 0

    subtype_rows = sorted((_finish(k, b) for k, b in by_subtype.items()), key=lambda r: r["key"])
    difficulty_rows = [
        _finish(k, by_difficulty[k]) for k in ("easy", "medium", "hard") if k in by_difficulty
    ]
    weak = sorted(
        (r for r in subtype_rows
         if r["attempted"] >= MIN_ATTEMPTS_FOR_WEAK and r["accuracy"] < WEAK_ACCURACY_THRESHOLD),
        key=lambda r: r["accuracy"],
    )

    activity = []
    for offset in range(ACTIVITY_DAYS - 1, -1, -1):
        day = (now - timedelta(days=offset)).strftime("%Y-%m-%d")
        d = per_day.get(day, {"attempted": 0, "correct": 0})
        activity.append({"date": day, **d})

    return {
        "overall": _finish("overall", overall),
        "by_subtype": subtype_rows,
        "by_difficulty": difficulty_rows,
        "weak_topics": weak,
        "activity": activity,
    }