import json
import os
import hashlib
import statistics
import time
from typing import Any, Dict, Tuple

from sqlalchemy import select
from app.core.db import Document, EvalRun, get_session
from app.llm.client import get_upstage_client
from app.llm.chat import chat
from app.services.analysis_runner import run_analysis_for_text
from app.agents.evaluators.tone_evaluator import ToneQualityAgent
from app.agents.evaluators.causality_evaluator import CausalityQualityAgent
from app.agents.evaluators.trauma_evaluator import TraumaQualityAgent
from app.agents.evaluators.hatebias_evaluator import HateBiasQualityAgent
from app.agents.evaluators.cliche_evaluator import GenreClicheQualityAgent
from app.agents.evaluators.spelling_evaluator import SpellingQualityAgent
from app.agents.evaluators.final_evaluator import FinalEvaluatorAgent


def _truncate_report(text: str) -> str:
    max_chars = int(os.getenv("REPORT_MAX_CHARS", "2000"))
    return text[:max_chars]


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}


def _extract_json_block(text: str) -> str | None:
    if not text:
        return None
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            candidate = parts[1].strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def perform_eval(outputs: dict) -> dict:
    report = outputs.get("report") or outputs.get("final_report") or {}
    decision = outputs.get("decision")
    has_report = isinstance(report, dict) and bool(report)
    decision_ok = decision in ("pass", "rewrite")
    report_markdown = report.get("full_report_markdown", "") if isinstance(report, dict) else ""
    report_len = len(report_markdown) if isinstance(report_markdown, str) else 0
    report_len_ok = report_len >= 200
    score = 1 if (has_report and decision_ok and report_len_ok) else 0
    return {
        "schema_ok": score,
        "schema_ok_details": {
            "has_report": has_report,
            "decision_ok": decision_ok,
            "report_len": report_len,
            "report_len_ok": report_len_ok,
        },
    }


def _issue_count(result: dict | None) -> int:
    if not result:
        return 0
    issues = result.get("issues", [])
    return len(issues) if isinstance(issues, list) else 0


def _issue_total(issue_counts: dict) -> int:
    total = 0
    for value in issue_counts.values():
        if isinstance(value, int):
            total += value
    return total


def collect_metrics(outputs: dict) -> dict:
    report = outputs.get("report") or outputs.get("final_report") or {}
    report_markdown = report.get("full_report_markdown", "") if isinstance(report, dict) else ""
    logic_result = outputs.get("logic") or outputs.get("causality")
    issue_counts = {
        "tone": _issue_count(outputs.get("tone")),
        "logic": _issue_count(logic_result),
        "trauma": _issue_count(outputs.get("trauma")),
        "hate_bias": _issue_count(outputs.get("hate_bias")),
        "genre_cliche": _issue_count(outputs.get("genre_cliche")),
        "spelling": _issue_count(outputs.get("spelling")),
    }
    total_issues = _issue_total(issue_counts)
    report_length = len(report_markdown) if isinstance(report_markdown, str) else 0
    issue_density_per_1k = (total_issues / report_length * 1000.0) if report_length else 0.0
    dominant_issue = None
    dominant_count = 0
    for key, value in issue_counts.items():
        if isinstance(value, int) and value > dominant_count:
            dominant_issue = key
            dominant_count = value
    dominant_issue_strength = (dominant_count / total_issues) if total_issues else 0.0
    issue_values = [v for v in issue_counts.values() if isinstance(v, int)]
    agent_disagreement = (
        statistics.pstdev(issue_values) if len(issue_values) > 1 else 0.0
    )
    return {
        "decision": outputs.get("decision"),
        "has_issues": any(v > 0 for v in issue_counts.values()),
        "issue_counts": issue_counts,
        "report_length": report_length,
        "total_issues": total_issues,
        "issue_density_per_1k": round(issue_density_per_1k, 4),
        "dominant_issue": dominant_issue,
        "dominant_issue_strength": round(dominant_issue_strength, 4),
        "agent_disagreement": round(agent_disagreement, 4),
    }

def collect_agent_metrics(
    outputs: dict,
    source_text: str | None,
) -> Tuple[dict, dict]:
    tone_quality = ToneQualityAgent()
    causality_quality = CausalityQualityAgent()
    trauma_quality = TraumaQualityAgent()
    hate_quality = HateBiasQualityAgent()
    cliche_quality = GenreClicheQualityAgent()
    spelling_quality = SpellingQualityAgent()
    final_evaluator = FinalEvaluatorAgent()

    tone_result = outputs.get("tone") or {}
    logic_result = outputs.get("logic") or outputs.get("causality") or {}
    trauma_result = outputs.get("trauma") or {}
    hate_result = outputs.get("hate_bias") or {}
    cliche_result = outputs.get("genre_cliche") or {}
    spelling_result = outputs.get("spelling") or {}
    persona_feedback = outputs.get("persona_feedback")
    if persona_feedback is None:
        debug_payload = outputs.get("debug") or {}
        persona_feedback = debug_payload.get("persona_feedback")
    aggregated = outputs.get("aggregated") or outputs.get("aggregate") or {}

    latencies_ms: dict[str, float] = {}
    text = source_text or ""

    def _safe_eval(
        agent,
        name: str,
        *args,
        expect_score: bool = False,
        **kwargs,
    ) -> dict:
        start = time.perf_counter()
        result: dict = {}
        try:
            result = agent.run(*args, **kwargs)
            if not isinstance(result, dict):
                result = {}
        except Exception as exc:
            result = {"error": str(exc)}
        if expect_score and "score" not in result:
            result["score"] = 0
        latencies_ms[name] = round((time.perf_counter() - start) * 1000.0, 2)
        return result

    metrics = {
        "tone": _safe_eval(tone_quality, "tone", text, tone_result, expect_score=True),
        "logic": _safe_eval(causality_quality, "logic", text, logic_result, expect_score=True),
        "trauma": _safe_eval(trauma_quality, "trauma", text, trauma_result, expect_score=True),
        "hate_bias": _safe_eval(hate_quality, "hate_bias", text, hate_result, expect_score=True),
        "genre_cliche": _safe_eval(cliche_quality, "genre_cliche", text, cliche_result, expect_score=True),
        "spelling": _safe_eval(spelling_quality, "spelling", text, spelling_result, expect_score=True),
    }

    metrics["final"] = _safe_eval(
        final_evaluator,
        "final",
        aggregate=aggregated,
        tone_issues=tone_result.get("issues", []),
        logic_issues=logic_result.get("issues", []),
        trauma_issues=trauma_result.get("issues", []),
        hate_issues=hate_result.get("issues", []),
        cliche_issues=cliche_result.get("issues", []),
        persona_feedback=persona_feedback,
    )

    return metrics, latencies_ms


async def fetch_latest_eval_run() -> EvalRun | None:
    async with get_session() as session:
        res = await session.execute(
            select(EvalRun)
            .order_by(EvalRun.created_at.desc())
            .limit(1)
        )
        return res.scalars().first()


async def fetch_eval_history(limit: int = 10) -> list[EvalRun]:
    async with get_session() as session:
        res = await session.execute(
            select(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit)
        )
        return res.scalars().all()


def _safe_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def compute_history_stats(runs: list[EvalRun]) -> dict:
    if not runs:
        return {}
    totals = []
    llm_scores = []
    schema_scores = []
    quality_scores = []
    per_issue: dict[str, list[float]] = {}
    for run in runs:
        try:
            metrics = json.loads(run.metrics_json)
        except Exception:
            metrics = {}
        try:
            scores = json.loads(run.scores_json)
        except Exception:
            scores = {}
        total = _safe_number(metrics.get("total_issues"))
        if total is not None:
            totals.append(total)
        schema_score = _safe_number(scores.get("schema_ok"))
        if schema_score is not None:
            schema_scores.append(schema_score)
        quality_score = _safe_number(scores.get("quality_score_v2"))
        if quality_score is not None:
            quality_scores.append(quality_score)
        llm_status = scores.get("llm_judge_status")
        llm_score = _safe_number(scores.get("llm_judge_overall"))
        if llm_score is not None and llm_status in (None, "ok", "zero_score"):
            llm_scores.append(llm_score)
        issue_counts = metrics.get("issue_counts") or {}
        for key, value in issue_counts.items():
            num = _safe_number(value)
            if num is None:
                continue
            per_issue.setdefault(key, []).append(num)

    def _stats(values: list[float]) -> dict:
        if not values:
            return {}
        mean = statistics.mean(values)
        median = statistics.median(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": round(mean, 3), "median": round(median, 3), "std": round(std, 3)}

    return {
        "sample_size": len(runs),
        "total_issues": _stats(totals),
        "llm_judge_overall": _stats(llm_scores),
        "scores": {
            "quality_score_v2": _stats(quality_scores),
        },
        "issue_counts": {key: _stats(values) for key, values in per_issue.items()},
    }


def compute_consistency_score(input_hash: str | None, runs: list[EvalRun]) -> float | None:
    if not input_hash:
        return None
    totals = []
    for run in runs:
        try:
            meta = json.loads(run.meta_json)
        except Exception:
            meta = {}
        if meta.get("input_hash") != input_hash:
            continue
        try:
            metrics = json.loads(run.metrics_json)
        except Exception:
            metrics = {}
        total = _safe_number(metrics.get("total_issues"))
        if total is not None:
            totals.append(total)
    if len(totals) < 2:
        return None
    std = statistics.pstdev(totals)
    score = 1.0 / (1.0 + std)
    return round(score, 3)


def compute_eval_delta(
    current_metrics: dict, current_scores: dict, prev: EvalRun | None
) -> dict:
    if not prev:
        return {}

    try:
        prev_metrics = json.loads(prev.metrics_json)
    except Exception:
        prev_metrics = {}
    try:
        prev_scores = json.loads(prev.scores_json)
    except Exception:
        prev_scores = {}

    delta = {
        "issue_counts": {},
        "scores": {},
        "decision_changed": prev_metrics.get("decision") != current_metrics.get("decision"),
    }
    for key, value in (current_metrics.get("issue_counts") or {}).items():
        prev_val = (prev_metrics.get("issue_counts") or {}).get(key)
        if isinstance(value, int) and isinstance(prev_val, int):
            delta["issue_counts"][key] = value - prev_val
    for key in ["schema_ok", "llm_judge_overall"]:
        cur = current_scores.get(key)
        prev_val = prev_scores.get(key)
        if isinstance(cur, (int, float)) and isinstance(prev_val, (int, float)):
            delta["scores"][key] = cur - prev_val

    return delta


def llm_as_judge(outputs: dict) -> dict:
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        return {"llm_judge_status": "disabled", "llm_judge_error": "missing_api_key"}
    client = get_upstage_client()
    report = outputs.get("report") or outputs.get("final_report") or {}
    report_text = ""
    if isinstance(report, dict):
        report_text = report.get("full_report_markdown", "") or report.get("summary", "")
    report_text = _truncate_report(report_text)

    prompt = (
        "You are a strict evaluator. Score the report quality from 0 to 1.\n"
        "Criteria:\n"
        "- clarity\n"
        "- usefulness\n"
        "- consistency_with_decision\n"
        "- structure\n"
        "- actionability\n"
        "Return ONLY a JSON object on a single line. No markdown, no code fences.\n"
        "If uncertain, still return valid JSON with numeric scores.\n"
        "Required keys:\n"
        "{\n"
        "  \"clarity\": float,\n"
        "  \"usefulness\": float,\n"
        "  \"consistency_with_decision\": float,\n"
        "  \"structure\": float,\n"
        "  \"actionability\": float,\n"
        "  \"overall\": float,\n"
        "  \"rationale\": \"...\"\n"
        "}\n\n"
        f"Report:\n{report_text}\n"
    )
    model = os.getenv("JUDGE_MODEL", "solar-pro2")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.choices[0].message.content or ""
    except Exception as exc:
        return {
            "llm_judge_status": "request_failed",
            "llm_judge_error": str(exc),
        }

    content = content.strip()
    if not content:
        return {
            "llm_judge_status": "empty_response",
            "llm_judge_error": "empty_content",
        }

    data = _safe_json(content)
    if not data:
        extracted = _extract_json_block(content)
        if extracted:
            data = _safe_json(extracted)
    if not data:
        repair_prompt = (
            "You must return valid JSON only.\n"
            "Convert the following content into JSON with keys:\n"
            "{"
            "\"clarity\": float, \"usefulness\": float, "
            "\"consistency_with_decision\": float, \"structure\": float, "
            "\"actionability\": float, \"overall\": float, \"rationale\": \"...\""
            "}\n"
            "Use 0.0 if a value is missing.\n"
            f"Content:\n{content}\n"
        )
        try:
            repair_response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": repair_prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            repaired = repair_response.choices[0].message.content or ""
            data = _safe_json(repaired) or _safe_json(_extract_json_block(repaired) or "")
            if data:
                content = repaired
        except Exception:
            data = {}
        if not data:
            return {
                "llm_judge_status": "parse_failed",
                "llm_judge_error": "invalid_json",
                "llm_judge_raw": content[:1000],
            }

    def _score(key: str) -> float:
        try:
            return float(data.get(key, 0.0))
        except Exception:
            return 0.0

    result = {
        "llm_judge_clarity": _score("clarity"),
        "llm_judge_usefulness": _score("usefulness"),
        "llm_judge_consistency": _score("consistency_with_decision"),
        "llm_judge_structure": _score("structure"),
        "llm_judge_actionability": _score("actionability"),
        "llm_judge_overall": _score("overall"),
        "llm_judge_rationale": str(data.get("rationale", "")),
        "llm_judge_status": "ok",
        "llm_judge_error": "",
        "llm_judge_raw": content[:1000],
    }
    if result["llm_judge_overall"] == 0.0:
        result["llm_judge_status"] = "zero_score"
    return result


def translate_rationale(text: str) -> str:
    if not text:
        return ""
    system = "You are a professional translator. Return Korean only."
    prompt = f"다음 문장을 자연스러운 한국어로 번역해줘:\n{text}"
    try:
        response = chat(prompt, system=system, temperature=0.0)
        return response.strip()
    except Exception:
        return ""


def compute_quality_score(
    metrics: dict,
    scores: dict,
    agent_metrics: dict,
    consistency_score: float | None,
) -> dict:
    llm_overall = _safe_number(scores.get("llm_judge_overall")) or 0.0
    llm_status = scores.get("llm_judge_status")
    llm_parts = []
    for key in [
        "llm_judge_clarity",
        "llm_judge_usefulness",
        "llm_judge_consistency",
        "llm_judge_structure",
        "llm_judge_actionability",
    ]:
        value = _safe_number(scores.get(key))
        if value is not None:
            llm_parts.append(value)
    llm_component = statistics.mean(llm_parts) if llm_parts else llm_overall
    schema_ok = _safe_number(scores.get("schema_ok")) or 0.0
    issue_counts = metrics.get("issue_counts") or {}
    spelling_count = issue_counts.get("spelling", 0)
    non_spelling_total = 0.0
    non_spelling_counts = []
    for key, value in issue_counts.items():
        if not isinstance(value, int):
            continue
        if key == "spelling":
            continue
        non_spelling_total += value
        non_spelling_counts.append(value)
    spelling_weight = 0.2
    weighted_total = non_spelling_total + (spelling_count * spelling_weight)
    report_length = _safe_number(metrics.get("report_length")) or 0.0
    weighted_density = (weighted_total / report_length * 1000.0) if report_length else 0.0
    agent_disagreement = _safe_number(metrics.get("agent_disagreement")) or 0.0
    if len(non_spelling_counts) > 1:
        agent_disagreement = statistics.pstdev(non_spelling_counts)
    consistency = consistency_score if consistency_score is not None else 0.0
    total_issues = _safe_number(metrics.get("total_issues")) or 0.0

    density_penalty = min(weighted_density / 8.0, 1.0)
    disagreement_penalty = min(agent_disagreement / 2.0, 1.0)
    total_penalty = min(weighted_total / 15.0, 1.0)
    consistency_bonus = min(max(consistency, 0.0), 1.0)

    weights = {
        "llm": 0.45,
        "schema": 0.05,
        "density": 0.2,
        "disagreement": 0.15,
        "total": 0.1,
        "consistency": 0.05,
    }
    llm_available = llm_status in (None, "ok", "zero_score")
    if not llm_available:
        llm_weight = weights.pop("llm")
        other_sum = sum(weights.values())
        if other_sum:
            for key in list(weights.keys()):
                weights[key] = weights[key] + (weights[key] / other_sum) * llm_weight
    base = (
        llm_component * weights.get("llm", 0.0)
        + schema_ok * weights.get("schema", 0.0)
        + (1.0 - density_penalty) * weights.get("density", 0.0)
        + (1.0 - disagreement_penalty) * weights.get("disagreement", 0.0)
        + (1.0 - total_penalty) * weights.get("total", 0.0)
        + consistency_bonus * weights.get("consistency", 0.0)
    )

    final_eval = agent_metrics.get("final") or {}
    if final_eval.get("persona_alignment") == "misaligned":
        base -= 0.1
    if final_eval.get("overall_quality") == "unstable":
        base -= 0.1
    if metrics.get("has_issues"):
        base = min(base, 0.75)
    if metrics.get("decision") == "rewrite":
        base = min(base, 0.7)

    final_score = max(0.0, min(1.0, round(base, 4)))
    return {
        "quality_score_v2": final_score,
        "quality_score_v2_breakdown": {
            "llm_component_avg": round(llm_component, 4),
            "llm_judge_status": llm_status,
            "schema_ok": schema_ok,
            "issue_density_penalty": round(density_penalty, 4),
            "agent_disagreement_penalty": round(disagreement_penalty, 4),
            "total_issues_penalty": round(total_penalty, 4),
            "consistency_bonus": round(consistency_bonus, 4),
            "persona_alignment": final_eval.get("persona_alignment"),
            "overall_quality": final_eval.get("overall_quality"),
        },
        "quality_score_v2_inputs": {
            "weighted_total_issues": round(weighted_total, 4),
            "weighted_density_per_1k": round(weighted_density, 4),
            "spelling_weight": spelling_weight,
            "report_length": report_length,
            "total_issues": total_issues,
        },
    }


async def evaluate_text(
    text: str | None = None,
    doc_id: str | None = None,
    use_llm_judge: bool = False,
) -> Dict[str, Any]:
    if not text and not doc_id:
        raise ValueError("text or doc_id is required")

    if doc_id:
        async with get_session() as session:
            doc = await session.get(Document, doc_id)
            if not doc:
                raise ValueError("Document not found")
            text = doc.extracted_text
            context = doc.meta_json
    else:
        context = None

    analysis_start = time.perf_counter()
    outputs = await run_analysis_for_text(text=text, context=context)
    analysis_latency_ms = round((time.perf_counter() - analysis_start) * 1000.0, 2)
    scores = perform_eval(outputs)
    if use_llm_judge:
        scores.update(llm_as_judge(outputs))
        if scores.get("llm_judge_rationale"):
            scores["quality_rationale_ko"] = translate_rationale(
                scores.get("llm_judge_rationale", "")
            )
    else:
        scores.setdefault("llm_judge_status", "disabled")

    metrics = collect_metrics(outputs)
    agent_metrics, agent_latencies = collect_agent_metrics(outputs, text)
    prompt_version = os.getenv("PROMPT_VERSION")
    agent_version = os.getenv("AGENT_VERSION")
    eval_config_id = os.getenv("EVAL_CONFIG_ID")
    input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None
    meta = {
        "input_length": len(text) if text else 0,
        "input_hash": input_hash,
        "analysis_latency_ms": analysis_latency_ms,
        "prompt_version": prompt_version,
        "agent_version": agent_version,
        "eval_config_id": eval_config_id,
        "judge_model": os.getenv("JUDGE_MODEL", "solar-pro2"),
        "use_llm_judge": use_llm_judge,
    }

    prev_eval = await fetch_latest_eval_run()
    delta = compute_eval_delta(metrics, scores, prev_eval)
    history = await fetch_eval_history(limit=int(os.getenv("EVAL_HISTORY_LIMIT", "10")))
    history_stats = compute_history_stats(history)
    consistency_score = compute_consistency_score(input_hash, history)
    scores.update(
        compute_quality_score(metrics, scores, agent_metrics, consistency_score)
    )

    eval_run = EvalRun(
        id=os.urandom(16).hex(),
        document_id=doc_id,
        metrics_json=json.dumps(metrics, ensure_ascii=False),
        scores_json=json.dumps(scores, ensure_ascii=False),
        delta_json=json.dumps(delta, ensure_ascii=False),
        meta_json=json.dumps(meta, ensure_ascii=False),
        agent_latency_json=json.dumps(agent_latencies, ensure_ascii=False),
    )

    async with get_session() as session:
        session.add(eval_run)
        await session.commit()

    return {
        "doc_id": doc_id,
        "report": outputs.get("final_report") or outputs.get("report"),
        "metrics": metrics,
        "agent_metrics": agent_metrics,
        "scores": scores,
        "outputs": outputs,
        "delta": delta,
        "history_stats": history_stats,
        "consistency_score": consistency_score,
        "meta": meta,
        "agent_latencies": agent_latencies,
        "eval_run_id": eval_run.id,
    }
