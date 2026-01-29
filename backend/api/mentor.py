from fastapi import APIRouter
from core.nim_client import NIMClient
from core.model_router import select_model
from prompts.mentor import MENTOR_SYSTEM_PROMPT

router = APIRouter()

@router.post("/help")
def mentor_help(level: str, issue: str):
    model = select_model(level)
    nim = NIMClient(model)
    response = nim.infer(MENTOR_SYSTEM_PROMPT, issue)
    return response["choices"][0]["message"]["content"]
