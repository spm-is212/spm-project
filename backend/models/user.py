"""
User model representing the users table in Supabase
"""

from typing import List
from datetime import datetime

class User:
    """
    Users table columns in Supabase database
    """
    uuid: str
    email: str
    password_hash: str
    role: str
    departments: List[str]
    teams: List[str]
    created_at: datetime
    updated_at: datetime
