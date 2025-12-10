from typing import Final

BASE_PROMPT = """You are an expert {role} for an industrial company.
Answer the user's question using ONLY the provided context.

Context:
{context}

Question: {question}
Helpful answer:"""

ROLE_PROMPTS: Final[dict[str, str]] = {
    "operator": BASE_PROMPT.format(role="operation technician", context="{context}", question="{question}"),
    "maintenance": BASE_PROMPT.format(
        role="maintenance engineer", context="{context}", question="{question}"
    ),
    "manager": BASE_PROMPT.format(role="plant manager", context="{context}", question="{question}"),
}


def get_prompt(role: str | None = None) -> str:
    if role and role in ROLE_PROMPTS:
        return ROLE_PROMPTS[role]
    return BASE_PROMPT.format(role="industrial assistant", context="{context}", question="{question}")

