from fastapi import FastAPI
from backend.routers import auth, task, health, crud_test

app = FastAPI(title="SPM Project API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(crud_test.router)


from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.routers import auth, task, health, crud_test
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="SPM Project API")

# OAuth2PasswordBearer instance to manage token dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT settings (use environment variables for production)
SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")  # Ensure this is stored securely
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Include existing routers (no changes needed here)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(crud_test.router)

# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta  # Use UTC for expiration
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to verify and decode JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

# Example of JWT login route (assumes you already have Supabase client elsewhere in the code)
@app.post("/token")
async def login_for_access_token(form_data: auth.User):
    # Use the Supabase client initialized elsewhere to get the user details
    user = await auth.get_user_from_db(form_data.username)
    
    if not user or user["password"] != form_data.password:  # Note: Make sure passwords are hashed
        raise HTTPException(
            status_code=401, detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected route (using JWT authentication)
@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, you are authenticated!"}

# Example of role-based access: Only admin can access this route
@app.get("/admin")
async def admin_route(current_user: str = Depends(get_current_user)):
    user = await auth.login(current_user)  # Use your existing Supabase query method
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"message": "Welcome Admin!"}

