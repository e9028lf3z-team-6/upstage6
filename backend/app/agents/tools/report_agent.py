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
        
        # 텍스트 일부만 발췌해서 문맥 제공 (전체 텍스트는 너무 길 수 있음)
        # split_text의 앞부분 요약이나 일부만 사용
        text_preview = ""
        if isinstance(split_text, dict) and "split_text" in split_text:
             # split_text가 리스트라면 앞부분 5개 정도만
            raw_splits = split_text["split_text"]
            if isinstance(raw_splits, list):
                text_preview = "\n".join(raw_splits[:5])
            else:
                text_preview = str(raw_splits)[:1000]

        system = """
        당신은 냉철하지만 건설적인 조언을 주는 '수석 편집자(Chief Editor)'입니다.
        당신의 목표는 작가가 이 리포트를 보고 글을 실제로 수정할 수 있도록 돕는 것입니다.
        
        반드시 JSON 형식으로 출력해야 합니다.
        """

        prompt = f"""
        당신은 냉철하면서도 따뜻한 조언을 주는 '수석 편집자(Chief Editor)'입니다.
        아래 제공된 [분석 데이터]를 종합하여, 작가가 글을 수정할 수 있도록 돕는 '최종 편집 리포트'를 작성해야 합니다.

        [분석 데이터]
        1. 혐오/차별 표현 (Hate/Bias): {len(hate_issues)}건
           - 세부: {str(hate_issues)[:500]}
        2. 트라우마 유발 가능성 (Trauma): {len(trauma_issues)}건
           - 세부: {str(trauma_issues)[:500]}
        3. 논리/개연성 이슈 (Logic/Causality): {len(logic_issues)}건
           - 세부: {str(logic_issues)[:500]}
        4. 말투/어조 이슈 (Tone): {len(tone_issues)}건
           - 세부: {str(tone_issues)[:500]}
        5. 장르 클리셰 (Cliche): {len(cliche_issues)}건
           - 세부: {str(cliche_issues)[:500]}
        6. 독자 페르소나 피드백:
           {str(persona_feedback)[:500] if persona_feedback else "없음"}

        [원고 미리보기 (일부)]
        {text_preview}

        [작성 지침 및 구조]
        당신은 아래의 구조와 원칙에 따라 마크다운(Markdown) 형식의 리포트를 작성해야 합니다.

        1. 분석 결과 정리 원칙
        - 에이전트별 의인화: 각 분석 영역을 "XX 에이전트는 이렇게 답변했습니다"라는 형식을 사용하여 전문성을 부여하십시오.
        - 핵심 위주 요약: 모든 데이터를 나열하지 말고, 작가가 즉각적으로 이해해야 할 '치명적인 결함'과 '장점' 위주로 압축하십시오.
        - 통찰력 있는 연결: 예를 들어, "말투의 문제(Tone)가 결국 캐릭터의 개연성(Causality)을 해치고 있다"는 식으로 서로 다른 에이전트의 결과를 연결해 분석하십시오.
        - 명확한 결론: 최종적으로 '승인(Accept)', '수정 권고(Minor Revision)', '재작성(Rewrite)' 중 하나를 명확히 판정하십시오.

        2. 보고서 출력 구조 (Markdown 내용에 반드시 포함)
        
        # [1. 종합 진단 요약]
        - **최종 판정**: (예: 🚨 재작성 권고 / ⚠️ 부분 수정 필요 / ✅ 승인)
        - **한 줄 요약**: 전체 피드백을 관통하는 가장 중요한 핵심 문장.

        # [2. 에이전트별 상세 피드백]
        - **🧐 서사/장르 분석관**: 글의 구조, 장르적 특징, 클리셰 활용도 요약. (Cliche 이슈 참고)
        - **🗣️ 말투/표현 감사관**: 언어적 습관, 어색한 문장, 톤앤매너 일치 여부 요약. (Tone 이슈 참고)
        - **🔗 인과/논리 검증관**: 설정 오류, 개연성 부족, 사건의 연결성 문제 요약. (Logic/Causality 이슈 참고)
        - **🛡️ 윤리/안전 관리자**: 트라우마, 혐오 표현 등 세이프티 체크 결과 요약. (Hate/Trauma 이슈 참고)
        - **👤 가상 독자(페르소나) 반응**: 설정된 페르소나가 느낀 구체적인 혼란이나 질문 요약.

        # [3. 최종 메트릭 및 개선 우선순위]
        - **핵심 리스크**: 가장 먼저 해결해야 할 문제 1-2가지.
        - **수정 방향 제안**: 작가가 바로 실행할 수 있는 구체적인 가이드라인.

        [출력 형식 (JSON)]
        {{
            "report_title": "종합 분석 리포트",
            "summary": "한 줄 요약 내용",
            "full_report_markdown": "위 [작성 지침 및 구조]에 따라 작성된 전체 마크다운 텍스트"
        }}
        """

        response = chat(prompt, system=system)
        return self._safe_json_load(response)
