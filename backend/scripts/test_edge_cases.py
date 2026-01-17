import asyncio
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.analysis_runner import run_analysis_for_text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test_case(name, text, context=None, mode="full"):
    print(f"\n>>> Running Test Case: {name}")
    print(f"Input Text (len): {len(text) if text else 0}")
    print(f"Context: {context}")
    
    try:
        result = await run_analysis_for_text(text, context=context, mode=mode)
        print(f"Result Status: SUCCESS")
        print(f"Decision: {result.get('decision')}")
        # print(f"Sample Result Keys: {list(result.keys())[:5]}")
    except Exception as e:
        print(f"Result Status: FAILED")
        print(f"Error: {e}")

async def main():
    load_dotenv()
    
    test_cases = [
        {
            "name": "Empty Text",
            "text": "",
            "context": None
        },
        {
            "name": "Whitespace Only",
            "text": "   \n   \t  ",
            "context": None
        },
        {
            "name": "Very Short Text",
            "text": "안녕",
            "context": None
        },
        {
            "name": "Invalid JSON Context",
            "text": "정상적인 텍스트입니다.",
            "context": "{'invalid': json}"
        },
        {
            "name": "Non-existent Selected Agent",
            "text": "정상적인 텍스트입니다.",
            "context": json.dumps({"settings": {"selected_agents": ["ghost_agent", "tone"]}})
        },
        {
            "name": "Large Text Simulation",
            "text": "이것은 매우 긴 텍스트입니다. " * 500, # Approx 7500 chars
            "context": None
        }
    ]
    
    for case in test_cases:
        await run_test_case(case["name"], case["text"], case["context"])

if __name__ == "__main__":
    asyncio.run(main())
