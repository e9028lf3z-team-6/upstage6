import os
from pathlib import Path
from typing import Tuple

import httpx
from pypdf import PdfReader
from docx import Document as DocxDocument

from backend.app.core.settings import get_settings

SUPPORTED_EXT = {".pdf", ".docx", ".txt", ".md"}

class DocumentParser:
    """Extract text from uploaded documents.

    Priority:
    1) Upstage Document Parse (if UPSTAGE_API_KEY provided)
    2) Local extractors (PDF via pypdf, DOCX via python-docx)
    """

    async def extract_text(self, file_path: str, content_type: str | None = None) -> Tuple[str, dict]:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXT:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {sorted(SUPPORTED_EXT)}")

        settings = get_settings()
        if settings.upstage_api_key:
            try:
                text, meta = await self._extract_with_upstage(path)
                if text and text.strip():
                    return text, {"method": "upstage_document_parse", **meta}
            except Exception as e:
                # fall back silently; expose error in meta
                pass

        # fallback local
        if ext == ".pdf":
            return self._extract_pdf(path), {"method": "local_pypdf"}
        if ext == ".docx":
            return self._extract_docx(path), {"method": "local_docx"}
        return path.read_text(encoding="utf-8", errors="ignore"), {"method": "local_text"}

    async def _extract_with_upstage(self, path: Path) -> Tuple[str, dict]:
        settings = get_settings()
        url = settings.upstage_base_url.rstrip("/") + settings.upstage_document_parse_endpoint
        headers = {"Authorization": f"Bearer {settings.upstage_api_key}"}

        # Upstage Document Parse is a multipart upload. Response shape may vary by API version.
        async with httpx.AsyncClient(timeout=120.0) as client:
            with path.open("rb") as f:
                files = {"document": (path.name, f, "application/octet-stream")}
                resp = await client.post(url, headers=headers, files=files)
                resp.raise_for_status()
                data = resp.json()

        # Best-effort extraction of text fields.
        # Common patterns: {"text": "..."} or {"content": {"text": "..."}} or pages.
        text = ""
        if isinstance(data, dict):
            if isinstance(data.get("text"), str):
                text = data["text"]
            elif isinstance(data.get("content"), dict) and isinstance(data["content"].get("text"), str):
                text = data["content"]["text"]
            elif isinstance(data.get("pages"), list):
                parts = []
                for p in data["pages"]:
                    if isinstance(p, dict) and isinstance(p.get("text"), str):
                        parts.append(p["text"])
                text = "\n".join(parts)

        return text, {"upstage_raw_keys": list(data.keys()) if isinstance(data, dict) else []}

    def _extract_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()

    def _extract_docx(self, path: Path) -> str:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs).strip()

document_parser = DocumentParser()
