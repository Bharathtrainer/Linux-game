"""Mission endpoint — orchestrates the full game loop.

Original (January) version: a single endpoint that returned a "Mission started"
string and did nothing else. Revived to be the actual heart of the game:

  POST /mission/start   → pick a scenario for the level, return narrative
  POST /mission/run     → run a player command in the sandbox, return output
  POST /mission/finish  → submit all attempts for grading by the judge

Scenarios are loaded from backend/scenarios/*.yaml. The sandbox runner from
core/sandbox.py executes user commands inside a one-shot Docker container.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.sandbox import run_in_sandbox, sandbox_image_exists
from api.judge import evaluate, EvaluateRequest, Attempt

router = APIRouter()

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def _load_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for path in SCENARIOS_DIR.glob("*.yaml"):
        with path.open("r", encoding="utf-8") as f:
            scenarios.append(yaml.safe_load(f))
    return scenarios


def _pick_scenario(level: str) -> dict[str, Any]:
    pool = [s for s in _load_scenarios() if s.get("level") == level.lower()]
    if not pool:
        raise HTTPException(
            status_code=404,
            detail=f"No scenarios available for level '{level}'. "
                   f"Available levels: entry, operator, engineer, sre.",
        )
    return random.choice(pool)


class StartRequest(BaseModel):
    user_id: str
    level: str


@router.post("/start")
def start_mission(req: StartRequest):
    """Pick a random scenario for this level and return it.

    The frontend keeps the scenario in memory and passes it back to /finish
    so the judge has the success criteria.
    """
    if not sandbox_image_exists():
        raise HTTPException(
            status_code=503,
            detail="Sandbox Docker image not built. Run "
                   "`docker build -t linux-mastery-sandbox sandbox/` first.",
        )
    scenario = _pick_scenario(req.level)
    return {
        "user_id": req.user_id,
        "scenario": scenario,
        "intro": (
            f"{scenario['title']}\n\n{scenario['narrative']}\n\n"
            f"Objective: {scenario['objective']}"
        ),
    }


class RunRequest(BaseModel):
    command: str
    setup_script: str | None = None  # passed from the scenario


@router.post("/run")
def run_command(req: RunRequest):
    """Execute a single player command inside the Docker sandbox."""
    result = run_in_sandbox(req.command, setup_script=req.setup_script)
    return result.to_dict()


class FinishRequest(BaseModel):
    user_id: str
    level: str
    scenario: dict[str, Any]
    attempts: list[Attempt]


@router.post("/finish")
def finish_mission(req: FinishRequest):
    """Send the player's attempts to the judge for scoring."""
    eval_req = EvaluateRequest(
        level=req.level,
        scenario=req.scenario,
        attempts=req.attempts,
    )
    grade = evaluate(eval_req)
    return {"user_id": req.user_id, "grade": grade}
