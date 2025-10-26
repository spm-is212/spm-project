from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
import os

# Routers
from backend.routers import auth, task, health, crud_test, project, reports, notification

# Your new job
from backend.jobs.due_soon_notifier import send_due_soon_notifications

app = FastAPI(title="SPM Project API")

# --- CORS setup ---
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

# --- Routers ---
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(crud_test.router)
app.include_router(project.router)
app.include_router(reports.router)
app.include_router(notification.router)

# --- APScheduler setup ---
scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Singapore"))

@app.on_event("startup")
async def startup_event():
    """Start scheduler once when FastAPI starts"""
    if os.getenv("SCHEDULER_ENABLED", "1") == "1" and not scheduler.running:
        # every midnight (00:00 Singapore time)
        scheduler.add_job(send_due_soon_notifications, "cron", hour=0, minute=0)
        scheduler.start()
        print("[Scheduler] Started daily due-soon job at midnight (Asia/Singapore)")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler cleanly on app shutdown"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Shutdown complete")
