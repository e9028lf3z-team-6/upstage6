from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    content_type: str
    created_at: str

class DocumentDetail(DocumentOut):
    extracted_text: str

class AnalysisOut(BaseModel):
    id: str
    document_id: str
    status: str
    created_at: str

class AnalysisDetail(AnalysisOut):
    result: dict
