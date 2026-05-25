"""Judge endpoint — scores the player's command attempts against a scenario.

Original (January) version: just fed the commands as a string to NIM and
returned whatever came back. No rubric, no JSON parsing, no scenario context.
Revived to take structured attempts (commands + their sandbox output) and
return a graded result matching the schema in prompts/judge.py.
"""

import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from core.llm_client import NIMClient, extract_json
from core.model_router import select_model
from prompts.judge import JUDGE_SYSTEM_PROMPT

router = APIRouter()


class Attempt(BaseModel):
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


class EvaluateRequest(BaseModel):
    level: str
    scenario: dict[str, Any]   # the scenario YAML dict (objective, success_signal, ...)
    attempts: list[Attempt]


@router.post("/evaluate")
def evaluate(req: EvaluateRequest):
    model = select_model(req.level)
    client = NIMClient(model)
    user_prompt = json.dumps(
        {
            "scenario": {
                "title": req.scenario.get("title"),
                "narrative": req.scenario.get("narrative"),
                "objective": req.scenario.get("objective"),
                "success_signal": req.scenario.get("success_signal"),
                "success_keywords": req.scenario.get("success_keywords", []),
            },
            "attempts": [a.model_dump() for a in req.attempts],
        },
        indent=2,
    )
    response = client.infer(JUDGE_SYSTEM_PROMPT, user_prompt)
    return extract_json(response)
