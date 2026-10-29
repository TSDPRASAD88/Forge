import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.explain import get_generator
from app.db.mongo import get_db
from app.services import ai as ai_service
from app.services.analytics import compute_stats

MIN_ATTEMPTS = 5

router = APIRouter(prefix="/stats", tags=["ai"])


class AdviceResult(BaseModel):
    summary: str
    actions: list[str]
    cached: bool


@router.post("/advice", response_model=AdviceResult)
async def advice(
    exam: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    generator: ai_service.TextGenerator = Depends(get_generator),
) -> AdviceResult:
    query = {"exam": exam} if exam else {}
    answers = await db.answers.find(query).to_list(length=None)
    stats = compute_stats(answers)
    if stats["overall"]["attempted"] < MIN_ATTEMPTS:
        raise HTTPException(
            status_code=400,
            detail=f"Answer at least {MIN_ATTEMPTS} questions first so the advice has something to work with.",
        )

    facts = ai_service.advice_facts(stats)
    key = hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()

    cached = await db.ai_advice.find_one({"_id": key})
    if cached:
        return AdviceResult(summary=cached["summary"], actions=cached["actions"], cached=True)

    allowed = ai_service.allowed_percents(facts)
    try:
        result = await ai_service.generate_verified(
            generator,
            ai_service.build_advice_prompt(facts),
            lambda raw: ai_service.parse_advice(raw, allowed),
        )
    except ai_service.AIServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service is unavailable or rate-limited. Try again in a minute.",
        ) from exc
    except ai_service.AIVerificationError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI advice failed our checks and was discarded. Your weak-topic list is still accurate.",
        ) from exc

    await db.ai_advice.replace_one(
        {"_id": key},
        {"_id": key, **result, "created_at": datetime.now(timezone.utc)},
        upsert=True,
    )
    return AdviceResult(**result, cached=False)