from fractions import Fraction
from math import gcd
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import Difficulty, ExamType, Topic


class ExactValue(BaseModel):
    """An exact rational number in lowest terms (no floats, ever)."""

    model_config = ConfigDict(frozen=True)

    numerator: int
    denominator: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def _must_be_lowest_terms(self) -> "ExactValue":
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("ExactValue must be in lowest terms; use from_fraction()")
        return self

    @classmethod
    def from_fraction(cls, f: Fraction) -> "ExactValue":
        return cls(numerator=f.numerator, denominator=f.denominator)

    def to_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)

    def display(self, decimals: int = 2) -> str:
        if self.denominator == 1:
            return str(self.numerator)
        text = f"{float(self.to_fraction()):.{decimals}f}"
        return text.rstrip("0").rstrip(".")


class SolutionStep(BaseModel):
    description: str
    expression: str | None = None
    result: str | None = None


class Question(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    exam: ExamType
    topic: Topic
    subtype: str                       # e.g. "percent_of_number"
    difficulty: Difficulty
    text: str
    unit: str = ""                     # "%", "Rs", ""
    options: list[str]
    correct_index: int
    answer: ExactValue                 # exact truth, used by solver/validator
    params: dict[str, int | str]       # generator inputs, so the solver can recompute
    steps: list[SolutionStep] = Field(default_factory=list)
    seed: int | None = None
    distractor_notes: dict[str, str] = Field(default_factory=dict)  # option text -> why it's wrong

    @model_validator(mode="after")
    def _check_options(self) -> "Question":
        if len(self.options) != 4:
            raise ValueError("A question must have exactly 4 options")
        if len(set(self.options)) != 4:
            raise ValueError("Options must be unique")
        if not 0 <= self.correct_index < 4:
            raise ValueError("correct_index must be between 0 and 3")
        return self