from fastapi import APIRouter, HTTPException
from backend.utils.security import get_current_user
from backend.utils.task_crud.crud import create_task, update_task
from backend.schemas.task import TaskCreate, TaskUpdate
import uuid

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/createTask")
def create_task_endpoint(task_data: TaskCreate):
    try:
        user = get_current_user()
        user_id = user["sub"]
        task_uuid = str(uuid.uuid4())
        create_task(user_id, task_data, task_uuid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/updateTask")
def update_task_endpoint(task_data: TaskUpdate):
    try:
        user = get_current_user()
        user_id = user["sub"]
        update_task(user_id, task_data.task_uuid, task_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
