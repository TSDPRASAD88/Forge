"""Creates the indexes in the database from your .env.  Run from backend/:  python -m app.tools.create_indexes"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.db.indexes import ensure_indexes


async def main() -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongo_db]
    await ensure_indexes(db)
    for name in ("answers", "sessions"):
        info = await db[name].index_information()
        print(f"{name}: {', '.join(sorted(info))}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())