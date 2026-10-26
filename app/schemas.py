"""Request and response models."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=50)
    message: str = Field(min_length=1, max_length=5000)
    source: str = Field(default="website", max_length=100)


class ScoreResult(BaseModel):
    """What the scoring step must return, whether from the LLM or the fallback."""

    is_spam: bool
    score: int = Field(ge=0, le=10)
    intent: str = Field(max_length=200)
    summary: str
    suggested_reply: str


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    message: str
    source: str
    is_spam: bool
    score: int
    intent: str
    summary: str
    suggested_reply: str
    scored_by: str
    crm_status: str
    crm_id: str
    created_at: datetime
