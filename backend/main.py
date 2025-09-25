from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from backend.routers import auth, task, health, crud_test

app = FastAPI(title="SPM Project API")

origins = [
    "http://localhost:5173",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(crud_test.router)
