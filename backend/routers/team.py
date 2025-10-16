from fastapi import APIRouter, Depends
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/teams", tags=["teams (deprecated)"])

@router.get("/my-teams", deprecated=True)
def get_my_teams(user: dict = Depends(get_current_user)):
    """
    DEPRECATED: This endpoint is deprecated and will be removed.

    The team abstraction has been removed. Use /api/projects/list instead
    to get projects where you are a collaborator.

    For backward compatibility, this returns an empty teams array.
    """
    # Return empty array for backward compatibility
    return {"teams": [], "message": "Teams feature deprecated. Use projects instead."}

@router.get("/team-tasks", deprecated=True)
def get_team_tasks(user: dict = Depends(get_current_user)):
    """
    DEPRECATED: This endpoint is deprecated and will be removed.

    Use /api/tasks/read instead to get tasks where you are an assignee,
    or filter tasks by project_id.
    """
    return {"tasks": [], "message": "Teams feature deprecated. Use task endpoints with project filters instead."}
