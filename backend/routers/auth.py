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

    token = create_access_token({"sub": db_user["uuid"], "role": db_user["role"]})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    return {"message": "Logged out (frontend should delete token)"}


@router.get("/users/department")
def get_users_by_current_user_department(user: dict = Depends(get_current_user)):
    """Get list of users from current user's department for task assignment"""
    try:
        user_id = user["sub"]

        user_manager = UserManager()
        current_user_data = user_manager.get_current_user_data(user_id)
        if not current_user_data:
            raise HTTPException(status_code=404, detail="User not found")

        user_departments = current_user_data.get("departments")
        if not user_departments:
            raise HTTPException(status_code=400, detail="User has no departments assigned")

        all_users = []
        seen_user_ids = set()

        for dept in user_departments:
            dept_users = user_manager.get_users_by_department(dept)
            for user in dept_users:
                if user["id"] not in seen_user_ids:
                    all_users.append(user)
                    seen_user_ids.add(user["id"])

        users = all_users

        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
