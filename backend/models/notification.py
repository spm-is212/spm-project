from datetime import datetime
from typing import Optional

class Notification:

    id: int                       
    sender_id: str                 # uuid of the sender (user who triggered the action)
    receiver_id: str               # uuid of the receiver (who sees the notification)
    task_id: Optional[int]       
    action: str                    # e.g. "created", "updated", "completed", "reminder"
    message: str                 
    timestamp: datetime           