from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import Difficulty, ExamType, Topic
from app.domain.models import Question, SolutionStep


class PublicQuestion(BaseModel):
    """What the client may see BEFORE answering: no answer, params or steps."""

    id: str
    topic: Topic
    subtype: str
    difficulty: Difficulty
    text: str
    unit: str
    options: list[str]

    @classmethod
    def from_question(cls, q: Question) -> "PublicQuestion":
        return cls.model_validate(q.model_dump(include=set(cls.model_fields)))


class SessionCreate(BaseModel):
    exam: ExamType
    topic: Topic | None = None    # None = mix every topic in the exam profile
    difficulty: Difficulty | None = None   # None = use the exam profile's mix
    subtype: str | None = None
    count: int = Field(default=10, ge=1, le=50)


class SessionPublic(BaseModel):
    id: str
    exam: ExamType
    created_at: datetime
    questions: list[PublicQuestion]
    answered: list[str]                    # question ids already answered


class AnswerSubmit(BaseModel):
    question_id: str
    selected_index: int | None = Field(default=None, ge=0, le=3)  # None = skipped
    time_taken_seconds: float | None = Field(default=None, ge=0)


class AnswerResult(BaseModel):
    correct: bool
    skipped: bool
    marks: float
    correct_index: int
    correct_answer: str
    steps: list[SolutionStep]
    explanation: str | None = None     # why the chosen option was wrong


class HistoryItem(BaseModel):
    session_id: str
    question_id: str
    exam: ExamType
    topic: Topic
    subtype: str
    difficulty: Difficulty
    text: str
    selected_index: int | None
    correct_index: int
    correct: bool
    skipped: bool
    marks: float
    time_taken_seconds: float | None
    answered_at: datetime