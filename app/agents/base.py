from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        ...
