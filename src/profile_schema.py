from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CareerStage(str, Enum):
    student_no_experience = "student_no_experience"
    student_with_experience = "student_with_experience"
    graduate_seeking_first_role = "graduate_seeking_first_role"
    experienced_switching = "experienced_switching"


class LanguageLevel(BaseModel):
    language: str
    level: str  # e.g. "A2", "B1", "Fluent", "Native"


class Profile(BaseModel):
    # --- extracted from CV, high confidence ---
    name: str
    email: str
    location: str
    years_experience: float
    highest_degree: str
    degree_status: str  # "completed" | "in_progress" | "expected_<date>"
    current_role_type: Optional[str] = None  # last job title/type, if any
    languages: list[LanguageLevel] = Field(default_factory=list)

    # --- classification ---
    career_stage: Optional[CareerStage] = None
    career_stage_confidence: float = 0.0  # 0-1, low triggers clarifying Qs

    # --- from clarifying questions, may be None until answered ---
    target_roles: list[str] = Field(default_factory=list)
    target_location: Optional[str] = None
    availability: Optional[str] = None  # e.g. "immediate", "from 10/2026"
    salary_floor_eur: Optional[int] = None
    must_haves: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True