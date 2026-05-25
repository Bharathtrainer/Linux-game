"""FastAPI entry point for the Enterprise Linux Mastery Game.

Run from the `backend/` directory:
    uvicorn main:app --reload

Or from the repo root:
    uvicorn backend.main:app --reload --app-dir .

Either works as long as your CWD allows the `api`, `core`, `prompts` packages
to resolve. The repo's quickstart uses the first form for simplicity.
"""

from fastapi import FastAPI

from api import judge, mentor, mission

app = FastAPI(
    title="Enterprise Linux Mastery Game",
    description=(
        "Local-first, AI-mentored Linux training game. "
        "Revived for the GitHub Finish-Up-A-Thon."
    ),
    version="0.2.0",
)

app.include_router(mentor.router, prefix="/mentor", tags=["mentor"])
app.include_router(judge.router, prefix="/judge", tags=["judge"])
app.include_router(mission.router, prefix="/mission", tags=["mission"])


@app.get("/")
def health():
    return {
        "status": "running",
        "version": app.version,
        "message": "Enterprise Linux Mastery Game backend is up.",
    }
