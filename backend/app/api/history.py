from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.schemas import HistoryItem

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryItem])
async def list_history(
    session_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[HistoryItem]:
    query = {"session_id": session_id} if session_id else {}
    docs = (
        await db.answers.find(query).sort("answered_at", -1).limit(limit).to_list(length=limit)
    )
    return [HistoryItem.model_validate(d) for d in docs]