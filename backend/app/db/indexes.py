"""MongoDB indexes. Safe to run repeatedly."""

from motor.motor_asyncio import AsyncIOMotorDatabase


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.answers.create_index("session_id")                       # session lookups
    await db.answers.create_index([("answered_at", -1)])              # history, newest first
    await db.answers.create_index([("exam", 1), ("subtype", 1)])      # stats filtered by exam
    await db.sessions.create_index([("created_at", -1)])              # "recent sessions" lookup