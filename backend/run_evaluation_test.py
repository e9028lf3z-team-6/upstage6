import os
import sys
import json
from dotenv import load_dotenv

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd()))

from app.agents.evaluators.tone_evaluator import ToneQualityAgent

def main():
    # 1. Load Env (API Key needed for LLM)
    load_dotenv()
    if not os.getenv("UPSTAGE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("Error: UPSTAGE_API_KEY or OPENAI_API_KEY is missing in .env")
        print("Please set it to run the LLM evaluation.")
        return

    # 2. Prepare Mock Data
    original_text = """
    철수는 밥을 먹었다. 그리고 갑자기 우주로 날아갔다. 
    영희가 말했다. "뭐하노? 니 미칫나?"
    작가는 생각했다. 이 전개가 맞는 것인가? 독자님들에게 사과드립니다.
    """

    # 가상의 Tone Agent 분석 결과 (일부러 실수를 섞음)
    mock_agent_output = {
        "issues": [
            {
                "location": "영희가 말했다.",
                "problem": "표준어가 아닌 표현 사용",
                "evidence": "뭐하노? 니 미칫나?",
                "reader_impact": "이해하기 어려움"
            }
        ],
        "note": "전반적으로 산만함"
    }

    print("---\n--- [Input Data] ---")
    print(f"Original Text: {original_text.strip()}")
    print(f"Agent Output: {json.dumps(mock_agent_output, ensure_ascii=False)}")
    print("\n---\n--- [Running Evaluator...] ---")

    # 3. Run Evaluator
    evaluator = ToneQualityAgent()
    try:
        result = evaluator.run(original_text, mock_agent_output)
        
        print("\n---\n--- [Evaluation Result] ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error running evaluator: {e}")

if __name__ == "__main__":
    main()
