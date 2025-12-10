from dataclasses import dataclass
from typing import Protocol


class Tool(Protocol):
    name: str
    description: str

    async def run(self, query: str) -> str:
        ...


@dataclass
class KnowledgeBaseTool:
    name: str = "knowledge_base_search"
    description: str = "Search the internal knowledge base for relevant snippets."

    async def run(self, query: str) -> str:
        return f"[KB search results for '{query}']"


@dataclass
class CalculatorTool:
    name: str = "calculator"
    description: str = "Perform basic numeric calculations."

    async def run(self, query: str) -> str:
        try:
            return str(eval(query, {"__builtins__": {}}))
        except Exception as exc:  # noqa: BLE001
            return f"Calculator error: {exc}"

