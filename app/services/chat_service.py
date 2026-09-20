"""Retrieval-augmented answer generation with a strict zero-hallucination prompt."""
import re

from groq import Groq
from app.config import settings
from app.services import vectorstore, memory

_client = Groq(api_key=settings.GROQ_API_KEY)


def sanitize_answer(answer: str) -> str:
    """Convert raw assistant markdown into cleaner plain text for the dashboard."""
    if not answer:
        return answer

    cleaned = answer.strip()
    cleaned = re.sub(r"^\s*[*\-]\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("*", "")
    cleaned = cleaned.replace(",", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

FALLBACK_MESSAGE = "I don't have information on this."

SYSTEM_PROMPT = """You are a customer support assistant. You must answer ONLY using \
the CONTEXT provided below, which comes from the company's own documents. \

Rules you must always follow:
- If the answer is not clearly present in the CONTEXT, respond with exactly: \
"I don't have information on this." Do not guess, infer, or use outside knowledge.
- Never make up facts, links, prices, or policies that are not in the CONTEXT.
- Keep answers concise and directly address the user's question.
- You may use the recent conversation history to understand follow-up questions, \
but the factual content of your answer must still come only from the CONTEXT.
"""


def answer_query(session_id: str, message: str) -> dict:
    hits = vectorstore.query(message, top_k=settings.TOP_K)

    relevant_hits = [h for h in hits if h["distance"] <= settings.MAX_DISTANCE_THRESHOLD]
    if not relevant_hits and hits:
        relevant_hits = hits[:min(2, len(hits))]

    if not relevant_hits:
        memory.add_turn(session_id, "user", message)
        memory.add_turn(session_id, "assistant", FALLBACK_MESSAGE)
        return {"answer": FALLBACK_MESSAGE, "sources": [], "resolved": False}

    context = "\n\n---\n\n".join(
        f"[Source: {h['filename']}]\n{h['text']}" for h in relevant_hits
    )

    history = memory.get_history(session_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {message}"}
    ]

    response = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=500,
        messages=messages,
    )
    answer = sanitize_answer(response.choices[0].message.content.strip())

    resolved = FALLBACK_MESSAGE.lower() not in answer.lower()

    memory.add_turn(session_id, "user", message)
    memory.add_turn(session_id, "assistant", answer)

    sources = sorted({h["filename"] for h in relevant_hits})
    return {"answer": answer, "sources": sources, "resolved": resolved}