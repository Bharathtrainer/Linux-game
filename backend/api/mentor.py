"""Mentor endpoint — generates scenarios and gives Socratic hints.

Original (January) version called NIM directly with a vague prompt and
returned freeform text. Revived to use the LLM client façade (Ollama by
default) and the structured JSON schema defined in prompts/mentor.py.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.llm_client import NIMClient, extract_json
from core.model_router import select_model
from prompts.mentor import MENTOR_SYSTEM_PROMPT

router = APIRouter()


class HelpRequest(BaseModel):
    level: str
    issue: str  # natural-language description of what the player tried


@router.post("/help")
def mentor_help(req: HelpRequest):
    """Get a Socratic-method hint based on what the player has tried."""
    try:
        model = select_model(req.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    client = NIMClient(model)
    user_prompt = f"HINT_REQUEST\n\nPlayer has tried:\n{req.issue}\n\nGive them a Socratic-method hint."
    response = client.infer(MENTOR_SYSTEM_PROMPT, user_prompt)
    return extract_json(response)


class ScenarioRequest(BaseModel):
    level: str
    topic_hint: str | None = None  # e.g. "disk", "networking", "systemd"


@router.post("/scenario")
def generate_scenario(req: ScenarioRequest):
    """Have the mentor invent a fresh scenario for the given level."""
    try:
        model = select_model(req.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    client = NIMClient(model)
    topic = req.topic_hint or "any realistic enterprise Linux situation"
    user_prompt = (
        f"GENERATE_SCENARIO\n\n"
        f"Level: {req.level}\n"
        f"Topic: {topic}\n\n"
        f"Generate a single scenario following the SCENARIO mode schema."
    )
    response = client.infer(MENTOR_SYSTEM_PROMPT, user_prompt)
    return extract_json(response)
