from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from backend.utils.security import get_current_user
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/")
def get_notifications(
    limit: Optional[int] = Query(50, description="Max notifications to return"),
    user: dict = Depends(get_current_user),
):
    """
    Return all notifications for the authenticated user (no read/unread filtering).
    """
    try:
        user_id = user["sub"]
        crud = SupabaseCRUD()
        notifications = crud.select("notifications", filters={"receiver_id": user_id}) or []
        return {"notifications": notifications[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {e}")

@router.delete("/clear")
def clear_notifications(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    crud = SupabaseCRUD()
    crud.delete("notifications", filters={"receiver_id": user_id})
    return {"message": "All notifications deleted"}
