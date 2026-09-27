"""
Safety guardrails: input prompt-injection screening and output toxicity/PII
screening. Wraps a lightweight heuristic layer plus an optional NeMo
Guardrails / Llama Guard hook for stricter enforcement.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
import re
from dataclasses import dataclass

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|any|previous) instructions",
    r"disregard (the )?system prompt",
    r"you are now (in )?(dan|jailbreak|developer) mode",
    r"reveal (your|the) (system prompt|hidden instructions)",
    r"act as if you have no (restrictions|guardrails|filters)",
]

TOXIC_OUTPUT_PATTERNS = [
    r"\b(kill|harm) (yourself|someone)\b",
    r"\bhow to (build|make) a (bomb|weapon)\b",
]

PII_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
}


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str | None = None
    redacted_text: str | None = None


class GuardrailsEngine:
    """Fast heuristic pre-filter; swap in NeMo Guardrails / Llama Guard for
    production-grade semantic classification by implementing `_llm_classify`.
    """

    def __init__(self) -> None:
        self._injection_re = re.compile("|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)
        self._toxic_re = re.compile("|".join(TOXIC_OUTPUT_PATTERNS), re.IGNORECASE)

    def screen_input(self, text: str) -> GuardrailResult:
        if self._injection_re.search(text):
            return GuardrailResult(allowed=False, reason="prompt_injection_detected")
        return GuardrailResult(allowed=True)

    def screen_output(self, text: str) -> GuardrailResult:
        if self._toxic_re.search(text):
            return GuardrailResult(allowed=False, reason="toxic_content_detected")
        redacted = text
        for label, pattern in PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[REDACTED_{label.upper()}]", redacted)
        return GuardrailResult(allowed=True, redacted_text=redacted)

    async def _llm_classify(self, text: str) -> GuardrailResult:  # pragma: no cover
        """Hook point: call NeMo Guardrails rails or a Llama-Guard endpoint
        here for semantic (not just regex) classification in production."""
        raise NotImplementedError


guardrails_engine = GuardrailsEngine()
