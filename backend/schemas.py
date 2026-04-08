"""
schemas.py
==========
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────
class PredictionLabel(str, Enum):
    FAKE = "FAKE"
    REAL = "REAL"
    UNKNOWN = "UNKNOWN"


class CredibilityLevel(str, Enum):
    HIGHLY_CREDIBLE = "Highly Credible"
    LIKELY_CREDIBLE = "Likely Credible"
    UNCERTAIN = "Uncertain"
    LIKELY_FAKE = "Likely Fake"
    HIGHLY_SUSPICIOUS = "Highly Suspicious"


# ─── Request Models ──────────────────────────────────────────────────────────
class TextPredictionRequest(BaseModel):
    """Request body for text-based prediction."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="News article text to analyze",
        examples=["Scientists discover new breakthrough in cancer research at MIT"]
    )
    language: Optional[str] = Field(
        None,
        description="Language code (e.g., 'en', 'hi'). Auto-detected if not provided."
    )


class URLPredictionRequest(BaseModel):
    """Request body for URL-based prediction."""
    url: str = Field(
        ...,
        description="URL of the news article to analyze",
        examples=["https://example.com/news/article"]
    )


# ─── Response Models ─────────────────────────────────────────────────────────
class SuspiciousWord(BaseModel):
    """A word/feature contributing to the prediction."""
    word: str
    importance: float
    direction: str  # "fake" or "real"
    tfidf_score: float


class PredictionResponse(BaseModel):
    """Response for a news prediction."""
    prediction: str = Field(..., description="FAKE or REAL")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage")
    credibility_score: int = Field(..., ge=0, le=100, description="Credibility score (0-100)")
    credibility_level: str = Field(..., description="Human-readable credibility level")
    credibility_color: str = Field(..., description="Color code for UI display")
    fake_probability: float = Field(..., ge=0, le=100)
    real_probability: float = Field(..., ge=0, le=100)
    suspicious_words: List[SuspiciousWord] = Field(default_factory=list)
    text_length: int = Field(..., description="Length of analyzed text")
    source_url: Optional[str] = Field(None, description="Source URL if analyzed from URL")
    analyzed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    analysis_id: Optional[str] = Field(None, description="Unique ID for this analysis")


class URLPredictionResponse(PredictionResponse):
    """Extended response for URL-based predictions."""
    extracted_title: Optional[str] = None
    extracted_text_length: int = 0
    source_domain: Optional[str] = None


class HistoryItem(BaseModel):
    """A historical analysis record."""
    id: str
    text_preview: str
    prediction: str
    confidence: float
    credibility_score: int
    credibility_level: str
    source_url: Optional[str] = None
    analyzed_at: str


class HistoryResponse(BaseModel):
    """Response containing analysis history."""
    total: int
    items: List[HistoryItem]


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_analyzed: int
    fake_count: int
    real_count: int
    average_credibility: float
    recent_analyses: List[HistoryItem]


class NewsArticle(BaseModel):
    """A monitored news article."""
    title: str
    description: Optional[str] = None
    url: str
    source: str
    published_at: Optional[str] = None
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    credibility_score: Optional[int] = None


class MonitorResponse(BaseModel):
    """Response for real-time news monitoring."""
    articles: List[NewsArticle]
    analyzed_count: int
    fake_count: int
    real_count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model_loaded: bool
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
