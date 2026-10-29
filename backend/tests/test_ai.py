import json

import pytest

from app.api.explain import get_generator
from app.domain.enums import Difficulty, ExamType
from app.engine.generator import generate_question
from app.main import app
from app.services.ai import AIVerificationError, parse_and_verify


class FakeAI:
    """Stands in for Gemini. Each reply is a string to return, or an Exception to raise."""

    def __init__(self, replies=()):
        self.replies = list(replies)
        self.calls = 0

    async def generate(self, prompt: str) -> str:
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def reply(final, text="Use the multiplier method."):
    return json.dumps({"explanation": text, "final_answer": str(final)})


@pytest.fixture
def ai(client):
    fake = FakeAI()
    app.dependency_overrides[get_generator] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_generator, None)


def answered_question(client, selected=0):
    s = client.post("/api/sessions", json={"exam": "ssc_cgl", "difficulty": "easy", "count": 1}).json()
    q = s["questions"][0]
    r = client.post(
        f"/api/sessions/{s['id']}/answers", json={"question_id": q["id"], "selected_index": selected}
    ).json()
    return s["id"], q["id"], r["correct_answer"]


def url(sid, qid):
    return f"/api/sessions/{sid}/questions/{qid}/explain"


def test_refuses_before_answering(client, ai):
    s = client.post("/api/sessions", json={"exam": "ssc_cgl", "difficulty": "easy", "count": 1}).json()
    res = client.post(url(s["id"], s["questions"][0]["id"]))
    assert res.status_code == 403
    assert ai.calls == 0


def test_good_reply_is_returned_then_cached(client, ai):
    sid, qid, correct = answered_question(client)
    ai.replies = [reply(correct, "Think of it as a multiplier.")]
    first = client.post(url(sid, qid))
    assert first.status_code == 200
    assert first.json() == {"explanation": "Think of it as a multiplier.", "cached": False}
    second = client.post(url(sid, qid))
    assert second.json()["cached"] is True
    assert ai.calls == 1


def test_bad_final_answer_twice_is_rejected_and_not_cached(client, ai):
    sid, qid, correct = answered_question(client)
    ai.replies = [reply("999999"), reply("999999"), reply(correct)]
    assert client.post(url(sid, qid)).status_code == 502
    assert client.post(url(sid, qid)).status_code == 200   # nothing bad was cached
    assert ai.calls == 3


@pytest.mark.parametrize(
    "bad", ["not json at all", reply("999999"), json.dumps({"explanation": "no answer field"})]
)
def test_one_bad_reply_then_good_is_accepted(client, ai, bad):
    sid, qid, correct = answered_question(client)
    ai.replies = [bad, reply(correct)]
    assert client.post(url(sid, qid)).status_code == 200
    assert ai.calls == 2


def test_service_error_gives_502_without_retry(client, ai):
    sid, qid, _ = answered_question(client)
    ai.replies = [RuntimeError("429 quota exceeded")]
    assert client.post(url(sid, qid)).status_code == 502
    assert ai.calls == 1


def test_missing_key_gives_503(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    try:
        sid, qid, _ = answered_question(client)
        assert client.post(url(sid, qid)).status_code == 503
    finally:
        get_settings.cache_clear()


def make_q():
    return generate_question(ExamType.SSC_CGL, Difficulty.EASY, subtype="percent_of_number", seed=1)


def test_parse_accepts_units_around_the_number():
    q = make_q()
    ans = q.answer.display()
    assert parse_and_verify(reply(f"Rs {ans}"), q)
    assert parse_and_verify(reply(f"{ans}%"), q)


def test_parse_rejects_wrong_answer():
    q = make_q()
    with pytest.raises(AIVerificationError):
        parse_and_verify(reply("123456"), q)