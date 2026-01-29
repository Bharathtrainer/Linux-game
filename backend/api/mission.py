from fastapi import APIRouter

router = APIRouter()

@router.post("/start")
def start_mission(user_id: str):
    return {"message": f"Mission started for {user_id}"}
