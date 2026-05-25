"""
LLM client for the Enterprise Linux Mastery Game.

Originally written against NVIDIA NIM (paid, lost access during the project's
abandonment). Revived to default to Ollama (local, free, no API key) while
keeping the original NIM path as a fallback for users who have it.

The provider is chosen by the LLM_PROVIDER env var ('ollama' or 'nim').
The legacy NIMClient class name is kept as an alias so existing callers
(api/mentor.py, api/judge.py) keep working without modification.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Ollama (default)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL_DEFAULT = os.getenv("OLLAMA_MODEL", "llama3.1")

# NIM (legacy)
NIM_BASE_URL = os.getenv("NIM_BASE_URL")
NIM_API_KEY = os.getenv("NIM_API_KEY")


# -----------------------------------------------------------------------------
# Provider implementations
# -----------------------------------------------------------------------------
class OllamaClient:
    """Talks to a local Ollama instance using its OpenAI-compatible /api/chat."""

    def __init__(self, model: str):
        # Allow callers to pass NIM-flavoured model names; map to a local one.
        self.model = self._resolve_model_alias(model)

    @staticmethod
    def _resolve_model_alias(model: str) -> str:
        """Map legacy NIM model names to local Ollama tags so older callers
        don't break. If the model already looks like an Ollama tag, pass through."""
        nim_to_ollama = {
            "llama-3.1-nemotron-nano-8b-v1": "llama3.1",
            "llama-3.3-nemotron-super-49b-v1.5": "llama3.1",
            "llama-3.1-nemotron-ultra-253b-v1": "llama3.1",
        }
        return nim_to_ollama.get(model, model or OLLAMA_MODEL_DEFAULT)

    def infer(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 512},
        }
        try:
            r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Cannot reach Ollama at {OLLAMA_HOST}. Is `ollama serve` running?"
            ) from e
        data = r.json()
        # Reshape into the OpenAI-style structure the old NIM caller expected,
        # so api/mentor.py and api/judge.py keep working.
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": data.get("message", {}).get("content", ""),
                    }
                }
            ],
            "model": data.get("model", self.model),
        }


class NIMClient_:
    """Original NVIDIA NIM client. Used only when LLM_PROVIDER=nim."""

    def __init__(self, model: str):
        self.model = model

    def infer(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not NIM_BASE_URL or not NIM_API_KEY:
            raise RuntimeError(
                "NIM_BASE_URL and NIM_API_KEY must be set when LLM_PROVIDER=nim. "
                "Set LLM_PROVIDER=ollama for local inference instead."
            )
        headers = {
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        }
        r = requests.post(f"{NIM_BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()


# -----------------------------------------------------------------------------
# Public façade
# -----------------------------------------------------------------------------
def get_client(model: str):
    """Return the client matching LLM_PROVIDER."""
    if LLM_PROVIDER == "nim":
        return NIMClient_(model)
    return OllamaClient(model)


# Legacy name kept so api/mentor.py and api/judge.py don't have to change yet.
class NIMClient:
    """Legacy alias. Routes to whichever provider is configured."""

    def __init__(self, model: str):
        self._inner = get_client(model)

    def infer(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return self._inner.infer(system_prompt, user_prompt)


def extract_text(response: dict[str, Any]) -> str:
    """Helper to pull text out of either provider's response."""
    return response["choices"][0]["message"]["content"]


def extract_json(response: dict[str, Any]) -> dict[str, Any]:
    """Pull JSON out of an LLM response, tolerating ```json fences and prose."""
    text = extract_text(response).strip()
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.split("```", 2)
        text = text[1] if len(text) > 1 else text[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    # Find the first { and the last } and grab between (handles prose wrappers).
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text, "error": "Model did not return valid JSON"}
