"""Pydantic models for job applications."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ApplicationState(str, Enum):
    """Application lifecycle states."""
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    SUBMITTING = "submitting"
    PENDING_VERIFICATION = "pending_verification"
    SUBMITTED = "submitted"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class FieldSource(str, Enum):
    """Source of the field value."""
    PROFILE = "profile"      # From user's stored profile
    CACHED = "cached"        # From cached responses
    AI = "ai"                # AI-generated
    MANUAL = "manual"        # User-provided during review


class FieldType(str, Enum):
    """Form field types."""
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    REACT_SELECT = "react_select"
    FILE = "file"
    CHECKBOX = "checkbox"
    RADIO = "radio"


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    """Request to analyze a job application form."""
    job_id: str
    auto_submit: bool = False


class SubmitRequest(BaseModel):
    """Request to submit an analyzed application."""
    field_overrides: dict[str, str] = Field(default_factory=dict)
    save_responses: bool = True
    idempotency_key: str | None = None


class VerifyRequest(BaseModel):
    """Request to provide email verification code."""
    code: str = Field(..., min_length=8, max_length=8, description="8-digit verification code")


class VerifyResponse(BaseModel):
    """Response from verify endpoint."""
    application_id: str
    status: str
    message: str
    submitted_at: datetime | None = None
    error: str | None = None
    expires_in_seconds: int | None = None


# --- Response Models ---

class FormFieldAnalysis(BaseModel):
    """Field with AI analysis - returned to frontend."""
    field_id: str
    label: str
    field_type: FieldType
    required: bool = False
    options: list[str] | None = None
    recommended_value: str | None = None
    reasoning: str | None = None
    source: FieldSource = FieldSource.MANUAL
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    editable: bool = True


class JobInfo(BaseModel):
    """Job information for response."""
    id: str
    title: str
    company_name: str
    url: str


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""
    application_id: str
    status: str
    expires_at: datetime
    ttl_seconds: int
    job: JobInfo
    fields: list[FormFieldAnalysis]
    form_fingerprint: str


class SubmitResponse(BaseModel):
    """Response from submit endpoint."""
    application_id: str
    status: str
    message: str
    submitted_at: datetime | None = None
    error: str | None = None


class ApplicationStatusResponse(BaseModel):
    """Response for application status check."""
    application_id: str
    user_id: str
    job_id: str
    job_title: str
    company_name: str
    status: ApplicationState
    fields: list[FormFieldAnalysis] | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    expires_at: datetime | None = None
    error: str | None = None


# --- Storage Models ---

class FormFieldStored(BaseModel):
    """Field as stored in MongoDB."""
    field_id: str
    selector: str  # CSS selector
    label: str
    field_type: FieldType
    required: bool = False
    options: list[str] | None = None
    recommended_value: str | None = None
    final_value: str | None = None
    source: FieldSource = FieldSource.MANUAL
    confidence: float = 0.0
    reasoning: str | None = None


class ApplicationDocument(BaseModel):
    """Full application document as stored in MongoDB."""
    id: str | None = Field(alias="_id", default=None)
    user_id: str
    job_id: str
    job_url: str
    job_title: str
    company_name: str
    status: ApplicationState
    auto_submit: bool = False
    form_fingerprint: str | None = None
    fields: list[FormFieldStored] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    submitted_at: datetime | None = None
    error: str | None = None
    idempotency_key: str | None = None

    class Config:
        populate_by_name = True


# --- Cached Response Models ---

class CachedAnswer(BaseModel):
    """A cached answer for a custom question."""
    question_text: str
    answer: str
    last_used: datetime
    use_count: int = 1


class UserCachedResponses(BaseModel):
    """Cached form responses for a user."""
    standard: dict[str, str] = Field(default_factory=dict)
    custom: dict[str, CachedAnswer] = Field(default_factory=dict)
