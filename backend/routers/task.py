from fastapi import APIRouter, HTTPException, Depends
from backend.utils.security import get_current_user
from backend.utils.task_crud.create import TaskCreator
from backend.utils.task_crud.read import TaskReader
from backend.utils.task_crud.update import TaskUpdater
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
