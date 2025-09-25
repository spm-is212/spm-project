"""
Task model representing the tasks table in Supabase
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime

class Task:
    """
    Tasks table columns in Supabase database
    """
    id: str
    parent_id: Optional[str]
    title: str
    description: str
    due_date: date
    status: str  # TO_DO, IN_PROGRESS, COMPLETED, BLOCKED
    priority: str  # LOW, MEDIUM, HIGH
    owner_user_id: str
    assignee_ids: List[str]
    comments: List[Dict[str, Any]]
    attachments: List[Dict[str, Any]]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
