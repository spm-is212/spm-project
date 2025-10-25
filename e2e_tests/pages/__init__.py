"""
Page Objects Package
"""
from .login_page import LoginPage
from .dashboard_page import DashboardPage
from .task_page import TaskPage
from .project_page import ProjectPage

__all__ = ["LoginPage", "DashboardPage", "TaskPage", "ProjectPage"]
