from fastapi import FastAPI
from backend.routers import auth, task, health

app = FastAPI(title="SPM Project API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
