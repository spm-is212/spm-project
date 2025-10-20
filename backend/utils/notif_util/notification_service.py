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
        """Send in-app and email notifications when a task event occurs."""
        timestamp = datetime.utcnow().isoformat()
        task_title = task.get("title", "Untitled Task")
        due_date = task.get("due_date", "No due date")

        # --- In-app notifications ---
        for receiver_id in receivers:
            self.create_in_app_notification(sender_id, receiver_id, action, task)

        # --- Email notifications ---
        if email_receivers:
            for email in email_receivers:
                subject = f"Task '{task_title}' {action}"
                body = (
                    f"Hi,\n\n"
                    f"The task **'{task_title}'** was {action} by user {sender_id}.\n"
                    f"Due: {due_date}\n"
                    f"Timestamp: {timestamp}\n\n"
                    f"View this task in your workspace for more details."
                )
                try:
                    self.send_email_notification(email, subject, body)
                except Exception as e:
                    print(f"[NotificationService] Failed to send email to {email}: {e}")