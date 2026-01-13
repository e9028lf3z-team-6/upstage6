import json
import os

from app.llm.chat import chat


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


def _interpret_report_sections(sections: dict) -> dict:
    if os.getenv("EVAL_REPORT_LLM_INTERPRET", "false").lower() != "true":
        return {}

    system = (
        "You are a strict JSON generator. "
        "Return valid JSON only. No markdown."
    )
    prompt = (
        "다음은 평가 리포트의 섹션별 수치 요약이다. "
        "각 섹션에 대해 1문장 한국어 해석을 작성하라. "
        "수치를 반복하지 말고 의미를 해석하라.\n"
        "숫자, 퍼센트, 단위 표기는 금지한다. "
        "데이터에 없는 내용을 추가하거나 추론하지 마라.\n"
        "해석은 한 줄로 작성하고 줄바꿈을 포함하지 마라.\n"
        "반드시 JSON으로만 응답하고, 키는 아래를 그대로 사용하라.\n\n"
        "keys: execution_summary, issue_density, delta, trend_stats, "
        "score_trend, quality_scores, agent_summary, prompt_suggestions\n\n"
        f"data: {json.dumps(sections, ensure_ascii=False)}"
    )
    response = chat(prompt, system=system, temperature=0.0)
    data = _safe_json(response)
    if not data:
        extracted = _extract_json_block(response)
        if extracted:
            data = _safe_json(extracted)
    if not data:
        return {"_status": "parse_failed", "_raw": response[:500]}
    for key, value in list(data.items()):
        if isinstance(value, str):
            cleaned = " ".join(value.split())
            data[key] = cleaned
    data["_status"] = "ok"
    return data


def render_eval_report(payload: dict) -> str:
    report = payload.get("report") or {}
    doc_id = payload.get("doc_id")
    metrics = payload.get("metrics") or {}
    scores = payload.get("scores") or {}
    agent_metrics = payload.get("agent_metrics") or {}
    issue_counts = metrics.get("issue_counts") or {}
    delta = payload.get("delta") or {}
    history_stats = payload.get("history_stats") or {}
    consistency_score = payload.get("consistency_score")
    meta = payload.get("meta") or {}
    agent_latencies = payload.get("agent_latencies") or {}
    issue_delta = delta.get("issue_counts") or {}
    total_issue_delta = sum(v for v in issue_delta.values() if isinstance(v, int))
    if total_issue_delta < 0:
        trend = "improving"
    elif total_issue_delta > 0:
        trend = "regressing"
    else:
        trend = "stable"
    top_regressed = [k for k, v in issue_delta.items() if isinstance(v, int) and v > 0]
    top_improved = [k for k, v in issue_delta.items() if isinstance(v, int) and v < 0]

    interpretations = _interpret_report_sections(
        {
            "execution_summary": {
                "decision": metrics.get("decision"),
                "has_issues": metrics.get("has_issues"),
                "report_length": metrics.get("report_length"),
                "input_length": meta.get("input_length"),
                "analysis_latency_ms": meta.get("analysis_latency_ms"),
            },
            "issue_density": {
                "issue_counts": issue_counts,
                "total_issues": metrics.get("total_issues"),
                "issue_density_per_1k": metrics.get("issue_density_per_1k"),
                "dominant_issue": metrics.get("dominant_issue"),
                "dominant_issue_strength": metrics.get("dominant_issue_strength"),
                "agent_disagreement": metrics.get("agent_disagreement"),
            },
            "delta": {
                "trend": trend,
                "issue_delta": issue_delta,
                "decision_changed": delta.get("decision_changed"),
                "top_regressed": top_regressed,
                "top_improved": top_improved,
            },
            "trend_stats": history_stats,
            "score_trend": history_stats.get("scores") if history_stats else {},
            "quality_scores": scores,
            "agent_summary": agent_metrics,
            "prompt_suggestions": {
                "active": [
                    name
                    for name, active in {
                        "tone_agent": issue_counts.get("tone", 0) > 0,
                        "causality_agent": issue_counts.get("logic", 0) > 0,
                        "trauma_agent": issue_counts.get("trauma", 0) > 0,
                        "hate_bias_agent": issue_counts.get("hate_bias", 0) > 0,
                        "genre_cliche_agent": issue_counts.get("genre_cliche", 0) > 0,
                        "report_agent": (agent_metrics.get("final") or {}).get("persona_alignment") == "misaligned",
                    }.items()
                    if active
                ],
                "dominant_issue": metrics.get("dominant_issue"),
                "issue_density": metrics.get("issue_density_per_1k"),
            },
        }
    )
    interpret_enabled = os.getenv("EVAL_REPORT_LLM_INTERPRET", "false").lower() == "true"
    interpret_failed = interpretations.get("_status") == "parse_failed"

    lines = []
    lines.append("==== 평가 리포트 ====")
    lines.append("")

    lines.append("[실행 요약]")
    if doc_id:
        lines.append(f"- doc_id: {doc_id}")
    lines.append(f"- decision: {metrics.get('decision')}")
    lines.append(f"- has_issues: {metrics.get('has_issues')}")
    lines.append(f"- report_length: {metrics.get('report_length')}")
    if meta.get("input_length") is not None:
        lines.append(f"- input_length: {meta.get('input_length')}")
    if meta.get("analysis_latency_ms") is not None:
        lines.append(f"- analysis_latency_ms: {meta.get('analysis_latency_ms')}")
    if interpretations.get("execution_summary"):
        lines.append(f"- 해석: {interpretations.get('execution_summary')}")
    elif interpret_enabled:
        lines.append("- 해석: (생성 실패)")
    lines.append("")

    lines.append("[이슈 밀도]")
    lines.append(
        f"- tone={issue_counts.get('tone')} logic={issue_counts.get('logic')} "
        f"trauma={issue_counts.get('trauma')} hate_bias={issue_counts.get('hate_bias')} "
        f"cliche={issue_counts.get('genre_cliche')} spelling={issue_counts.get('spelling')}"
    )
    lines.append(
        f"- total_issues={metrics.get('total_issues')} "
        f"issue_density_per_1k={metrics.get('issue_density_per_1k')} "
        f"dominant_issue={metrics.get('dominant_issue')} "
        f"dominant_issue_strength={metrics.get('dominant_issue_strength')} "
        f"agent_disagreement={metrics.get('agent_disagreement')}"
    )
    if interpretations.get("issue_density"):
        lines.append(f"- 해석: {interpretations.get('issue_density')}")
    elif interpret_enabled:
        lines.append("- 해석: (생성 실패)")
    lines.append("")

    if delta:
        lines.append("[변화량]")
        if delta.get("decision_changed"):
            lines.append("- decision_changed: true")
        if issue_delta:
            lines.append(f"- trend: {trend} (issue_total_delta={total_issue_delta:+d})")
            lines.append(
                "- issue_delta: "
                + " ".join(f"{k}={v:+d}" for k, v in issue_delta.items())
            )
            if top_regressed:
                lines.append("- top_regressed: " + ", ".join(top_regressed))
            if top_improved:
                lines.append("- top_improved: " + ", ".join(top_improved))
        if interpretations.get("delta"):
            lines.append(f"- 해석: {interpretations.get('delta')}")
        elif interpret_enabled:
            lines.append("- 해석: (생성 실패)")
        score_delta = delta.get("scores") or {}
        if score_delta:
            lines.append(
                "- score_delta: "
                + " ".join(f"{k}={v:+.2f}" for k, v in score_delta.items())
            )
        lines.append("")

    if history_stats:
        lines.append("[추세 통계]")
        lines.append(f"- sample_size: {history_stats.get('sample_size')}")
        total_stats = history_stats.get("total_issues") or {}
        if total_stats:
            lines.append(
                "- total_issues_avg/median/std: "
                f"{total_stats.get('mean')}/{total_stats.get('median')}/{total_stats.get('std')}"
            )
        for key, stats in (history_stats.get("issue_counts") or {}).items():
            lines.append(
                f"- {key}_avg/median/std: {stats.get('mean')}/{stats.get('median')}/{stats.get('std')}"
            )
        llm_stats = history_stats.get("llm_judge_overall") or {}
        if llm_stats:
            lines.append(
                "- llm_judge_overall_avg/median/std: "
                f"{llm_stats.get('mean')}/{llm_stats.get('median')}/{llm_stats.get('std')}"
            )
        if consistency_score is not None:
            lines.append(f"- consistency_score: {consistency_score}")
        if interpretations.get("trend_stats"):
            lines.append(f"- 해석: {interpretations.get('trend_stats')}")
        elif interpret_enabled:
            lines.append("- 해석: (생성 실패)")
        lines.append("")

    score_stats = history_stats.get("scores") or {}
    if score_stats:
        lines.append("[품질 점수 추세]")
        quality_stats = score_stats.get("quality_score_v2") or {}
        if quality_stats:
            lines.append(
                "- quality_score_v2_avg/median/std: "
                f"{quality_stats.get('mean')}/{quality_stats.get('median')}/{quality_stats.get('std')}"
            )
        if interpretations.get("score_trend"):
            lines.append(f"- 해석: {interpretations.get('score_trend')}")
        elif interpret_enabled:
            lines.append("- 해석: (생성 실패)")
        lines.append("")

    lines.append("[품질 점수]")
    for key in [
        "quality_score_v2",
    ]:
        if key in scores:
            lines.append(f"- {key}: {scores.get(key)}")
    if scores.get("quality_score_v2_breakdown"):
        lines.append(f"- quality_score_v2_breakdown: {scores.get('quality_score_v2_breakdown')}")
    if scores.get("quality_score_v2_inputs"):
        lines.append(f"- quality_score_v2_inputs: {scores.get('quality_score_v2_inputs')}")
    if "quality_rationale_ko" in scores:
        rationale = scores.get("quality_rationale_ko")
        if rationale:
            lines.append(f"- rationale: {rationale}")
    if interpretations.get("quality_scores"):
        lines.append(f"- 해석: {interpretations.get('quality_scores')}")
    elif interpret_enabled:
        lines.append("- 해석: (생성 실패)")
    lines.append("")

    lines.append("[품질 평가 기준]")
    lines.append("- clarity: 보고서가 명확하고 모호하지 않은가")
    lines.append("- usefulness: 실무에 도움이 되는 구체적 지적과 제안이 있는가")
    lines.append("- consistency_with_decision: decision(예: rewrite)와 근거가 일치하는가")
    lines.append("- structure: 섹션 구성과 흐름이 논리적인가")
    lines.append("- actionability: 바로 적용 가능한 행동 지침이 있는가")
    lines.append("- overall: 위 항목을 종합한 품질 판단")
    lines.append("")

    lines.append("[에이전트 성능 요약]")
    for key in ["tone", "logic", "trauma", "hate_bias", "genre_cliche", "spelling"]:
        value = agent_metrics.get(key) or {}
        if not value:
            continue
        score = value.get("score", "n/a")
        reason = value.get("reason")
        error = value.get("error")
        line = f"- {key}: score={score}"
        if reason:
            line += f" reason={reason}"
        if error:
            line += f" error={error}"
        lines.append(line)
        latency = agent_latencies.get(key)
        if latency is not None:
            lines.append(f"- {key}_latency_ms: {latency}")
    final_eval = agent_metrics.get("final") or {}
    if final_eval:
        lines.append(f"- overall_quality: {final_eval.get('overall_quality')}")
        lines.append(f"- dominant_risk: {final_eval.get('dominant_risk')}")
        lines.append(f"- issue_density: {final_eval.get('issue_density')}")
        lines.append(f"- persona_alignment: {final_eval.get('persona_alignment')}")
    if interpretations.get("agent_summary"):
        lines.append(f"- 해석: {interpretations.get('agent_summary')}")
    elif interpret_enabled:
        lines.append("- 해석: (생성 실패)")
    lines.append("")

    lines.append("[프롬프트 개선 제안]")
    if issue_counts.get("tone", 0) > 0:
        lines.append("- tone_agent: 위치·증거 필드를 강제하고, 말투만 다루도록 범위를 좁히세요.")
    if issue_counts.get("logic", 0) > 0:
        lines.append("- causality_agent: 사건 A→B 전환만 다루도록 명시하고, 동기/전제 누락을 우선 식별하게 하세요.")
    if issue_counts.get("trauma", 0) > 0:
        lines.append("- trauma_agent: 트리거 분류 기준을 명확화하고, 과도한 공포 묘사 탐지에 집중하게 하세요.")
    if issue_counts.get("hate_bias", 0) > 0:
        lines.append("- hate_bias_agent: 집단 대상만 허용하고 개인 이름/비유는 제외하도록 규칙을 강화하세요.")
    if issue_counts.get("genre_cliche", 0) > 0:
        lines.append("- genre_cliche_agent: 장르/패턴/근거 3요소를 강제하고 모호한 패턴을 배제하세요.")
    if final_eval.get("persona_alignment") == "misaligned":
        lines.append("- report_agent: 페르소나/업무 맥락 연결을 서두에 명시하도록 요구하세요.")
    if interpretations.get("prompt_suggestions"):
        lines.append(f"- 해석: {interpretations.get('prompt_suggestions')}")
    elif interpret_enabled:
        lines.append("- 해석: (생성 실패)")
    lines.append("")
    lines.append("[참고]")
    lines.append("- 위 제안은 프롬프트 수정 방향에 대한 고수준 가이드입니다.")
    if meta.get("prompt_version") or meta.get("agent_version") or meta.get("eval_config_id"):
        lines.append(
            "- eval_meta: "
            f"prompt_version={meta.get('prompt_version')} "
            f"agent_version={meta.get('agent_version')} "
            f"eval_config_id={meta.get('eval_config_id')}"
        )
    if interpret_failed:
        lines.append("- interpret_status: parse_failed")
    return "\n".join(lines)
