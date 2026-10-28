
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_db
from app.domain.models import Question
from app.domain.profiles import get_profile
from app.engine.generator import GENERATORS
from app.schemas import (
    AnswerResult,
    AnswerSubmit,
    PublicQuestion,
    SessionCreate,
    SessionPublic,
)
from app.services.practice import QuestionBuildError, build_questions

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _load_session(db: AsyncIOMotorDatabase, session_id: str) -> dict:
    doc = await db.sessions.find_one({"_id": session_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return doc


@router.post("", response_model=SessionPublic, status_code=201)
async def create_session(
    body: SessionCreate, db: AsyncIOMotorDatabase = Depends(get_db)
) -> SessionPublic:
    if body.subtype is not None and body.subtype not in GENERATORS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown subtype: {body.subtype}",
        )

    try:
        questions = build_questions(
            body.exam,
            body.count,
            body.difficulty,
            body.subtype,
        )
    except QuestionBuildError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session_id = uuid4().hex
    now = datetime.now(timezone.utc)

    await db.sessions.insert_one(
        {
            "_id": session_id,
            "exam": body.exam.value,
            "created_at": now,
            "questions": [q.model_dump(mode="json") for q in questions],
        }
    )

    return SessionPublic(
        id=session_id,
        exam=body.exam,
        created_at=now,
        questions=[PublicQuestion.from_question(q) for q in questions],
        answered=[],
    )


@router.get("/{session_id}", response_model=SessionPublic)
async def read_session(
    session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
) -> SessionPublic:
    doc = await _load_session(db, session_id)
    answers = await db.answers.find(
        {"session_id": session_id}
    ).to_list(length=None)

    return SessionPublic(
        id=session_id,
        exam=doc["exam"],
        created_at=doc["created_at"],
        questions=[
            PublicQuestion.from_question(Question.model_validate(raw))
            for raw in doc["questions"]
        ],
        answered=[a["question_id"] for a in answers],
    )


@router.post("/{session_id}/answers", response_model=AnswerResult)
async def submit_answer(
    session_id: str,
    body: AnswerSubmit,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnswerResult:
    doc = await _load_session(db, session_id)

    raw = next(
        (q for q in doc["questions"] if q["id"] == body.question_id),
        None,
    )
    if raw is None:
        raise HTTPException(
            status_code=404,
            detail="Question not in this session",
        )

    q = Question.model_validate(raw)
    profile = get_profile(q.exam)

    skipped = body.selected_index is None
    correct = (not skipped) and body.selected_index == q.correct_index

    if skipped:
        marks = 0.0
    elif correct:
        marks = profile.marks_correct
    else:
        marks = round(-profile.marks_negative, 4)

    try:
        # Composite _id makes one answer per question per session atomic.
        await db.answers.insert_one(
            {
                "_id": f"{session_id}:{q.id}",
                "session_id": session_id,
                "question_id": q.id,
                "exam": q.exam.value,
                "topic": q.topic.value,
                "subtype": q.subtype,
                "difficulty": q.difficulty.value,
                "text": q.text,
                "selected_index": body.selected_index,
                "correct_index": q.correct_index,
                "correct": correct,
                "skipped": skipped,
                "marks": marks,
                "time_taken_seconds": body.time_taken_seconds,
                "answered_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Question already answered",
        ) from None

    explanation = None
    if not skipped and not correct:
        explanation = q.distractor_notes.get(
            q.options[body.selected_index]
        )

    return AnswerResult(
        correct=correct,
        skipped=skipped,
        marks=marks,
        correct_index=q.correct_index,
        correct_answer=q.options[q.correct_index],
        steps=q.steps,
        explanation=explanation,
    )
