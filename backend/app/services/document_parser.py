import zipfile
import zlib
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Dict, Any

import httpx
try:
    import olefile
except ImportError:
    olefile = None

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.settings import get_settings


SUPPORTED_EXT = {".pdf", ".docx", ".txt", ".md", ".hwp", ".hwpx"}


class DocumentParser:
    """
    Document → text + context meta extractor

    Priority:
    1) Upstage Document Parse (if API key present)
    2) Local extractors (PDF / DOCX / HWP / HWPX)
    """

    async def extract_text(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXT:
            raise ValueError(f"Unsupported file type: {ext}")

        settings = get_settings()

        # ------------------------------
        # 1) Upstage Document Parse
        # ------------------------------
        if settings.upstage_api_key:
            try:
                text, meta = await self._extract_with_upstage(path)
                if text and text.strip():
                    return text, {
                        "source": "upstage_document_parse",
                        "file_name": path.name,
                        "file_type": ext,
                        **meta,
                    }
            except Exception as e:
                upstage_error = str(e)
        else:
            upstage_error = None

        # ------------------------------
        # 2) Local fallback
        # ------------------------------
        if ext == ".pdf":
            text = self._extract_pdf(path)
            method = "local_pypdf"
        elif ext == ".docx":
            text = self._extract_docx(path)
            method = "local_docx"
        elif ext == ".hwp":
            text = self._extract_hwp(path)
            method = "local_hwp"
        elif ext == ".hwpx":
            text = self._extract_hwpx(path)
            method = "local_hwpx"
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            method = "local_text"

        return text, {
            "source": method,
            "file_name": path.name,
            "file_type": ext,
            "upstage_error": upstage_error,
        }

    # --------------------------------------------------
    # Upstage
    # --------------------------------------------------
    async def _extract_with_upstage(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        settings = get_settings()
        url = settings.upstage_base_url.rstrip("/") + settings.upstage_document_parse_endpoint
        headers = {"Authorization": f"Bearer {settings.upstage_api_key}"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            with path.open("rb") as f:
                files = {"document": (path.name, f, "application/octet-stream")}
                resp = await client.post(url, headers=headers, files=files)
                resp.raise_for_status()
                data = resp.json()

        text = ""
        if isinstance(data, dict):
            if isinstance(data.get("text"), str):
                text = data["text"]
            elif isinstance(data.get("content"), dict) and isinstance(data["content"].get("text"), str):
                text = data["content"]["text"]
            elif isinstance(data.get("pages"), list):
                text = "\n".join(
                    p.get("text", "") for p in data["pages"] if isinstance(p, dict)
                )

        return text, {
            "upstage_raw_keys": list(data.keys()) if isinstance(data, dict) else [],
        }

    # --------------------------------------------------
    # Local extractors
    # --------------------------------------------------
    def _extract_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    def _extract_docx(self, path: Path) -> str:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs).strip()

    def _extract_hwpx(self, path: Path) -> str:
        text_parts = []
        try:
            with zipfile.ZipFile(path, "r") as zf:
                section_files = sorted(
                    [n for n in zf.namelist() if n.startswith("Contents/section") and n.endswith(".xml")],
                    key=lambda x: int("".join(filter(str.isdigit, x)) or 0),
                )
                for sec in section_files:
                    with zf.open(sec) as f:
                        root = ET.parse(f).getroot()
                        for elem in root.iter():
                            if elem.tag.endswith("t") and elem.text:
                                text_parts.append(elem.text)
                            if elem.tag.endswith("p"):
                                text_parts.append("\n")
        except Exception as e:
            return f"[Error parsing HWPX: {e}]"

        return "".join(text_parts).strip()

    def _extract_hwp(self, path: Path) -> str:
        if not olefile:
            return "[Error: olefile not installed]"

        text_parts = []
        try:
            if not olefile.isOleFile(path):
                return "[Error: invalid HWP file]"

            with olefile.OleFileIO(path) as ole:
                sections = sorted(
                    [d for d in ole.listdir() if d[0] == "BodyText" and d[1].startswith("Section")],
                    key=lambda x: int("".join(filter(str.isdigit, x[1])) or 0),
                )

                for sec in sections:
                    data = ole.openstream(sec).read()
                    try:
                        data = zlib.decompress(data, -15)
                    except Exception:
                        pass

                    cursor = 0
                    size = len(data)
                    while cursor + 4 <= size:
                        header = struct.unpack("<I", data[cursor:cursor+4])[0]
                        tag_id = header & 0x3FF
                        rec_size = (header >> 20) & 0xFFF
                        cursor += 4

                        if rec_size == 0xFFF and cursor + 4 <= size:
                            rec_size = struct.unpack("<I", data[cursor:cursor+4])[0]
                            cursor += 4

                        if cursor + rec_size > size:
                            break

                        if tag_id == 67:  # PARA_TEXT
                            payload = data[cursor:cursor+rec_size]
                            try:
                                t = payload.decode("utf-16le", errors="ignore")
                                t = t.replace("\u0000", "").replace("\u000b", "\n")
                                text_parts.append(t)
                                text_parts.append("\n")
                            except Exception:
                                pass

                        cursor += rec_size

        except Exception as e:
            return f"[Error parsing HWP: {e}]"

        return "".join(text_parts).strip()


document_parser = DocumentParser()
