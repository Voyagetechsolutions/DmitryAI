# shared/contracts/dmitry.py
"""Dmitry service contracts - exact schema Platform expects."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class EntityContext(BaseModel):
    """Entity context for advice request."""
    type: str
    id: str
    name: Optional[str] = None
    attributes: Dict = Field(default_factory=dict)


class RecommendedAction(BaseModel):
    """Action recommendation from Dmitry."""
    action_type: str
    target_type: str
    target_id: str
    target_name: Optional[str] = None
    reason: str
    confidence: float = Field(ge=0, le=1)
    evidence_refs: List[str]
    blast_radius: str  # low, medium, high, critical
    priority: int = Field(ge=1, le=10, default=5)


class RiskFactorExplanation(BaseModel):
    """Explanation of a risk factor."""
    factor: str
    severity: str
    description: str
    evidence: List[str]


class AdviseRequest(BaseModel):
    """Request for Dmitry to provide advice on a finding."""
    finding_id: str
    tenant_id: str
    entity: EntityContext
    severity: str
    risk_score: float
    exposure_paths: List[dict]
    evidence_refs: List[str]
    policy_context: Dict = Field(default_factory=dict)


class AdviseResponse(BaseModel):
    """Dmitry's advice response."""
    summary: str
    risk_factors: List[RiskFactorExplanation]
    impact_analysis: str
    recommended_actions: List[RecommendedAction]
    evidence_chain: List[dict]
    confidence: float = Field(ge=0, le=1)
    citations: List[str]
    processing_time_ms: int


class ChatRequest(BaseModel):
    """Chat request to Dmitry."""
    message: str
    context: Dict
    tenant_id: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response from Dmitry."""
    response: str
    sources: List[str]
    conversation_id: str
    follow_up_questions: Optional[List[str]] = None
