from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD


class UserManager:
    """
    User management utilities
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.table_name = "users"

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users

        Returns:
            List of user dictionaries
        """
        users = self.crud.select(self.table_name, columns="uuid, email, role, departments")

        return [
            {
                "id": user["uuid"],
                "email": user["email"],
                "username": user["email"].split("@")[0],
                "role": user["role"],
                "departments": user.get("departments", [])
            }
            for user in users
        ]

    def get_users_by_department(self, department: str) -> List[Dict[str, Any]]:
        """
        Get users by department

        Args:
            department: Department name

        Returns:
            List of user dictionaries from the specified department
        """
        # Use Supabase client directly for array contains operation
        result = self.crud.client.table(self.table_name).select("uuid, email, role, departments").contains("departments", [department]).execute()
        users = result.data

        return [
            {
                "id": user["uuid"],
                "email": user["email"],
                "username": user["email"].split("@")[0],
                "role": user["role"],
                "departments": user["departments"]
            }
            for user in users
        ]

    def get_current_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current user's data by user ID

        Args:
            user_id: User ID from JWT token

        Returns:
            User dictionary or None if not found
        """
        users = self.crud.select(
            self.table_name,
            columns="uuid, email, role, departments",
            filters={"uuid": user_id}
        )

        if not users:
            return None

        user = users[0]
        return {
            "id": user["uuid"],
            "email": user["email"],
            "username": user["email"].split("@")[0],
            "role": user["role"],
            "departments": user.get("departments")
        }
