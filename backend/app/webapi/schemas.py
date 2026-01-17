from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


# -------------------------
# Document
# -------------------------
class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    content_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentOut):
    extracted_text: str
    meta_json: str


# -------------------------
# Analysis
# -------------------------
class AnalysisOut(BaseModel):
    id: str
    document_id: str
    status: str
    decision: str | None = None
    has_issues: bool | None = None
    issue_counts: Dict[str, int] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisDetail(AnalysisOut):
    result: Dict[str, Any]
