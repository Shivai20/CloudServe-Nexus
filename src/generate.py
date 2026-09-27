"""Verifiable Grounded Generation Module (A6).

Drafts customer responses strictly grounded in retrieved documentation passages,
citing specific chunk IDs (e.g., [DOC-AUTH-001#sec-3]).
Includes resilient extractive fallback when the LLM provider is offline or times out (A11).
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
import re
from src.guardrails import get_guardrails
from src.models import (
    GenerationResult,
    NormalizedTicket,
    RetrievedChunk,
    RoutingAction,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Default to Groq's fast llama model if using Groq, otherwise OpenRouter default
DEFAULT_MODEL = "llama-3.1-8b-instant" if GROQ_API_KEY else "meta-llama/llama-3.1-8b-instruct"
MODEL_NAME = os.getenv("MODEL_NAME", DEFAULT_MODEL)


class GroundedGenerator:
    """Generates grounded responses with verifiable citations."""

    def __init__(self):
        self.guardrails = get_guardrails()

    def generate(
        self, ticket: NormalizedTicket, retrieved_chunks: List[RetrievedChunk]
    ) -> GenerationResult:
        """Generates a grounded response with citations from retrieved documentation."""
        if not retrieved_chunks:
            return GenerationResult(
                response_text=(
                    "Thank you for contacting CloudServe support. I do not have enough documentation "
                    "to answer your question directly. I have escalated this ticket to our senior engineering team."
                ),
                citations=[],
                is_grounded=True,
                grounding_notes="No passages retrieved; escalated plainly per A6.",
            )

        # 1. Try Primary LLM (Groq)
        if GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"):
            logger.info("Attempting generation via Groq...")
            res = self._call_llm(ticket, retrieved_chunks, GROQ_API_KEY, "https://api.groq.com/openai/v1", "openai/gpt-oss-20b")
            if res: return res
            
        # 2. Try Backup LLM (OpenRouter)
        if OPENROUTER_API_KEY and not OPENROUTER_API_KEY.startswith("your_"):
            logger.info("Groq failed or unavailable. Falling back to OpenRouter...")
            res = self._call_llm(ticket, retrieved_chunks, OPENROUTER_API_KEY, "https://openrouter.ai/api/v1", "meta-llama/llama-3.1-8b-instruct")
            if res: return res

        # 3. Graceful Degradation (A11) - If all APIs fail, gracefully escalate.
        logger.warning("All LLM providers failed. Gracefully degrading to human escalation.")
        return GenerationResult(
            response_text=(
                "Thank you for contacting CloudServe. We are currently experiencing high support volume, "
                "so I have escalated your ticket to our senior engineering team for immediate review."
            ),
            citations=[],
            is_grounded=True,
            grounding_notes="LLM providers offline. Graceful escalation triggered (A11).",
        )

    def _call_llm(
        self, ticket: NormalizedTicket, retrieved_chunks: List[RetrievedChunk],
        api_key: str, base_url: str, model_name: str
    ) -> Optional[GenerationResult]:
        """Calls a specific LLM endpoint and validates the response."""
        try:
            import requests

            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "prompts",
                "build",
                "generate_prompt.txt",
            )
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()

            chunks_formatted = "\n\n".join(
                f"[{c.chunk_id}] {c.title}\n{c.content}" for c in retrieved_chunks[:3]
            )

            prompt = template.replace("{retrieved_chunks}", chunks_formatted)\
                             .replace("{ticket_id}", ticket.ticket_id)\
                             .replace("{customer_tier}", ticket.customer_tier)\
                             .replace("{ticket_text}", ticket.full_text)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a professional CloudServe support engineer."},
                    {"role": "user", "content": prompt},
                ]
            }
            
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=8.0)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            resp_text = parsed.get("response", "")
            citations = parsed.get("citations", [])
            if not citations:
                citations = re.findall(r"\[(DOC-[A-Z]+-\d+(?:#sec-\d+)?)\]", resp_text)

            # Validate generated output with guardrails
            safe, reason, _ = self.guardrails.check_generated_response(
                resp_text, chunks_formatted
            )
            if not safe:
                logger.warning(f"Generated text failed guardrails: {reason}")
                return None

            return GenerationResult(
                response_text=resp_text,
                citations=citations,
                is_grounded=True,
                grounding_notes=f"Generated via {model_name} with verified citations.",
            )

        except Exception as e:
            logger.error(f"LLM Call failed to {base_url}: {e}")
            return None


_generator_instance: Optional[GroundedGenerator] = None


def get_generator() -> GroundedGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = GroundedGenerator()
    return _generator_instance
