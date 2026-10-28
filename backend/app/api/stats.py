from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.services.analytics import compute_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(exam: str | None = None, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    query = {"exam": exam} if exam else {}
    answers = await db.answers.find(query).to_list(length=None)
    return compute_stats(answers)