<<<<<<< Updated upstream
from fastapi import APIRouter, HTTPException
from backend.utils.security import get_current_user
from backend.utils.task_crud.crud import create_task, update_task
from backend.schemas.task import TaskCreate, TaskUpdate
import uuid
=======
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from backend.utils.security import get_current_user
from backend.utils.task_crud.create import TaskCreator
from backend.utils.task_crud.read import TaskReader
from backend.utils.task_crud.update import TaskUpdater
from backend.wrappers.storage import SupabaseStorage
from backend.schemas.task import TaskCreateRequest, TaskUpdateRequest
>>>>>>> Stashed changes

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


@router.post("/uploadTaskFile")
async def upload_task_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_url = None
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        await file.close()

    return {"file_url": file_url}


@router.put("/updateTask")
def update_task_endpoint(task_data: TaskUpdate):
    try:
        user = get_current_user()
        user_id = user["sub"]
        update_task(user_id, task_data.task_uuid, task_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
