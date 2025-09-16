from fastapi import APIRouter, HTTPException
from supabase import create_client
from schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from utils.security import hash_password, verify_password, create_access_token
import os
from dotenv import load_dotenv

load_dotenv()


router = APIRouter(prefix="/api/auth", tags=["auth"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate):
    existing = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    result = supabase.table("users").insert({
        "email": user.email,
        "password_hash": hashed_pw,
        "role": user.role
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to register user")

    return result.data[0]


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    result = supabase.table("users").select("*").eq("email", user.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_user = result.data[0]
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": db_user["id"],
        "role": db_user["role"]
    })

    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    return {"message": "Logged out (frontend should delete token)"}
