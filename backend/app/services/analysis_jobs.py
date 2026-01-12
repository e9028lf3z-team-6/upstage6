import asyncio
import json
from typing import Any

from rq import get_current_job

from app.core.db import get_session, Document, Analysis
from app.services.analysis_runner import run_analysis_for_text


def _issue_count(result: dict | None) -> int:
    if not result:
        return 0
    issues = result.get("issues", [])
    return len(issues) if isinstance(issues, list) else 0


def _collect_issue_counts(result: dict) -> dict:
    return {
        "tone": _issue_count(result.get("tone")),
        "logic": _issue_count(result.get("logic")),
        "trauma": _issue_count(result.get("trauma")),
        "hate_bias": _issue_count(result.get("hate_bias")),
        "genre_cliche": _issue_count(result.get("genre_cliche")),
        "spelling": _issue_count(result.get("spelling")),
    }


def _is_fallback(result: dict) -> bool:
    report = result.get("final_report") or {}
    if isinstance(report, dict) and isinstance(report.get("note"), str):
        return "LLM 미사용" in report.get("note")
    return False


async def run_analysis_job_async(analysis_id: str, doc_id: str) -> None:
    job = get_current_job()
    if job:
        job.meta["progress"] = 5
        job.save_meta()

    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            return
        analysis = await session.get(Analysis, analysis_id)
        if not analysis:
            return
        analysis.status = "running"
        await session.commit()

    try:
        if job:
            job.meta["progress"] = 20
            job.save_meta()
        result = await run_analysis_for_text(doc.extracted_text, context=doc.meta_json)
        status = "fallback" if _is_fallback(result) else "done"
    except Exception as exc:
        result = {"error": str(exc), "note": "analysis execution failed"}
        status = "failed"

    decision = result.get("decision")
    issue_counts = _collect_issue_counts(result)
    has_issues = any(v > 0 for v in issue_counts.values())

    async with get_session() as session:
        analysis = await session.get(Analysis, analysis_id)
        if not analysis:
            return
        analysis.status = status
        analysis.decision = decision
        analysis.has_issues = has_issues
        analysis.issue_counts_json = json.dumps(issue_counts, ensure_ascii=False)
        analysis.result_json = json.dumps(result, ensure_ascii=False)
        await session.commit()

    if job:
        job.meta["progress"] = 100
        job.save_meta()


def run_analysis_job(analysis_id: str, doc_id: str) -> None:
    asyncio.run(run_analysis_job_async(analysis_id, doc_id))
