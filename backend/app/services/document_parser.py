import os
import zipfile
import zlib
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

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
    """Extract text from uploaded documents.

    Priority:
    1) Upstage Document Parse (if UPSTAGE_API_KEY provided)
    2) Local extractors (PDF via pypdf, DOCX via python-docx, HWP via olefile, HWPX via zipfile)
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
        if ext == ".hwp":
            return self._extract_hwp(path), {"method": "local_hwp"}
        if ext == ".hwpx":
            return self._extract_hwpx(path), {"method": "local_hwpx"}
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

    def _extract_hwpx(self, path: Path) -> str:
        """Extract text from HWPX (zip-based XML)."""
        text_parts = []
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                # Find section XMLs
                section_files = [n for n in zf.namelist() if n.startswith("Contents/section") and n.endswith(".xml")]
                # Sort by number to maintain order
                section_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

                for sec in section_files:
                    with zf.open(sec) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        # HWPX text is usually in <hp:t> tags
                        # Namespace handling might be tricky, so we iterate all elements
                        for elem in root.iter():
                            if elem.tag.endswith('t') and elem.text:
                                text_parts.append(elem.text)
                            # Add newlines for paragraph breaks (hp:p)
                            if elem.tag.endswith('p'):
                                text_parts.append("\n")
        except Exception as e:
            return f"[Error parsing HWPX: {e}]"
        
        return "".join(text_parts).strip()

    def _extract_hwp(self, path: Path) -> str:
        """Extract text from HWP (OLE-based binary). Improved implementation parsing HWP records."""
        if not olefile:
            return "[Error: 'olefile' library not installed. Cannot parse .hwp locally.]"
        
        text_parts = []
        try:
            if not olefile.isOleFile(path):
                return "[Error: Not a valid HWP file]"
            
            with olefile.OleFileIO(path) as ole:
                dirs = ole.listdir()
                # Find BodyText sections
                sections = []
                for d in dirs:
                    if d[0] == "BodyText" and d[1].startswith("Section"):
                        sections.append(d)
                
                # Sort sections
                sections.sort(key=lambda x: int(''.join(filter(str.isdigit, x[1])) or 0))

                for sec in sections:
                    stream = ole.openstream(sec)
                    data = stream.read()
                    
                    # Decompress (Deflate)
                    try:
                        decompressed = zlib.decompress(data, -15)
                    except:
                        decompressed = data
                    
                    # Parse HWP Records
                    # Record Header: 4 bytes (Tag: 10 bits, Level: 10 bits, Size: 12 bits)
                    cursor = 0
                    size = len(decompressed)
                    while cursor < size:
                        if cursor + 4 > size:
                            break
                        
                        header = struct.unpack('<I', decompressed[cursor:cursor+4])[0]
                        tag_id = header & 0x3FF
                        # level = (header >> 10) & 0x3FF
                        rec_size = (header >> 20) & 0xFFF
                        
                        if rec_size == 0xFFF: # Size > 4095 bytes
                            if cursor + 8 > size: break
                            rec_size = struct.unpack('<I', decompressed[cursor+4:cursor+8])[0]
                            cursor += 8
                        else:
                            cursor += 4
                        
                        if cursor + rec_size > size:
                            break

                        # HWPTAG_PARA_TEXT = 67
                        if tag_id == 67:
                            payload = decompressed[cursor:cursor+rec_size]
                            # HWP text is UTF-16LE. 
                            # It may contain control characters (e.g. inline images, fields) which we should strip.
                            # But simple decoding is much better than nothing.
                            try:
                                # Replace null characters or other binary artifacts
                                t = payload.decode('utf-16le', errors='ignore')
                                # Filter out HWP control chars (usually high-byte unicode or specific ranges)
                                # Basic cleanup:
                                t = t.replace('\u0000', '').replace('\u0001', '').replace('\u0002', '') \
                                     .replace('\u0003', '').replace('\u000b', '\n').replace('\r\n', '\n')
                                text_parts.append(t)
                                text_parts.append("\n") # Paragraph break
                            except:
                                pass
                        
                        cursor += rec_size

        except Exception as e:
            return f"[Error parsing HWP: {e}]"

        return "".join(text_parts).strip()

document_parser = DocumentParser()
