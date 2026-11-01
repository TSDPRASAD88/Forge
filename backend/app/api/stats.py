from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.services.analytics import compute_stats
from app.services.insights import compute_insights

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(exam: str | None = None, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    query = {"exam": exam} if exam else {}
    answers = await db.answers.find(query).to_list(length=None)
    return compute_stats(answers)


async def _describe(db: AsyncIOMotorDatabase, pattern: dict) -> dict:
    """Look up the explanation and an example question for a mistake pattern, then drop the lookup keys."""
    session = await db.sessions.find_one({"_id": pattern.pop("session_id")})
    question_id = pattern.pop("question_id")
    selected = pattern.pop("selected_index")
    raw = next((q for q in session["questions"] if q["id"] == question_id), None) if session else None
    if raw is None or selected is None:
        return {"note": None, "example": None}
    option = raw["options"][selected]
    return {"note": raw.get("distractor_notes", {}).get(option), "example": raw["text"]}


@router.get("/insights")
async def get_insights(exam: str | None = None, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    query = {"exam": exam} if exam else {}
    answers = await db.answers.find(query).to_list(length=None)
    result = compute_insights(answers)
    for pattern in result["patterns"]:
        pattern.update(await _describe(db, pattern))
    return result