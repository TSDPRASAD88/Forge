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


def test_mixed_topics_include_both(client):
    s = start(client, count=40)
    assert {q["topic"] for q in s["questions"]} == {"percentages", "ratios"}


def test_subtype_implies_its_topic(client):
    s = start(client, subtype="ratio_chain", count=5)
    assert all(q["subtype"] == "ratio_chain" and q["topic"] == "ratios" for q in s["questions"])


def test_subtype_topic_mismatch_is_rejected(client):
    res = client.post(
        "/api/sessions",
        json={"exam": "ssc_cgl", "topic": "percentages", "subtype": "ratio_chain"},
    )
    assert res.status_code == 422