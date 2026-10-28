from fastapi import APIRouter

from app.domain.enums import ExamType
from app.domain.profiles import ExamProfile, PROFILES, get_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ExamProfile])
async def list_profiles() -> list[ExamProfile]:
    return list(PROFILES.values())


@router.get("/{exam}", response_model=ExamProfile)
async def read_profile(exam: ExamType) -> ExamProfile:
    return get_profile(exam)