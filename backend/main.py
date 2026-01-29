from fastapi import FastAPI
from api import mentor, judge, mission

app = FastAPI(title="Enterprise Linux Mastery Game")

app.include_router(mentor.router, prefix="/mentor")
app.include_router(judge.router, prefix="/judge")
app.include_router(mission.router, prefix="/mission")

@app.get("/")
def health():
    return {"status": "running"}
