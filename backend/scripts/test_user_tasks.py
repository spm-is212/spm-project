"""
Test script to verify user can see tasks in their team's projects
"""
import os
import sys
from supabase import create_client
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("USER TASK VISIBILITY TEST")
print("=" * 80)

# Get a user (you can change this email to test with a specific user)
test_email = input("\nEnter user email to test (or press Enter for first user): ").strip()

if test_email:
    user_result = supabase.table("users").select("*").eq("email", test_email).execute()
else:
    user_result = supabase.table("users").select("*").limit(1).execute()

if not user_result.data:
    print("No user found!")
    sys.exit(1)

user = user_result.data[0]
print(f"\n1. Testing with user: {user['email']}")
print(f"   UUID: {user['uuid']}")
print(f"   Role: {user['role']}")
print(f"   Departments: {user['departments']}")

# Get user's teams
print(f"\n2. Finding user's teams...")
teams_result = supabase.table("teams").select("*").contains("team_members", [user['uuid']]).execute()
user_teams = teams_result.data

print(f"   Found {len(user_teams)} teams where user is a member:")
for team in user_teams:
    print(f"   - {team['name']} (ID: {team['id']}, Members: {len(team['team_members'])})")

if len(user_teams) == 0:
    print("\n   ⚠️  User is not a member of any teams!")
    print("   This is why no projects/tasks are showing.")
    sys.exit(0)

# Get team IDs
team_ids = [team['id'] for team in user_teams]

# Get projects for those teams
print(f"\n3. Finding projects in user's teams...")
projects_result = supabase.table("projects").select("*").in_("team_id", team_ids).execute()
user_projects = projects_result.data

print(f"   Found {len(user_projects)} projects:")
for project in user_projects[:5]:  # Show first 5
    print(f"   - {project['name']} (ID: {project['id']}, Team: {project['team_id']})")
if len(user_projects) > 5:
    print(f"   ... and {len(user_projects) - 5} more")

if len(user_projects) == 0:
    print("\n   ⚠️  No projects found in user's teams!")
    print("   This is why no tasks are showing.")
    sys.exit(0)

# Get project IDs
project_ids = [project['id'] for project in user_projects]

# Get tasks for those projects
print(f"\n4. Finding tasks in user's projects...")
tasks_result = supabase.table("tasks").select("*").in_("project_id", project_ids).execute()
user_tasks = tasks_result.data

print(f"   Found {len(user_tasks)} tasks:")
for task in user_tasks[:5]:  # Show first 5
    assignee_count = len(task.get('assignee_ids', []))
    print(f"   - {task['title']}")
    print(f"     Project: {task['project_id']}, Status: {task['status']}, Assignees: {assignee_count}")
if len(user_tasks) > 5:
    print(f"   ... and {len(user_tasks) - 5} more")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"User should see:")
print(f"  ✓ {len(user_teams)} team(s)")
print(f"  ✓ {len(user_projects)} project(s)")
print(f"  ✓ {len(user_tasks)} task(s)")

if len(user_tasks) == 0:
    print("\n⚠️  NO TASKS FOUND!")
    print("Would you like to create a test task? (yes/no): ", end="")
    create_task = input().strip().lower()

    if create_task == 'yes' and len(user_projects) > 0:
        project = user_projects[0]
        print(f"\nCreating test task in project: {project['name']}")

        new_task = {
            "title": f"Test Task - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": "This is a test task created to verify task visibility",
            "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "status": "TO_DO",
            "priority": "MEDIUM",
            "owner_user_id": user['uuid'],
            "assignee_ids": [user['uuid']],
            "project_id": project['id'],
            "is_archived": False,
            "comments": [],
            "attachments": []
        }

        result = supabase.table("tasks").insert(new_task).execute()
        if result.data:
            print(f"✓ Test task created successfully!")
            print(f"  Task ID: {result.data[0]['id']}")
            print(f"  Title: {result.data[0]['title']}")
            print(f"\nNow refresh your browser and you should see this task!")
        else:
            print("✗ Failed to create task")
    else:
        print("\nNo task created.")
else:
    print(f"\n✓ User should see {len(user_tasks)} tasks in the UI!")
