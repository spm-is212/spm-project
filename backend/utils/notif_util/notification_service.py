from datetime import datetime
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.utils.notif_util.email_utils import send_email  # create this helper

class NotificationService:
    def __init__(self):
        self.crud = SupabaseCRUD()

    def create_in_app_notification(self, sender_id, receiver_id, action, task):
        message = f"Task '{task['title']}' was {action}."
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "task_id": task["id"],
            "action": action,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            self.crud.insert("notifications", data)
        except Exception as e:
            print(f"Insert failed: {e}")
        return data

    def send_email_notification(self, receiver_email, subject, body):
        send_email(receiver_email, subject, body)

    def notify_task_event(self, sender_id, action, task, receivers, email_receivers=None):
        for receiver_id in receivers:
            self.create_in_app_notification(sender_id, receiver_id, action, task)
        if email_receivers:
            for email in email_receivers:
                subject = f"Task '{task['title']}' {action}"
                body = f"The task '{task['title']}' was {action}.\nDue: {task.get('due_date')}"
                self.send_email_notification(email, subject, body)
