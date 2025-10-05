from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from backend.utils.security import get_current_user
from backend.utils.task_crud.create import TaskCreator
from backend.utils.task_crud.read import TaskReader
from backend.utils.task_crud.update import TaskUpdater
from backend.wrappers.storage import SupabaseStorage
from backend.schemas.task import TaskCreateRequest, TaskUpdateRequest

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/createTask")
def create_task_endpoint(request: TaskCreateRequest, user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]

        task_creator = TaskCreator()
        result = task_creator.create_task_with_subtasks(
            user_id=user_id,
            main_task=request.main_task,
            subtasks=request.subtasks
        )

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc


@router.post("/uploadTaskFile")
async def upload_task_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_url: Optional[str] = None
    try:
        user_id = user.get("sub")
        storage = SupabaseStorage()
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        file_url = storage.upload_file(
            file_name=file.filename,
            file_bytes=file_bytes,
            content_type=file.content_type,
            user_id=user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc
    finally:
        await file.close()

    return {"file_url": file_url}


@router.put("/updateTask")
def update_task_endpoint(request: TaskUpdateRequest, user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]
        user_role = user["role"]
        user_teams = user.get("teams", [])

        task_updater = TaskUpdater()
        result = task_updater.update_tasks(
            main_task_id=request.main_task_id,
            user_id=user_id,
            user_role=user_role,
            user_teams=user_teams,
            main_task=request.main_task,
            subtasks=request.subtasks,
            new_subtasks=request.new_subtasks
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/readTasks")
def read_tasks_endpoint(user: dict = Depends(get_current_user)):
    """Read tasks based on user access control rules"""
    try:
        user_id = user["sub"]
        user_role = user["role"]
        user_teams = user.get("teams", [])
        user_departments = user.get("departments", [])

        task_reader = TaskReader()
        tasks = task_reader.get_tasks_for_user(
            user_id=user_id,
            user_role=user_role,
            user_teams=user_teams,
            user_departments=user_departments
        )

        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/readArchivedTasks")
def read_archived_tasks_endpoint(user: dict = Depends(get_current_user)):
    """Read archived subtasks with their main tasks based on user access control rules"""
    try:
        user_id = user["sub"]
        user_role = user["role"]
        user_teams = user.get("teams", [])
        user_departments = user.get("departments", [])

        task_reader = TaskReader()
        archived_subtasks = task_reader.get_archived_subtasks_for_user(
            user_id=user_id,
            user_role=user_role,
            user_teams=user_teams,
            user_departments=user_departments
        )

        return {"archived_subtasks": archived_subtasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/filterByDueDate")
def filter_tasks_by_due_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Filter tasks by due date range.

    Args:
        start_date: Optional ISO format date (YYYY-MM-DD) for range start
        end_date: Optional ISO format date (YYYY-MM-DD) for range end

    Returns:
        Filtered tasks within the date range, respecting user access control
    """
    try:
        user_id = user["sub"]
        user_role = user["role"]
        user_teams = user.get("teams", [])
        user_departments = user.get("departments", [])

        # Get all tasks user has access to
        task_reader = TaskReader()
        tasks = task_reader.get_tasks_for_user(
            user_id=user_id,
            user_role=user_role,
            user_teams=user_teams,
            user_departments=user_departments
        )

        # Filter by due date range if provided
        filtered_tasks = tasks
        if start_date:
            start = datetime.fromisoformat(start_date).date()
            filtered_tasks = [t for t in filtered_tasks if t.get("due_date") and datetime.fromisoformat(t["due_date"]).date() >= start]

        if end_date:
            end = datetime.fromisoformat(end_date).date()
            filtered_tasks = [t for t in filtered_tasks if t.get("due_date") and datetime.fromisoformat(t["due_date"]).date() <= end]

        return {"tasks": filtered_tasks}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
