from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from backend.utils.security import get_current_user
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/create", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    """Create a new project"""
    try:
        crud = SupabaseCRUD()

        # Prepare project data
        project_data = {
            "name": project.name,
            "description": project.description,
            "team_id": project.team_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Insert into database
        result = crud.client.table("projects").insert(project_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create project")

        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/list", response_model=List[ProjectResponse])
def list_projects(team_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """
    List all projects, optionally filtered by team_id

    Args:
        team_id: Optional team ID to filter projects
    """
    try:
        crud = SupabaseCRUD()

        if team_id:
            # Filter by team_id
            projects = crud.client.table("projects").select("*").eq("team_id", team_id).execute()
        else:
            # Get all projects
            projects = crud.client.table("projects").select("*").execute()

        return projects.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get a specific project by ID"""
    try:
        crud = SupabaseCRUD()

        result = crud.client.table("projects").select("*").eq("id", project_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project: ProjectUpdate,
    user: dict = Depends(get_current_user)
):
    """Update a project"""
    try:
        crud = SupabaseCRUD()

        # Check if project exists
        existing = crud.client.table("projects").select("*").eq("id", project_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Prepare update data (only include fields that are provided)
        update_data = {}
        if project.name is not None:
            update_data["name"] = project.name
        if project.description is not None:
            update_data["description"] = project.description
        if project.team_id is not None:
            update_data["team_id"] = project.team_id

        update_data["updated_at"] = datetime.utcnow().isoformat()

        # Update in database
        result = crud.client.table("projects").update(update_data).eq("id", project_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update project")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{project_id}")
def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete a project"""
    try:
        crud = SupabaseCRUD()

        # Check if project exists
        existing = crud.client.table("projects").select("*").eq("id", project_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete from database
        crud.client.table("projects").delete().eq("id", project_id).execute()

        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
