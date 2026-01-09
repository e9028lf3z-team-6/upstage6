import os
import re
from typing import List, Dict, Any

from openai import OpenAI  # openai==1.52.2
from dotenv import load_dotenv

from app.service.vector_service import VectorService
from app.service.time_service import TimeService

load_dotenv()


class AgentService:
    def __init__(self, vector_service: VectorService, time_service: TimeService):
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")

        self.client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1")
        self.vector_service = vector_service
        self.time_service = time_service

    # ===============================
    # Public
    # ===============================
    def process_query(self, query: str, context_limit: int = 3) -> Dict[str, Any]:
        """
        글로벌 협업 가이드 Agent 메인 진입점
        """
        # 1. 질문에서 지역 추출
        timezone, location_name = self._extract_timezone(query)

        # 2. 현지 시간 조회 (Function Calling 결과 활용)
        time_info = self.time_service.get_current_time(timezone)
        local_time = time_info.hhmm

        # 3. 근무 규정 검색 (RAG)
        rules = self.vector_service.search_for_agent(
            f"{location_name} 근무 규정",
            k=context_limit,
        )

        # 4. context 구성
        context = self._prepare_context(
            location_name=location_name,
            local_time=local_time,
            rules=rules,
        )

        # 5. 판단 생성
        response = self._generate_response(query, context)

        return {
            "question": query,
            "ai_message": response,
        }

    # ===============================
    # Internal helpers
    # ===============================
    def _extract_timezone(self, query: str) -> tuple[str, str]:
        """
        질문에서 지역을 추출하여 timezone으로 변환
        (과제 범위에서는 단순 매핑이면 충분)
        """
        if re.search(r"런던|London", query, re.IGNORECASE):
            return "Europe/London", "런던"

        # 기본값 (확장 가능)
        return "Asia/Seoul", "서울"

    def _prepare_context(self, location_name: str, local_time: str, rules: List[str]) -> str:
        """
        LLM이 '판단'하기 쉬운 형태의 context 생성
        """
        rules_text = "\n".join(f"- {r}" for r in rules)

        return f"""
현재 {location_name} 현지 시간은 {local_time} 입니다.

{location_name} 지사 근무 규정:
{rules_text}
""".strip()

    def _generate_response(self, query: str, context: str) -> str:
        system_prompt = """
You are a global collaboration guide bot.

Your job:
- Decide whether a meeting or call is appropriate now.
- Use BOTH the local time and the working rules.
- Answer clearly with a reason.
"""

        user_prompt = f"""
Context:
{context}

User question:
{query}

Answer in Korean.
"""

        try:
            response = self.client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Error generating response: {str(e)}"

    # ===============================
    # Knowledge ingestion
    # ===============================
    def add_knowledge(
            self,
            documents: List[str],
            metadatas: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        근무 규정(rules.json 등)을 Vector DB에 주입
        """
        if not documents:
            raise ValueError("documents is empty")

        self.vector_service.add_documents(
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "status": "success",
            "message": f"{len(documents)} documents inserted",
            "inserted": len(documents),
        }
