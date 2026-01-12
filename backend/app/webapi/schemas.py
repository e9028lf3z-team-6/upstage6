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

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentOut):
    extracted_text: str


# -------------------------
# Analysis
# -------------------------
class AnalysisOut(BaseModel):
    id: str
    document_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisDetail(AnalysisOut):
    result: Dict[str, Any]
