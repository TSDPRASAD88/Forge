import json
import re
import logging
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings
from app.domain.models import Question
log = logging.getLogger(__name__)

class AIUnavailableError(RuntimeError):
    """No API key configured."""


class AIVerificationError(ValueError):
    """The reply was malformed, or its final answer did not match ours."""


class TextGenerator(Protocol):
    async def generate(self, prompt: str) -> str: ...


class GeminiGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(self, prompt: str) -> str:
        from google.genai import types

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        return response.text or ""


@lru_cache
def _gemini(api_key: str, model: str) -> GeminiGenerator:
    return GeminiGenerator(api_key, model)


def make_generator() -> TextGenerator:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AIUnavailableError("GEMINI_API_KEY is not set in backend/.env")
    return _gemini(settings.gemini_api_key, settings.gemini_model)


def build_prompt(q: Question, selected: str | None) -> str:
    steps = "\n".join(
        f"{i}. {s.description} {s.expression or ''} {('= ' + s.result) if s.result else ''}".strip()
        for i, s in enumerate(q.steps, 1)
    )
    options = ", ".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(q.options))
    correct = q.options[q.correct_index]

    if selected is None:
        learner = "The learner skipped this question."
    elif selected == correct:
        learner = f"The learner chose {selected}, which is correct."
    else:
        note = q.distractor_notes.get(selected, "")
        learner = f"The learner chose {selected}, which is wrong. Known reason: {note}"

    return f"""You are a patient aptitude tutor for competitive exams.

Question: {q.text}
Options: {options}
Correct answer: {correct}
Standard solution steps:
{steps}
{learner}

Task: explain how to get the correct answer using a DIFFERENT method or a quick shortcut
than the standard steps (for example fractions, multipliers or mental maths), in simple language.
Rules:
- Work forward from the numbers in the question. Never start from the correct answer or use it to check the method.
- Use 3 to 4 short sentences, at most 90 words.
- Never change, round or reinterpret any number from the question.
- Your method must end at exactly the correct answer given above.
Reply with JSON only, in this exact shape:
{{"explanation": "<your explanation>", "final_answer": "<the final number only>"}}"""


def parse_and_verify(raw: str, q: Question) -> str:
    """Return the explanation text only if the model's final answer equals our exact answer."""
    try:
        data = json.loads(raw)
        text = str(data["explanation"]).strip()
        cleaned = re.sub(r"[^0-9.\-]", "", str(data["final_answer"]).replace("−", "-"))
        final = Fraction(Decimal(cleaned))
    except (ValueError, KeyError, TypeError, InvalidOperation, ZeroDivisionError) as exc:
        raise AIVerificationError(f"malformed reply: {exc!r}") from exc
    if not text:
        raise AIVerificationError("empty explanation")
    if final != q.answer.to_fraction():
        raise AIVerificationError(f"model answered {final}, expected {q.answer.to_fraction()}")
    return text


class AIServiceError(RuntimeError):
    """The AI service itself failed (network, quota, SDK error)."""


async def generate_verified(generator: TextGenerator, prompt: str, verify, attempts: int = 2):
    """Call the model; return verify(reply). Retry once if the reply fails verification."""
    for attempt in range(1, attempts + 1):
        try:
            reply = await generator.generate(prompt)
        except Exception as exc:  # noqa: BLE001
            log.warning("Gemini call failed: %r", exc)
            raise AIServiceError(str(exc)) from exc
        try:
            return verify(reply)
        except AIVerificationError as exc:
            log.warning("AI reply rejected (attempt %d): %s", attempt, exc)
    raise AIVerificationError("every attempt failed verification")


def advice_facts(stats: dict) -> dict:
    """The only data Gemini ever sees for study advice: aggregates, no question text."""

    def row(r: dict) -> dict:
        return {
            "name": r["key"],
            "attempted": r["attempted"],
            "accuracy_pct": round(r["accuracy"] * 100),
            "avg_seconds": r["avg_time_seconds"],
        }

    o = stats["overall"]
    return {
        "overall": {
            "attempted": o["attempted"],
            "skipped": o["skipped"],
            "accuracy_pct": round(o["accuracy"] * 100),
            "avg_seconds": o["avg_time_seconds"],
        },
        "by_type": [row(r) for r in stats["by_subtype"]],
        "by_difficulty": [row(r) for r in stats["by_difficulty"]],
        "weak_types": [r["key"] for r in stats["weak_topics"]],
    }


def allowed_percents(facts: dict) -> set[int]:
    values = {0, 100, facts["overall"]["accuracy_pct"]}
    values.update(r["accuracy_pct"] for r in facts["by_type"])
    values.update(r["accuracy_pct"] for r in facts["by_difficulty"])
    return values


def build_advice_prompt(facts: dict) -> str:
    return f"""You are a supportive aptitude coach for Indian competitive exams (GATE, SSC CGL).
Here are a learner's practice statistics as JSON. Percentages are whole numbers.
{json.dumps(facts, indent=1)}

Write short, practical study advice based ONLY on these statistics.
Rules:
- Start with one sentence summarising how they are doing.
- Then give exactly 3 concrete actions, each at most 25 words, naming specific question types from the data (in plain words, e.g. "successive change").
- You may suggest a method (for example fractions, multipliers, or measuring against the original value) but never claim to know which specific mistakes the learner made.
- Only quote percentages that appear in the statistics. Do not state target percentages.
- Be encouraging and plain-spoken. Stay on topic.
Reply with JSON only, in this exact shape:
{{"summary": "<one sentence>", "actions": ["<action 1>", "<action 2>", "<action 3>"]}}"""


_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent\b)", re.IGNORECASE)


def parse_advice(raw: str, allowed: set[int]) -> dict:
    """Accept the reply only if it is well-formed and quotes no percentage we did not provide."""
    try:
        data = json.loads(raw)
        summary = str(data["summary"]).strip()
        raw_actions = data["actions"]
        if not isinstance(raw_actions, list):
            raise TypeError("actions must be a list")
        actions = [str(a).strip() for a in raw_actions]
    except (ValueError, KeyError, TypeError) as exc:
        raise AIVerificationError(f"malformed reply: {exc!r}") from exc
    if not summary or not 1 <= len(actions) <= 5 or any(not a for a in actions):
        raise AIVerificationError("advice has the wrong shape")
    for number in _PERCENT.findall(" ".join([summary, *actions])):
        if float(number) not in allowed:
            raise AIVerificationError(f"invented percentage: {number}%")
    return {"summary": summary, "actions": actions}