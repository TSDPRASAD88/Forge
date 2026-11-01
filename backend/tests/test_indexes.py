import asyncio

from mongomock_motor import AsyncMongoMockClient

from app.db.indexes import ensure_indexes


def test_ensure_indexes_creates_the_expected_indexes_and_is_repeatable():
    db = AsyncMongoMockClient()["idx_test"]

    async def run():
        await ensure_indexes(db)
        await ensure_indexes(db)                      # running twice must be harmless
        return await db.answers.index_information(), await db.sessions.index_information()

    answers, sessions = asyncio.run(run())
    assert {"session_id_1", "answered_at_-1", "exam_1_subtype_1"} <= set(answers)
    assert "created_at_-1" in sessions