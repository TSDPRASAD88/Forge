import json

import pytest

from app.api.explain import get_generator
from app.main import app
from app.services.ai import AIVerificationError, parse_advice


class FakeAI:
    def __init__(self, replies=()):
        self.replies = list(replies)
        self.calls = 0

    async def generate(self, prompt: str) -> str:
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def reply(summary="You are building a solid base.", actions=("Practise A.", "Practise B.", "Practise C.")):
    return json.dumps({"summary": summary, "actions": list(actions)})


BAD = reply(summary="You are at 4242% accuracy.")     # invented percentage


@pytest.fixture
def ai(client):
    fake = FakeAI()
    app.dependency_overrides[get_generator] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_generator, None)


def answer_some(client, n, count=None):
    s = client.post(
        "/api/sessions", json={"exam": "ssc_cgl", "difficulty": "easy", "count": count or n}
    ).json()
    for q in s["questions"][:n]:
        client.post(
            f"/api/sessions/{s['id']}/answers",
            json={"question_id": q["id"], "selected_index": 0, "time_taken_seconds": 8},
        )
    return s


def test_needs_enough_answers(client, ai):
    assert client.post("/api/stats/advice").status_code == 400
    assert ai.calls == 0


def test_advice_is_returned_then_cached(client, ai):
    answer_some(client, 6)
    ai.replies = [reply()]
    first = client.post("/api/stats/advice")
    assert first.status_code == 200
    body = first.json()
    assert body["cached"] is False
    assert len(body["actions"]) == 3
    assert client.post("/api/stats/advice").json()["cached"] is True
    assert ai.calls == 1


def test_new_answers_trigger_fresh_advice(client, ai):
    s = answer_some(client, 6, count=7)
    ai.replies = [reply(), reply()]
    assert client.post("/api/stats/advice").json()["cached"] is False
    client.post(
        f"/api/sessions/{s['id']}/answers",
        json={"question_id": s["questions"][6]["id"], "selected_index": 0, "time_taken_seconds": 8},
    )
    assert client.post("/api/stats/advice").json()["cached"] is False
    assert ai.calls == 2


def test_invented_percentage_is_rejected_then_good_accepted(client, ai):
    answer_some(client, 6)
    ai.replies = [BAD, reply()]
    assert client.post("/api/stats/advice").status_code == 200
    assert ai.calls == 2


def test_two_bad_replies_give_502(client, ai):
    answer_some(client, 6)
    ai.replies = [BAD, BAD]
    assert client.post("/api/stats/advice").status_code == 502
    assert ai.calls == 2


def test_service_error_gives_502(client, ai):
    answer_some(client, 6)
    ai.replies = [RuntimeError("429 quota exceeded")]
    assert client.post("/api/stats/advice").status_code == 502
    assert ai.calls == 1


def test_missing_key_gives_503(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    try:
        assert client.post("/api/stats/advice").status_code == 503
    finally:
        get_settings.cache_clear()


def test_parse_accepts_a_listed_percentage():
    out = parse_advice(reply(summary="You solved 67% correctly."), {67})
    assert out["summary"] == "You solved 67% correctly."
    assert len(out["actions"]) == 3


def test_parse_rejects_an_invented_percentage():
    with pytest.raises(AIVerificationError):
        parse_advice(reply(summary="You solved 80% correctly."), {67})


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        json.dumps({"summary": "ok", "actions": "not a list"}),
        json.dumps({"summary": "", "actions": ["a"]}),
    ],
)
def test_parse_rejects_bad_shapes(raw):
    with pytest.raises(AIVerificationError):
        parse_advice(raw, {67})


def test_parse_also_catches_the_word_percent():
    with pytest.raises(AIVerificationError):
        parse_advice(reply(summary="You are at 80 percent overall."), {67})