from fastapi import APIRouter, HTTPException, Depends
from backend.utils.security import get_current_user
from backend.utils.task_crud.create import TaskCreator
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
        user_role = user["role"]

        task_updater = TaskUpdater()
        result = task_updater.update_tasks(
            main_task_id=request.main_task_id,
            user_role=user_role,
            main_task=request.main_task,
            subtasks=request.subtasks
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
