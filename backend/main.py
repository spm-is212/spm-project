from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, task, health, crud_test, project, reports , notification

app = FastAPI(title="SPM Project API")

# CORS middleware BEFORE routers (correct order!)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(crud_test.router)
app.include_router(project.router)
app.include_router(reports.router)
app.include_router(notification.router)
