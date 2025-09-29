from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.schemas.user import UserCreate, UserResponse, TokenResponse
from backend.utils.security import hash_password, verify_password, create_access_token, get_current_user

from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.utils.user_crud.user_manager import UserManager

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate):
    existing = SupabaseCRUD().client.table("users").select("*").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    result = (
        SupabaseCRUD().client.table("users")
        .insert({"email": user.email, "password_hash": hashed_pw, "role": user.role, "departments": user.departments})
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to register user")

    return result.data[0]


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    result = SupabaseCRUD().client.table("users").select("*").eq("email", form_data.username).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_user = result.data[0]
    if not verify_password(form_data.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": db_user["uuid"],
        "role": db_user["role"],
        "teams": db_user.get("teams", []),
        "departments": db_user.get("departments", [])
    })
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    return {"message": "Logged out (frontend should delete token)"}


@router.get("/users")
def get_all_users_for_assignment(user: dict = Depends(get_current_user)):
    """Get list of all users for task assignment"""
    try:
        user_manager = UserManager()
        all_users = user_manager.get_all_users()
        return {"users": all_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
