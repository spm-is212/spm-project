from fastapi import APIRouter, Depends
from backend.utils.security import get_current_user
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("/my-teams")
def get_my_teams(user: dict = Depends(get_current_user)):
    """Get teams for the current user using user_teams junction table"""
    try:
        crud = SupabaseCRUD()
        user_id = user["sub"]

        # Method 1: Get teams from user_teams junction table
        user_teams_result = crud.client.table('user_teams').select('team_id').eq('user_id', user_id).execute()

        if not user_teams_result.data:
            # Fallback: Try getting from user.teams array if exists in JWT
            user_teams = user.get("teams", [])
            if user_teams and len(user_teams) > 0:
                result = crud.client.table('teams').select('*').in_('id', user_teams).execute()
                return {"teams": result.data or []}
            return {"teams": []}

        # Extract team IDs from junction table
        team_ids = [ut['team_id'] for ut in user_teams_result.data]

        # Fetch full team data
        teams_result = crud.client.table('teams').select('*').in_('id', team_ids).execute()

        return {"teams": teams_result.data or []}
    except Exception as e:
        # Log error and return empty array
        print(f"Teams table error: {str(e)}")
        return {"teams": []}

@router.get("/team-tasks")
def get_team_tasks(user: dict = Depends(get_current_user)):
    # TODO: Implement team tasks retrieval
    return {"tasks": []}
