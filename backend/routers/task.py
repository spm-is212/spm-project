from typing import Optional
from datetime import datetime
import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import ValidationError
from backend.utils.security import get_current_user
from backend.utils.task_crud.create import TaskCreator
from backend.utils.task_crud.read import TaskReader
from backend.utils.task_crud.update import TaskUpdater
from backend.schemas.task import TaskCreateRequest, TaskUpdateRequest
from backend.wrappers.storage import SupabaseStorage
from backend.utils.task_crud.constants import MAX_FILE_SIZE_BYTES, FILE_TOO_LARGE_ERROR, FILE_UPLOAD_ERROR

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/createTask")
async def create_task_endpoint(
    task_data: str = Form(...),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    try:
        user_id = user["sub"]
        request_dict = json.loads(task_data)
        request = TaskCreateRequest(**request_dict)

        file_url = None
        if file:
            file_bytes = await file.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail=FILE_TOO_LARGE_ERROR)

            try:
                storage = SupabaseStorage()
                file_url = storage.upload_file(
                    file_name=file.filename,
                    file_bytes=file_bytes,
                    content_type=file.content_type,
                    user_id=user_id
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{FILE_UPLOAD_ERROR}: {str(e)}")
            finally:
                await file.close()

        if file_url:
            request.main_task.file_url = file_url

        task_creator = TaskCreator()
        result = task_creator.create_task_with_subtasks(
            user_id=user_id,
            main_task=request.main_task,
            subtasks=request.subtasks
        )

        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=[{"msg": str(err["msg"]), "type": err["type"], "loc": err["loc"]} for err in e.errors()])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/updateTask")
async def update_task_endpoint(
    task_data: str = Form(...),
    file: Optional[UploadFile] = File(None),
    remove_file: bool = Form(False),
    user: dict = Depends(get_current_user)
):
    try:
        user_id = user["sub"]
        user_role = user["role"]

        request_dict = json.loads(task_data)
        request = TaskUpdateRequest(**request_dict)

        if remove_file and request.main_task:
            from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
            crud = SupabaseCRUD()
            existing_task = crud.select("tasks", filters={"id": request.main_task_id})
            if existing_task and existing_task[0].get("file_url"):
                storage = SupabaseStorage()
                storage.delete_file(existing_task[0]["file_url"])
            request.main_task.file_url = None

        file_url = None
        if file:
            file_bytes = await file.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail=FILE_TOO_LARGE_ERROR)

            try:
                from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
                crud = SupabaseCRUD()
                existing_task = crud.select("tasks", filters={"id": request.main_task_id})
                if existing_task and existing_task[0].get("file_url"):
                    storage = SupabaseStorage()
                    storage.delete_file(existing_task[0]["file_url"])

                storage = SupabaseStorage()
                file_url = storage.upload_file(
                    file_name=file.filename,
                    file_bytes=file_bytes,
                    content_type=file.content_type,
                    user_id=user_id
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{FILE_UPLOAD_ERROR}: {str(e)}")
            finally:
                await file.close()

        if file_url and request.main_task:
            request.main_task.file_url = file_url

        task_updater = TaskUpdater()
        result = task_updater.update_tasks(
            main_task_id=request.main_task_id,
            user_id=user_id,
            user_role=user_role,
            main_task=request.main_task,
            subtasks=request.subtasks,
            new_subtasks=request.new_subtasks
        )

        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=[{"msg": str(err["msg"]), "type": err["type"], "loc": err["loc"]} for err in e.errors()])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/readTasks")
def read_tasks_endpoint(user: dict = Depends(get_current_user)):
    """
    Read tasks based on user access control rules.

    Access control is based on:
    - Role hierarchy (managing_director > director > manager > staff)
    - Project collaboration (tasks in projects where user is a collaborator)
    - Direct task assignment (tasks where user is an assignee)
    """
    try:
        user_id = user["sub"]
        user_role = user["role"]
        user_departments = user.get("departments", [])

        task_reader = TaskReader()
        tasks = task_reader.get_tasks_for_user(
            user_id=user_id,
            user_role=user_role,
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
        user_departments = user.get("departments", [])

        task_reader = TaskReader()
        archived_subtasks = task_reader.get_archived_subtasks_for_user(
            user_id=user_id,
            user_role=user_role,
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
        user_departments = user.get("departments", [])

        # Get all tasks user has access to
        task_reader = TaskReader()
        tasks = task_reader.get_tasks_for_user(
            user_id=user_id,
            user_role=user_role,
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
