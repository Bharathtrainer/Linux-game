from fastapi import APIRouter
from core.nim_client import NIMClient
from core.model_router import select_model
from prompts.judge import JUDGE_SYSTEM_PROMPT

router = APIRouter()

@router.post("/evaluate")
def evaluate(level: str, commands: list[str]):
    model = select_model(level)
    nim = NIMClient(model)
    prompt = f"Commands executed:\n{commands}"
    response = nim.infer(JUDGE_SYSTEM_PROMPT, prompt)
    return response["choices"][0]["message"]["content"]
