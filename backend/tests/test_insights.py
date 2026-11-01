from datetime import datetime, timedelta, timezone

from app.services.insights import mistake_patterns, pace

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def ans(correct=False, skipped=False, tag=None, subtype="pl_profit_percent", t=20.0, sel=0,
        exam="ssc_cgl", minutes=0):
    return {
        "exam": exam, "subtype": subtype, "correct": correct, "skipped": skipped, "trap_tag": tag,
        "time_taken_seconds": t, "selected_index": None if skipped else sel,
        "session_id": "s1", "question_id": f"q{minutes}", "answered_at": T0 + timedelta(minutes=minutes),
    }


def test_patterns_count_and_rank():
    answers = (
        [ans(tag="pl_profit_percent:t0", minutes=i) for i in range(3)]
        + [ans(tag="pl_profit_percent:t1", minutes=10)]
        + [ans(correct=True, minutes=11)]                      # correct: ignored
        + [ans(skipped=True, minutes=12)]                      # skipped: ignored
        + [ans(tag="pl_profit_percent:filler", minutes=13)]    # filler is not a pattern
        + [ans(tag=None, minutes=14)]                          # answered before tags existed
    )
    out = mistake_patterns(answers)
    assert [(p["tag"], p["count"]) for p in out["patterns"]] == [
        ("pl_profit_percent:t0", 3),
        ("pl_profit_percent:t1", 1),
    ]
    assert out["tagged_wrong"] == 4
    assert out["untagged_wrong"] == 2


def test_pattern_remembers_the_latest_answer():
    out = mistake_patterns([ans(tag="x:t0", minutes=5), ans(tag="x:t0", minutes=1)])
    assert out["patterns"][0]["question_id"] == "q5"


def test_pace_buckets_use_the_exam_budget():
    answers = [
        ans(t=2.0), ans(t=8.9),                 # under 9s (a quarter of 36s): rushed, wrong
        ans(t=36.0, correct=True),              # exactly on budget: steady
        ans(t=36.1),                            # over budget: slow
    ]
    p = pace(answers)
    assert p["budget_seconds"] == 36
    assert p["timed_answers"] == 4
    assert p["rushed"] == {"count": 2, "accuracy": 0.0}
    assert p["steady"] == {"count": 1, "accuracy": 1.0}
    assert p["slow"] == {"count": 1, "accuracy": 0.0}
    assert p["rushed_wrong"] == 2


def test_rushed_flag():
    answers = [ans(t=2.0) for _ in range(6)] + [ans(t=20.0, correct=True) for _ in range(6)]
    flags = pace(answers)["flags"]
    assert any("under 9s" in f and "0%" in f for f in flags)


def test_no_rushed_flag_when_fast_answers_are_right():
    answers = [ans(t=2.0, correct=True) for _ in range(6)] + [ans(t=20.0, correct=True) for _ in range(6)]
    assert pace(answers)["flags"] == []


def test_rushed_flag_needs_enough_answers():
    assert pace([ans(t=2.0) for _ in range(4)])["flags"] == []


def test_slow_flag():
    answers = [ans(t=50.0, correct=True) for _ in range(6)] + [ans(t=20.0, correct=True) for _ in range(6)]
    flags = pace(answers)["flags"]
    assert len(flags) == 1 and "longer than" in flags[0]


def test_option_bias_flag():
    picks = [0] * 20 + [1] * 7 + [2] * 7 + [3] * 6
    answers = [ans(t=20.0, correct=(i % 2 == 0), sel=s) for i, s in enumerate(picks)]
    assert any("option A" in f for f in pace(answers)["flags"])


def test_no_option_bias_flag_when_spread_out():
    answers = [ans(t=20.0, correct=True, sel=i % 4) for i in range(40)]
    assert pace(answers)["flags"] == []


def test_option_bias_needs_enough_answers():
    assert pace([ans(t=20.0, correct=True, sel=0) for _ in range(10)])["flags"] == []


def test_mixed_exams_have_no_single_budget():
    p = pace([ans(t=20.0, exam="ssc_cgl"), ans(t=20.0, exam="gate_cse")])
    assert p["budget_seconds"] is None


# ---- through the API ----

def start(client, **overrides):
    body = {"exam": "ssc_cgl", "count": 5, "difficulty": "easy"}
    body.update(overrides)
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def answer_all(client, s):
    for q in s["questions"]:
        client.post(f"/api/sessions/{s['id']}/answers", json={"question_id": q["id"], "selected_index": 0})


def test_insights_endpoint_describes_patterns(client):
    items = []
    for _ in range(30):                  # answers are random, so keep going until a real mistake appears
        answer_all(client, start(client))
        items = client.get("/api/history?limit=200").json()
        if any(not i["correct"] and i["trap_tag"] and not i["trap_tag"].endswith(":filler") for i in items):
            break
    wrong = [i for i in items if not i["correct"] and not i["skipped"]]

    out = client.get("/api/stats/insights").json()
    assert out["patterns"]
    for p in out["patterns"]:
        assert p["note"] and p["example"]
        assert "session_id" not in p and "question_id" not in p
    assert out["tagged_wrong"] + out["untagged_wrong"] == len(wrong)
    assert {"rushed", "steady", "slow", "flags"} <= set(out["pace"])


def test_insights_endpoint_filters_by_exam(client):
    answer_all(client, start(client))
    out = client.get("/api/stats/insights?exam=gate_cse").json()
    assert out["patterns"] == []
    assert out["pace"]["timed_answers"] == 0

def test_rushed_flag_when_there_are_too_few_slower_answers_to_compare():
    answers = [ans(t=2.0) for _ in range(8)] + [ans(t=20.0) for _ in range(2)]
    assert any("under 9s" in f for f in pace(answers)["flags"])