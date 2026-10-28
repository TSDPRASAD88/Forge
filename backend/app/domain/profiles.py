from pydantic import BaseModel, model_validator

from app.domain.enums import Difficulty, ExamType, Topic


class ExamProfile(BaseModel):
    exam: ExamType
    name: str
    description: str
    topics: list[Topic]
    difficulty_mix: dict[Difficulty, float]
    marks_correct: float
    marks_negative: float
    seconds_per_question: int

    @model_validator(mode="after")
    def _mix_sums_to_one(self) -> "ExamProfile":
        if abs(sum(self.difficulty_mix.values()) - 1.0) > 1e-9:
            raise ValueError("difficulty_mix must sum to 1")
        return self


PROFILES: dict[ExamType, ExamProfile] = {
    ExamType.GATE_CSE: ExamProfile(
        exam=ExamType.GATE_CSE,
        name="GATE CSE - General Aptitude",
        description="Verbal and numerical aptitude section of GATE CSE.",
        topics=[Topic.PERCENTAGES],
        difficulty_mix={Difficulty.EASY: 0.2, Difficulty.MEDIUM: 0.5, Difficulty.HARD: 0.3},
        marks_correct=1.0,
        marks_negative=1 / 3,
        seconds_per_question=90,
    ),
    ExamType.SSC_CGL: ExamProfile(
        exam=ExamType.SSC_CGL,
        name="SSC CGL - Quantitative Aptitude",
        description="Speed-focused arithmetic for SSC CGL Tier 1.",
        topics=[Topic.PERCENTAGES],
        difficulty_mix={Difficulty.EASY: 0.4, Difficulty.MEDIUM: 0.4, Difficulty.HARD: 0.2},
        marks_correct=2.0,
        marks_negative=0.5,
        seconds_per_question=36,
    ),
}


def get_profile(exam: ExamType) -> ExamProfile:
    return PROFILES[exam]