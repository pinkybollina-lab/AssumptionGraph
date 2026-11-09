
from typing import Optional

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    department: str
    speaker: Optional[str] = None
    source_type: str = "text"
    language: str = "en-IN"
    transcript: str = Field(min_length=5)


class AssumptionCreate(BaseModel):
    source_id: Optional[int] = None
    department: str
    subject: str
    metric: str
    value: str
    unit: Optional[str] = None
    period: Optional[str] = None
    assumption_type: str = "forecast"
    owner: Optional[str] = None
    extraction_confidence: float = Field(default=0.5, ge=0, le=1)
    speaker_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    evidence: str
    review_status: str = "pending"


class AssumptionResponse(AssumptionCreate):
    id: int

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    assumption_id: int
    new_value: str

class DependencyCreate(BaseModel):
    prerequisite_assumption_id: int
    dependent_assumption_id: int
    rationale: str = Field(min_length=5)
class FindingStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
