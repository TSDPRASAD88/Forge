import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.db.mongo import get_db
from app.domain.models import Question
from app.services import ai as ai_service

log = logging.getLogger(__name__)
MAX_ATTEMPTS = 2

router = APIRouter(prefix="/sessions", tags=["ai"])


class ExplainResult(BaseModel):
    explanation: str
    cached: bool


def get_generator() -> ai_service.TextGenerator:
    try:
        return ai_service.make_generator()
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{session_id}/questions/{question_id}/explain", response_model=ExplainResult)
async def explain(
    session_id: str,
    question_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    generator: ai_service.TextGenerator = Depends(get_generator),
) -> ExplainResult:
    key = f"{session_id}:{question_id}"

    answer = await db.answers.find_one({"_id": key})
    if answer is None:
        raise HTTPException(status_code=403, detail="Answer the question before asking for an explanation")

    cached = await db.ai_explanations.find_one({"_id": key})
    if cached:
        return ExplainResult(explanation=cached["explanation"], cached=True)

    session = await db.sessions.find_one({"_id": session_id})
    raw = next((r for r in session["questions"] if r["id"] == question_id), None) if session else None
    if raw is None:
        raise HTTPException(status_code=404, detail="Question not found")

    q = Question.model_validate(raw)
    idx = answer["selected_index"]
    selected = q.options[idx] if idx is not None else None
    prompt = ai_service.build_prompt(q, selected)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            reply = await generator.generate(prompt)
        except Exception as exc:  # noqa: BLE001  (network, quota, SDK errors)
            log.warning("Gemini call failed: %r", exc)
            raise HTTPException(
                status_code=502,
                detail="The AI service is unavailable or rate-limited. Try again in a minute. The standard steps are still correct.",
            ) from exc
        try:
            text = ai_service.parse_and_verify(reply, q)
        except ai_service.AIVerificationError as exc:
            log.warning("AI reply rejected (attempt %d): %s", attempt, exc)
            continue
        await db.ai_explanations.replace_one(
            {"_id": key},
            {"_id": key, "explanation": text, "created_at": datetime.now(timezone.utc)},
            upsert=True,
        )
        return ExplainResult(explanation=text, cached=False)

    raise HTTPException(
        status_code=502,
        detail="The AI explanation failed our answer check and was discarded. Use the standard steps.",
    )