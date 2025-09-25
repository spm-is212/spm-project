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
        # Get all users and filter by department (works with test table patches)
        all_users = self.crud.select(self.table_name, columns="uuid, email, role, departments")

        # Filter users that have the department in their departments array
        department_users = []
        for user in all_users:
            user_departments = user.get("departments", [])
            if isinstance(user_departments, list) and department in user_departments:
                department_users.append(user)

        return [
            {
                "id": user["uuid"],
                "email": user["email"],
                "username": user["email"].split("@")[0],
                "role": user["role"],
                "departments": user["departments"]
            }
            for user in department_users
        ]

    def get_users_by_team(self, team: str) -> List[Dict[str, Any]]:
        """
        Get users by team

        Args:
            team: Team name

        Returns:
            List of user dictionaries from the specified team
        """
        # Get all users and filter by team (works with test table patches)
        all_users = self.crud.select(self.table_name, columns="uuid, email, role, departments, teams")

        # Filter users that have the team in their teams array
        team_users = []
        for user in all_users:
            user_teams = user.get("teams", [])
            if isinstance(user_teams, list) and team in user_teams:
                team_users.append(user)

        return [
            {
                "id": user["uuid"],
                "email": user["email"],
                "username": user["email"].split("@")[0],
                "role": user["role"],
                "departments": user["departments"],
                "teams": user.get("teams", [])
            }
            for user in team_users
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
