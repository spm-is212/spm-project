from fastapi import APIRouter, HTTPException
from backend.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.utils.security import hash_password, verify_password, create_access_token
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    result = SupabaseCRUD().client.table("users").select("*").eq("email", user.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_user = result.data[0]
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user["uuid"], "role": db_user["role"]})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    return {"message": "Logged out (frontend should delete token)"}
