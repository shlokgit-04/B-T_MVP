from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User input message")


class ExtractedEntity(BaseModel):
    field: str
    value: Any
    source: str = "extracted"


class ParsedEntry(BaseModel):
    entry_type: Optional[str] = None
    confidence: float = 0.0
    extracted: Dict[str, Any] = Field(default_factory=dict)
    entities: List[ExtractedEntity] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    status: str
    entry_type: Optional[str] = None
    message: str
    extracted: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    current_question: Optional[str] = None
    progress: int = 0
    confidence: float = 0.0
    entities: List[ExtractedEntity] = Field(default_factory=list)
    summary: Optional[str] = None


class SessionState(BaseModel):
    session_id: str
    entry_type: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    completed: bool = False
    saved: bool = False
    confirmation_pending: bool = False


class SaveEntry(BaseModel):
    session_id: str
    entry_type: str
    data: Dict[str, Any]


class SessionResponse(BaseModel):
    session_id: str
    state: SessionState
