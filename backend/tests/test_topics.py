
from app.engine.ratios import RATIO_GENERATORS


def start(client, **overrides):
    body = {"exam": "ssc_cgl", "count": 5}
    body.update(overrides)
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_topic_filter_gives_only_that_topic(client):
    s = start(client, topic="ratios", count=10)
    assert {q["topic"] for q in s["questions"]} == {"ratios"}
    assert {q["subtype"] for q in s["questions"]} <= set(RATIO_GENERATORS)


def test_mixed_topics_include_all(client):
    topics = set()
    for _ in range(2):
        topics |= {q["topic"] for q in start(client, count=50)["questions"]}
    assert topics == {"percentages", "ratios", "profit_loss", "time_work", "averages_mixtures"}


def test_averages_mixtures_topic_filter(client):
    from app.engine.averages import AM_GENERATORS

    s = start(client, topic="averages_mixtures", count=10)
    assert {q["topic"] for q in s["questions"]} == {"averages_mixtures"}
    assert {q["subtype"] for q in s["questions"]} <= set(AM_GENERATORS)

def test_time_work_topic_filter(client):
    from app.engine.time_work import TW_GENERATORS

    s = start(client, topic="time_work", count=10)
    assert {q["topic"] for q in s["questions"]} == {"time_work"}
    assert {q["subtype"] for q in s["questions"]} <= set(TW_GENERATORS)


def test_profit_loss_topic_filter(client):
    from app.engine.profit_loss import PL_GENERATORS

    s = start(client, topic="profit_loss", count=10)
    assert {q["topic"] for q in s["questions"]} == {"profit_loss"}
    assert {q["subtype"] for q in s["questions"]} <= set(PL_GENERATORS)


def test_subtype_implies_its_topic(client):
    s = start(client, subtype="ratio_chain", count=5)
    assert all(
        q["subtype"] == "ratio_chain" and q["topic"] == "ratios"
        for q in s["questions"]
    )


def test_subtype_topic_mismatch_is_rejected(client):
    res = client.post(
        "/api/sessions",
        json={
            "exam": "ssc_cgl",
            "topic": "percentages",
            "subtype": "ratio_chain",
        },
    )
    assert res.status_code == 422
