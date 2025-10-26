from datetime import datetime, timedelta
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.utils.notif_util.notification_service import NotificationService

def send_due_soon_notifications():
    crud = SupabaseCRUD()
    ns = NotificationService()
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)

    tasks = crud.select("tasks", filters={
        "is_archived": False
    })

    for task in tasks:
        due_date_str = task.get("due_date")
        if not due_date_str:
            continue

        due_date = datetime.fromisoformat(due_date_str)
        if now < due_date <= tomorrow:
            title = task["title"]
            receivers = task.get("assignee_ids", [])
            ns.notify_task_event(
                sender_id="system",
                action="due soon",
                task=task,
                receivers=receivers,
                email_receivers=[u["email"] for u in task.get("assignees", [])]
            )
            print(f"Sent 'due soon' reminder for task '{title}'")
