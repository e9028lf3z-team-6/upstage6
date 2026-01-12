# backend/app/agents/__init__.py
"""
agents public API

- agents/tools, agents/metrics 하위의 실제 Agent 클래스들을 자동 노출
- 외부에서는 `from app.agents import XXXAgent` 만 사용
"""

from importlib import import_module
from pathlib import Path
import inspect

__all__ = []

BASE_DIR = Path(__file__).parent
SUB_PACKAGES = ["tools", "metrics"]


def _load_agents_from(package_name: str):
    package_dir = BASE_DIR / package_name
    module_base = f"app.agents.{package_name}"

    for py_file in package_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        module = import_module(f"{module_base}.{module_name}")

        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Agent 관례: 클래스명 끝이 Agent
            if obj.__name__.endswith("Agent"):
                globals()[obj.__name__] = obj
                __all__.append(obj.__name__)


for sub in SUB_PACKAGES:
    _load_agents_from(sub)
