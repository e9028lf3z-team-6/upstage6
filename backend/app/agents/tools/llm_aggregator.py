from pydantic import BaseModel
from typing import List, Dict


class AggregateResult(BaseModel):
    """
    평가 및 위임 노드의 최종 출력 스키마

    - decision:
        * pass / rewrite

    - problem_types:
        * 발견된 문제 유형 목록
        * 예: ["hate", "trauma", "logic", "tone", "cliche"]

    - primary_issue:
        * 가장 우선적으로 개입해야 할 문제
        * 우선순위:
            hate > trauma > logic > tone > cliche

    - rationale:
        * 각 평가 축에 대한 판단 근거 요약 (explainability)

    - reader_confusion_detected:
        * 페르소나 관점에서 독자 혼란 감지 여부

    - reader_context_gap:
        * 독자 기준에서 배경 설명 부족 감지 여부
    """

    decision: str
    problem_types: List[str]
    primary_issue: str | None
    rationale: Dict[str, str]

    reader_confusion_detected: bool = False
    reader_context_gap: bool = False

    summary: str = ""
class IssueBasedAggregatorAgent:
    """
    평가 및 위임 노드 (Issue 기반 Aggregator)

    설계 원칙:
    1. 판단만 수행 (생성/수정/평가 X)
    2. LLM 사용 안 함 (완전 결정론)
    3. 점수 사용 안 함 (issue 존재 여부만 사용)

    최종 판단 우선순위:
        hate > trauma > logic > tone > cliche

    주의:
    - cliche는 rewrite 결정의 직접 원인이 아님
    - 참고 정보(soft signal)로만 포함
    """

    name = "issue-aggregator"

    def run(
        self,
        tone_issues: List[dict],
        logic_issues: List[dict],
        trauma_issues: List[dict] | None = None,
        hate_issues: List[dict] | None = None,
        cliche_issues: List[dict] | None = None,
        persona_feedback: dict | None = None,
        reader_context: dict | None = None,
    ) -> AggregateResult:

        trauma_issues = trauma_issues or []
        hate_issues = hate_issues or []
        cliche_issues = cliche_issues or []

        problem_types: List[str] = []
        rationale: Dict[str, str] = {}

        # -----------------------------
        # 1. Hate / Bias (최상위)
        # -----------------------------
        if hate_issues:
            problem_types.append("hate")
            rationale["hate"] = f"{len(hate_issues)} issue(s) detected"
        else:
            rationale["hate"] = "no issue"

        # -----------------------------
        # 2. Trauma
        # -----------------------------
        if trauma_issues:
            problem_types.append("trauma")
            rationale["trauma"] = f"{len(trauma_issues)} issue(s) detected"
        else:
            rationale["trauma"] = "no issue"

        # -----------------------------
        # 3. Logic
        # -----------------------------
        if logic_issues:
            problem_types.append("logic")
            rationale["logic"] = f"{len(logic_issues)} issue(s) detected"
        else:
            rationale["logic"] = "no issue"

        # -----------------------------
        # 4. Tone
        # -----------------------------
        if tone_issues:
            problem_types.append("tone")
            rationale["tone"] = f"{len(tone_issues)} issue(s) detected"
        else:
            rationale["tone"] = "no issue"

        # -----------------------------
        # 5. Genre Cliché
        # -----------------------------
        if cliche_issues:
            problem_types.append("cliche")
            rationale["cliche"] = (
                f"{len(cliche_issues)} cliché pattern(s) detected "
                f"(reference only)"
            )
        else:
            rationale["cliche"] = "no issue"

        # -----------------------------
        # 6. Persona 기반 약한 신호
        # -----------------------------
        reader_confusion_detected = False
        reader_context_gap = False

        if persona_feedback:
            confusions = persona_feedback.get("confusions", [])
            missing_context = persona_feedback.get("missing_context", [])

            if confusions:
                reader_confusion_detected = True
                rationale["persona_confusion"] = (
                    f"{len(confusions)} confusion(s) detected from reader persona"
                )

            if missing_context:
                reader_context_gap = True
                rationale["persona_context_gap"] = (
                    f"{len(missing_context)} missing context point(s) detected"
                )

        # -----------------------------
        # 7. 독자 기준 명시
        # -----------------------------
        if reader_context and reader_context.get("knowledge_level"):
            rationale["logic_basis"] = (
                f"logic evaluation performed based on "
                f"{reader_context.get('knowledge_level')} reader level"
            )
        else:
            rationale["logic_basis"] = (
                "logic evaluation performed based on default reader level"
            )

        # -----------------------------
        # 8. primary_issue 결정
        # -----------------------------
        primary_issue = None
        if "hate" in problem_types:
            primary_issue = "hate"
        elif "trauma" in problem_types:
            primary_issue = "trauma"
        elif "logic" in problem_types:
            primary_issue = "logic"
        elif "tone" in problem_types:
            primary_issue = "tone"
        elif "cliche" in problem_types:
            primary_issue = "cliche"

        # -----------------------------
        # 9. 최종 decision
        # -----------------------------
        # cliche 단독으로는 rewrite를 유발하지 않음
        hard_problem_types = [
            p for p in problem_types if p != "cliche"
        ]
        decision = "rewrite" if hard_problem_types else "pass"
        # decision 요약 문장 만들기
        if decision == "pass":
            summary = "전반적으로 큰 문제는 발견되지 않았습니다. 현재 원고는 그대로 진행(pass) 가능합니다."
        else:
            summary = f"수정(rewrite) 권장: 주요 이슈는 {primary_issue}이며, 문제 유형은 {', '.join(problem_types)} 입니다."

        return AggregateResult(
            decision=decision,
            problem_types=problem_types,
            primary_issue=primary_issue,
            rationale=rationale,
            reader_confusion_detected=reader_confusion_detected,
            reader_context_gap=reader_context_gap,
            summary=summary,
        )
