from datetime import datetime, timezone

from app.services.analytics import compute_stats

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def ans(subtype="what_percent", difficulty="easy", correct=True, skipped=False, marks=2.0, t=10.0):
    return {
        "subtype": subtype, "difficulty": difficulty, "correct": correct,
        "skipped": skipped, "marks": marks, "time_taken_seconds": t, "answered_at": NOW,
    }


def test_empty():
    s = compute_stats([], now=NOW)
    assert s["overall"]["attempted"] == 0
    assert s["overall"]["accuracy"] == 0.0
    assert s["weak_topics"] == []
    assert len(s["activity"]) == 14


def test_overall_numbers():
    s = compute_stats([ans(), ans(correct=False, marks=-0.5, t=20.0), ans(skipped=True, correct=False, marks=0.0, t=None)], now=NOW)
    o = s["overall"]
    assert (o["attempted"], o["correct"], o["skipped"]) == (3, 1, 1)
    assert o["marks"] == 1.5
    assert o["avg_time_seconds"] == 15.0          # skipped-without-time excluded
    assert o["accuracy"] == round(1 / 3, 4)


def test_breakdowns():
    s = compute_stats([ans("a", "easy"), ans("b", "hard"), ans("b", "hard")], now=NOW)
    assert {r["key"]: r["attempted"] for r in s["by_subtype"]} == {"a": 1, "b": 2}
    assert [r["key"] for r in s["by_difficulty"]] == ["easy", "hard"]


def test_weak_topics_need_enough_attempts():
    few = [ans("x", correct=False, marks=-0.5) for _ in range(4)]
    assert compute_stats(few, now=NOW)["weak_topics"] == []
    enough = [ans("x", correct=False, marks=-0.5) for _ in range(5)]
    assert [r["key"] for r in compute_stats(enough, now=NOW)["weak_topics"]] == ["x"]


def test_weak_topics_sorted_worst_first():
    data = (
        [ans("meh", correct=(i < 2)) for i in range(5)]      # 40%
        + [ans("bad", correct=(i < 1)) for i in range(5)]    # 20%
        + [ans("good") for _ in range(5)]                    # 100%
    )
    assert [r["key"] for r in compute_stats(data, now=NOW)["weak_topics"]] == ["bad", "meh"]


def test_activity_counts_today():
    s = compute_stats([ans(), ans(correct=False)], now=NOW)
    today = s["activity"][-1]
    assert today["date"] == "2026-10-28"
    assert (today["attempted"], today["correct"]) == (2, 1)


def test_stats_endpoint(client):
    r = client.post("/api/sessions", json={"exam": "ssc_cgl", "difficulty": "easy", "count": 3}).json()
    for q in r["questions"]:
        client.post(f"/api/sessions/{r['id']}/answers", json={"question_id": q["id"], "selected_index": 0, "time_taken_seconds": 5})
    s = client.get("/api/stats").json()
    assert s["overall"]["attempted"] == 3
    assert client.get("/api/stats?exam=gate_cse").json()["overall"]["attempted"] == 0