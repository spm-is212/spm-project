from pydantic import BaseModel, EmailStr


# Input schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "staff"  # default role


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Output schemas
class UserResponse(BaseModel):
    uuid: str
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
