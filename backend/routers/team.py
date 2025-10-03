from fastapi import APIRouter, Depends
from backend.utils.security import get_current_user
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("/my-teams")
def get_my_teams(user: dict = Depends(get_current_user)):
    """Get teams for the current user"""
    try:
        user_teams = user.get("teams", [])

        if not user_teams or len(user_teams) == 0:
            return {"teams": []}

        crud = SupabaseCRUD()

        # Fetch teams from database
        result = crud.client.table('teams').select('*').in_('id', user_teams).execute()

        return {"teams": result.data or []}
    except Exception as e:
        # Log error and return empty array instead of dummy data
        print(f"Teams table error: {str(e)}")
        return {"teams": []}

@router.get("/team-tasks")
def get_team_tasks(user: dict = Depends(get_current_user)):
    # TODO: Implement team tasks retrieval
    return {"tasks": []}
