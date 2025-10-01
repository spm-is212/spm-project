from fastapi import APIRouter, Depends
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("/my-teams")
def get_my_teams(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    return {"teams": ["Team A", "Team B"]}

@router.get("/team-tasks")
def get_team_tasks(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    user_teams = user.get("teams", [])
    return {"tasks": ["Task 1", "Task 2"]}
