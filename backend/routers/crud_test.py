from fastapi import APIRouter, HTTPException
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.crud_schemas import (
    ReadRequest,
    CreateRequest,
    UpdateRequest,
    DeleteRequest,
    CountRequest
)

router = APIRouter(prefix="/api/crud", tags=["crud"])


@router.post("/read")
def read_table(request: ReadRequest):
    try:
        result = SupabaseCRUD().select(
            table=request.table_name,
            columns=request.columns,
            filters=request.filters,
            limit=request.limit,
            order_by=request.order_by,
            ascending=request.ascending
        )
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {request.table_name}: {str(e)}")


@router.post("/create")
def create_record(request: CreateRequest):
    try:
        result = SupabaseCRUD().insert(table=request.table_name, data=request.data)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating record in {request.table_name}: {str(e)}")


@router.post("/update")
def update_record(request: UpdateRequest):
    try:
        result = SupabaseCRUD().update(table=request.table_name, data=request.data, filters=request.filters)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating {request.table_name}: {str(e)}")


@router.post("/delete")
def delete_record(request: DeleteRequest):
    try:
        result = SupabaseCRUD().delete(table=request.table_name, filters=request.filters)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting from {request.table_name}: {str(e)}")


@router.post("/count")
def count_records(request: CountRequest):
    try:
        result = SupabaseCRUD().count(table=request.table_name, filters=request.filters)
        return {"count": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting {request.table_name}: {str(e)}")
