"""
Test user data for E2E tests
"""

TEST_USERS = {
    "admin": {
        "email": "senior_engineer@allinone.com",
        "password": "password123",
        "role": "admin"
    },
    "manager": {
        "email": "derek_tan@allinone.com",
        "password": "password123",
        "role": "manager"
    },
    "staff": {
        "email": "jack_sim@allinone.com",
        "password": "password123",
        "role": "staff"
    }
}

TEST_TASKS = {
    "basic_task": {
        "title": "Test Task",
        "description": "This is a test task description",
        "priority": "5",
        "status": "TO_DO"
    },
    "high_priority_task": {
        "title": "Urgent Task",
        "description": "High priority urgent task",
        "priority": "9",
        "status": "IN_PROGRESS"
    }
}

TEST_PROJECTS = {
    "basic_project": {
        "name": "Test Project",
        "description": "This is a test project"
    }
}
