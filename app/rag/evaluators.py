from dataclasses import dataclass


@dataclass
class EvaluationResult:
    faithfulness: float
    relevance: float
    notes: str


async def evaluate_response(answer: str, references: list[dict]) -> EvaluationResult:
    # Placeholder logic until hooking up to a judge model
    score = 0.8 if references else 0.2
    return EvaluationResult(
        faithfulness=score,
        relevance=score,
        notes="Static evaluation until automated judge is integrated.",
    )

