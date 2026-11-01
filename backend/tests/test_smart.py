from collections import Counter

from app.domain.enums import Difficulty
from app.services.smart import MIN_WEIGHT, RETRY_WINDOW, retry_session_size, retry_weights, weak_weights


def ans(subtype="a", difficulty="easy", correct=True, skipped=False):
    return {"subtype": subtype, "difficulty": difficulty, "correct": correct, "skipped": skipped}


def test_weak_weights_favour_low_accuracy():
    answers = [ans("bad", correct=False)] * 10 + [ans("good")] * 10
    w = weak_weights(answers, {"bad", "good", "new"})
    assert w[("bad", None)] > w[("new", None)] > w[("good", None)]
    assert w[("good", None)] == MIN_WEIGHT


def test_weak_weights_ignore_other_subtypes():
    w = weak_weights([ans("other", correct=False)], {"a"})
    assert w == {("a", None): 0.5}


def test_retry_counts_net_mistakes_per_subtype_and_difficulty():
    answers = [
        ans("a", "easy", correct=False),
        ans("a", "easy", correct=False),
        ans("a", "easy"),                       # net +1
        ans("b", "hard", correct=False),        # net +1
        ans("c", "easy"),                       # net -1, not listed
    ]
    w = retry_weights(answers, {"a", "b", "c"})
    assert w == {("a", Difficulty.EASY): 1.0, ("b", Difficulty.HARD): 1.0}


def test_retry_ignores_skipped_and_respects_the_window():
    assert retry_weights([ans("a", correct=False, skipped=True)], {"a"}) == {}
    old_mistake = [ans("a")] * RETRY_WINDOW + [ans("b", correct=False)]   # newest first
    assert retry_weights(old_mistake, {"a", "b"}) == {}


def test_retry_session_size_is_capped_by_open_mistakes():
    assert retry_session_size({("a", Difficulty.EASY): 1.0}) == 3
    assert retry_session_size({("a", Difficulty.EASY): 2.0, ("b", Difficulty.HARD): 2.0}) == 12


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


def open_mistakes(client) -> Counter:
    net: Counter = Counter()
    for item in client.get("/api/history?limit=200").json():
        net[(item["subtype"], item["difficulty"])] += -1 if item["correct"] else 1
    return Counter({k: v for k, v in net.items() if v > 0})


def test_retry_with_no_history_is_refused(client):
    res = client.post("/api/sessions", json={"exam": "ssc_cgl", "mode": "retry"})
    assert res.status_code == 409


def test_retry_only_asks_about_open_mistakes(client):
    open_: Counter = Counter()
    for _ in range(30):                          # answers are random, so keep going until one is wrong
        answer_all(client, start(client))
        open_ = open_mistakes(client)
        if open_:
            break
    assert open_
    s = start(client, mode="retry", count=10, difficulty=None)
    assert {(q["subtype"], q["difficulty"]) for q in s["questions"]} <= set(open_)
    assert len(s["questions"]) == min(10, max(3, int(sum(open_.values()) * 3)))


def test_weak_mode_builds_a_session(client):
    answer_all(client, start(client))
    s = start(client, mode="weak", count=12, difficulty=None)
    assert len(s["questions"]) == 12


def test_weak_mode_respects_the_topic_filter(client):
    s = start(client, mode="weak", topic="ratios", count=10, difficulty=None)
    assert {q["topic"] for q in s["questions"]} == {"ratios"}


def test_smart_mode_cannot_be_combined_with_a_subtype(client):
    res = client.post("/api/sessions", json={"exam": "ssc_cgl", "mode": "weak", "subtype": "ratio_chain"})
    assert res.status_code == 422