from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from backend.utils.security import get_current_user
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/create", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    """Create a new project with collaborators"""
    try:
        crud = SupabaseCRUD()
        user_id = user["sub"]

        # Prepare project data
        project_data = {
            "name": project.name,
            "description": project.description,
            "collaborator_ids": project.collaborator_ids,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Add team_id if provided (for backward compatibility)
        if project.team_id:
            project_data["team_id"] = project.team_id

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
    List projects where the user is a collaborator or has assigned tasks

    Args:
        team_id: Optional team ID to filter projects (deprecated, for backward compatibility)
    """
    try:
        crud = SupabaseCRUD()
        user_id = user["sub"]
        user_role = user.get("role", "user")

        # Get all projects
        projects = crud.client.table("projects").select("*").execute()

        if not projects.data:
            return []

        # For directors/managing directors, return all projects
        if user_role in ["director", "managing_director"]:
            user_projects = projects.data
        else:
            # Method 1: Filter by collaborator_ids
            collaborator_projects = [
                p for p in projects.data
                if p.get("collaborator_ids") and user_id in p.get("collaborator_ids", [])
            ]

            # Method 2: Also include projects where user has tasks assigned
            # Get all tasks where user is assignee or owner
            tasks_result = crud.client.table("tasks").select("project_id").or_(
                f"owner_user_id.eq.{user_id},assignee_ids.cs.{{{user_id}}}"
            ).execute()

            task_project_ids = set([t['project_id'] for t in tasks_result.data if t.get('project_id')])

            # Combine both methods
            user_project_ids = set([p['id'] for p in collaborator_projects])
            user_project_ids.update(task_project_ids)

            user_projects = [p for p in projects.data if p['id'] in user_project_ids]

        # Optional: filter by team_id if provided (backward compatibility)
        if team_id:
            user_projects = [p for p in user_projects if p.get("team_id") == team_id]

        return user_projects
    except ConnectionError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Database connection unavailable. Please try again.")
    except TimeoutError as e:
        print(f"Database timeout error: {str(e)}")
        raise HTTPException(status_code=504, detail="Database request timed out. Please try again.")
    except Exception as e:
        print(f"Unexpected error in list_projects: {str(e)}")
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
        user_id = user["sub"]

        # Check if project exists
        existing = crud.client.table("projects").select("*").eq("id", project_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify user is a collaborator or has permission to update
        project_data = existing.data[0]
        if user_id not in project_data.get("collaborator_ids", []):
            # Allow directors/managing directors to update
            if user.get("role") not in ["director", "managing_director"]:
                raise HTTPException(status_code=403, detail="Only project collaborators can update the project")

        # Prepare update data (only include fields that are provided)
        update_data = {}
        if project.name is not None:
            update_data["name"] = project.name
        if project.description is not None:
            update_data["description"] = project.description
        if project.collaborator_ids is not None:
            update_data["collaborator_ids"] = project.collaborator_ids
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
