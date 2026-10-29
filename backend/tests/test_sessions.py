def start(client, **overrides):
    body = {"exam": "ssc_cgl", "difficulty": "easy", "count": 5}
    body.update(overrides)
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_session_hides_answers(client):
    s = start(client)
    assert len(s["questions"]) == 5
    assert s["answered"] == []
    for q in s["questions"]:
        for secret in ("correct_index", "answer", "steps", "params", "seed"):
            assert secret not in q
        assert len(q["options"]) == 4


def test_mixed_difficulty_when_none_given(client):
    s = start(client, difficulty=None, count=20)
    assert len(s["questions"]) == 20


def test_unknown_subtype_rejected(client):
    res = client.post("/api/sessions", json={"exam": "ssc_cgl", "subtype": "nope"})
    assert res.status_code == 422


def test_count_limits(client):
    assert client.post("/api/sessions", json={"exam": "ssc_cgl", "count": 0}).status_code == 422
    assert client.post("/api/sessions", json={"exam": "ssc_cgl", "count": 51}).status_code == 422


def test_get_session(client):
    s = start(client)
    res = client.get(f"/api/sessions/{s['id']}")
    assert res.status_code == 200
    assert [q["id"] for q in res.json()["questions"]] == [q["id"] for q in s["questions"]]


def test_unknown_session_404(client):
    assert client.get("/api/sessions/does-not-exist").status_code == 404


def test_submit_answer_marks_and_solution(client):
    s = start(client)
    for q in s["questions"]:
        res = client.post(
            f"/api/sessions/{s['id']}/answers",
            json={"question_id": q["id"], "selected_index": 0},
        )
        assert res.status_code == 200, res.text
        r = res.json()
        is_correct = r["correct_index"] == 0
        assert r["correct"] == is_correct
        assert r["marks"] == (2.0 if is_correct else -0.5)   # ssc_cgl marking
        assert r["correct_answer"] == q["options"][r["correct_index"]]
        assert len(r["steps"]) >= 2

    answered = client.get(f"/api/sessions/{s['id']}").json()["answered"]
    assert sorted(answered) == sorted(q["id"] for q in s["questions"])


def test_double_answer_conflict(client):
    s = start(client)
    payload = {"question_id": s["questions"][0]["id"], "selected_index": 1}
    assert client.post(f"/api/sessions/{s['id']}/answers", json=payload).status_code == 200
    assert client.post(f"/api/sessions/{s['id']}/answers", json=payload).status_code == 409


def test_skip_scores_zero(client):
    s = start(client)
    res = client.post(
        f"/api/sessions/{s['id']}/answers",
        json={"question_id": s["questions"][0]["id"]},
    )
    r = res.json()
    assert r["skipped"] and not r["correct"] and r["marks"] == 0


def test_unknown_question_404(client):
    s = start(client)
    res = client.post(
        f"/api/sessions/{s['id']}/answers",
        json={"question_id": "nope", "selected_index": 0},
    )
    assert res.status_code == 404


def test_history_lists_answers_and_filters_by_session(client):
    s1, s2 = start(client, count=2), start(client, count=2)
    for s in (s1, s2):
        for q in s["questions"]:
            client.post(
                f"/api/sessions/{s['id']}/answers",
                json={"question_id": q["id"], "selected_index": 0, "time_taken_seconds": 12.5},
            )
    everything = client.get("/api/history").json()
    assert len(everything) == 4
    only_s1 = client.get(f"/api/history?session_id={s1['id']}").json()
    assert len(only_s1) == 2
    assert all(item["session_id"] == s1["id"] for item in only_s1)
    assert only_s1[0]["time_taken_seconds"] == 12.5


def test_wrong_answer_gets_explanation(client):
    s = start(client, count=8)
    wrong_seen = 0
    for q in s["questions"]:
        assert "distractor_notes" not in q            # notes must not leak before answering
        r = client.post(
            f"/api/sessions/{s['id']}/answers",
            json={"question_id": q["id"], "selected_index": 0},
        ).json()
        if r["correct"]:
            assert r["explanation"] is None
        else:
            wrong_seen += 1
            assert r["explanation"]
    assert wrong_seen >= 1