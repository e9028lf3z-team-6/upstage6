import time
from typing import Dict, Any, List

def add_log(agent: str, message: str, log_type: str = "info") -> List[Dict[str, Any]]:
    """
    새로운 에이전트 로그 항목을 리스트로 생성하여 반환합니다.
    LangGraph의 Annotated logs 리듀서와 함께 사용하기 위해 개별 로그만 반환합니다.
    """
    return [{
        "agent": agent,
        "message": message,
        "type": log_type,
        "timestamp": time.time()
    }]
