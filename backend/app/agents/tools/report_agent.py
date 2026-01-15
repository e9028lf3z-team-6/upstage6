import json
from typing import Dict, List
from app.agents.base import BaseAgent
from app.llm.chat import chat


class ComprehensiveReportAgent(BaseAgent):
    """
    종합 리포트 에이전트 (Chief Editor)

    역할:
    - 모든 개별 에이전트(Tone, Causality, Trauma, Hate, Cliche, Persona)의 결과를 종합
    - 작가에게 전달할 최종 피드백 리포트를 작성 (사람이 읽기 좋은 자연어)
    - 단순 나열이 아닌, 편집자 관점의 통찰과 우선순위를 제공

    입력:
    - 각 에이전트별 이슈 목록
    - 페르소나 피드백
    - 텍스트 요약 정보

    출력:
    - Markdown 포맷의 구조화된 리포트
    """

    name = "report-agent"

    def run(
        self,
        split_text: dict,
        tone_issues: List[dict],
        logic_issues: List[dict],
        trauma_issues: List[dict],
        hate_issues: List[dict],
        cliche_issues: List[dict],
        persona_feedback: dict | None = None,
    ) -> Dict:
        # 원고의 전반적인 분위기를 알 수 있도록 앞부분 문장들을 추출
        text_preview = ""
        if isinstance(split_text, dict):
            raw_sentences = split_text.get("sentences") or split_text.get("split_sentences")
            if isinstance(raw_sentences, list) and raw_sentences:
                # 앞부분 15문장 정도를 보여주어 맥락 파악 도움
                text_preview = "\n".join(raw_sentences[:15])

        def _format_all_issues(issues: List[dict], title: str) -> str:
            if not issues:
                return f"{title}: 발견된 이슈 없음"
            
            lines = [f"### {title} (총 {len(issues)}건)"]
            for iss in issues:
                idx = iss.get('sentence_index', '?')
                quote = iss.get('quote') or iss.get('original') or "인용문 없음"
                reason = iss.get('reason') or iss.get('description') or "사유 없음"
                severity = iss.get('severity', 'medium')
                lines.append(f"- [문장 {idx} / 중요도: {severity}] \"{quote}\" -> {reason}")
            return "\n".join(lines)

        system = """
        당신은 냉철하지만 건설적인 조언을 주는 '수석 편집자(Chief Editor)'입니다.
        제공된 모든 분석 데이터를 꼼꼼히 검토하여 작가에게 최종 리포트를 작성하십시오.
        결과는 반드시 마크다운(Markdown) 형식으로만 작성하십시오.
        """

        prompt = f"""
        당신은 수석 편집자입니다. 아래 제공된 [전체 분석 데이터]를 바탕으로 작가를 위한 '최종 편집 리포트'를 작성하세요.
        절대 데이터를 생략하지 말고, 문서 전체에서 발견된 주요 흐름을 짚어주어야 합니다.

        [분석 데이터 요약]
        {_format_all_issues(hate_issues, "1. 혐오/차별 표현")}
        
        {_format_all_issues(trauma_issues, "2. 트라우마 유발 가능성")}
        
        {_format_all_issues(logic_issues, "3. 논리/개연성 이슈")}
        
        {_format_all_issues(tone_issues, "4. 말투/어조 이슈")}
        
        {_format_all_issues(cliche_issues, "5. 장르 클리셰")}

        [6. 독자 페르소나 피드백]
        {json.dumps(persona_feedback, ensure_ascii=False) if persona_feedback else "특이사항 없음"}

        [원고 일부 (맥락 참조용)]
        {text_preview}

        [작성 지침 및 구조]
        당신은 아래의 구조와 원칙에 따라 마크다운(Markdown) 형식의 리포트를 작성해야 합니다.
        
        # [1. 종합 진단 요약]
        - **최종 판정**: (예: 🔴 재작성 권고 / 🟡 부분 수정 필요 / 🟢 승인)
        - **한 줄 요약**: 전체 피드백을 관통하는 가장 중요한 핵심 문장.

        # [2. 에이전트별 상세 피드백]
        - 각 이슈는 가능한 한 issue의 quote를 그대로 인용하고 sentence_index를 함께 표기하세요.
        - 근거 인용은 목록 형태로 정리하고, 중요도 순서로 배열하세요.
        - **📚 서사/장르 분석관**: 글의 구조, 장르적 특징, 클리셰 활용도 요약. (Cliche 이슈 참고)
        - **✍️ 말투/표현 감사관**: 언어적 습관, 어색한 문장, 톤앤매너 일치 여부 요약. (Tone 이슈 참고)
        - **🧐 인과/논리 검증관**: 설정 오류, 개연성 부족, 사건의 연결성 문제 요약. (Logic/Causality 이슈 참고)
        - **🛡️ 윤리/안전 관리자**: 트라우마, 혐오 표현 등 세이프티 체크 결과 요약. (Hate/Trauma 이슈 참고)
        - **👥 가상 독자(페르소나) 반응**: 설정된 페르소나가 느낀 구체적인 혼란이나 질문 요약.

        # [3. 최종 메트릭 및 개선 우선순위]
        - **핵심 리스크**: 가장 먼저 해결해야 할 문제 1-2가지.
        - **수정 방향 제안**: 작가가 바로 실행할 수 있는 구체적인 가이드라인.
        """

        response = chat(prompt, system=system)

        # JSON 파싱 없이 마크다운 텍스트를 그대로 반환
        return {
            "report_title": "종합 분석 리포트",
            "summary": "종합 리포트를 확인하세요.",  # 요약은 마크다운 안에 포함됨
            "full_report_markdown": response,
        }
