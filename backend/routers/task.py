from fastapi import APIRouter, Depends
from utils.security import get_current_user, require_role

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Staff & Managers can create tasks
@router.post("/", dependencies=[Depends(require_role(["staff", "manager"]))])
def create_task(user=Depends(get_current_user)):
    # return {"message": f"Task created by {user['role']}"}
    pass

# Only Managers/Directors can assign tasks
@router.post("/assign", dependencies=[Depends(require_role(["manager", "director"]))])
def assign_task(user=Depends(get_current_user)):
    # return {"message": f"Task assigned by {user['role']}"}
    pass

@router.get("/reports", dependencies=[Depends(require_role(["manager", "director"]))])
def view_reports():
    # return {"message": "Report data"}
    pass

@router.get("/audit", dependencies=[Depends(require_role(["hr"]))])
def audit_logs():
    # return {"message": "HR-only audit logs"}
    pass
