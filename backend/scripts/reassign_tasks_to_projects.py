"""
Script to reassign tasks to correct project IDs based on current team structure
"""
import os
import sys
from supabase import create_client

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def main():
    print("=" * 80)
    print("TASK REASSIGNMENT SCRIPT")
    print("=" * 80)

    # 1. Get all teams
    print("\n1. Fetching teams...")
    teams_response = supabase.table("teams").select("*").execute()
    teams = teams_response.data
    print(f"   Found {len(teams)} teams:")
    for team in teams:
        print(f"   - {team['name']} (ID: {team['id']})")

    # 2. Get all projects
    print("\n2. Fetching projects...")
    projects_response = supabase.table("projects").select("*").execute()
    projects = projects_response.data
    print(f"   Found {len(projects)} projects:")
    for project in projects:
        print(f"   - {project['name']} (ID: {project['id']}, Team: {project['team_id']})")

    # 3. Get all tasks
    print("\n3. Fetching tasks...")
    tasks_response = supabase.table("tasks").select("id, title, project_id").execute()
    tasks = tasks_response.data
    print(f"   Found {len(tasks)} tasks")

    # 4. Find tasks with invalid project_ids
    valid_project_ids = {p['id'] for p in projects}
    invalid_tasks = [t for t in tasks if t['project_id'] not in valid_project_ids]

    print(f"\n4. Found {len(invalid_tasks)} tasks with invalid project IDs:")
    for task in invalid_tasks[:5]:  # Show first 5
        print(f"   - '{task['title']}' (ID: {task['id']}, Project ID: {task['project_id']})")
    if len(invalid_tasks) > 5:
        print(f"   ... and {len(invalid_tasks) - 5} more")

    if len(invalid_tasks) == 0:
        print("\n✓ All tasks already have valid project IDs!")
        return

    # 5. Ask user which project to assign tasks to
    if len(projects) == 0:
        print("\nError: No projects found. Please create projects first.")
        return

    print("\n5. Select a project to assign all orphaned tasks to:")
    for i, project in enumerate(projects):
        print(f"   [{i+1}] {project['name']} (Team: {project['team_id']})")

    choice = input(f"\nEnter project number (1-{len(projects)}), or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        print("Cancelled.")
        return

    try:
        project_index = int(choice) - 1
        if project_index < 0 or project_index >= len(projects):
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid input.")
        return

    selected_project = projects[project_index]
    print(f"\n✓ Selected: {selected_project['name']}")

    # 6. Confirm
    confirm = input(f"\nReassign {len(invalid_tasks)} tasks to '{selected_project['name']}'? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("Cancelled.")
        return

    # 7. Update tasks
    print(f"\n6. Updating {len(invalid_tasks)} tasks...")
    updated_count = 0

    for task in invalid_tasks:
        try:
            supabase.table("tasks").update({
                "project_id": selected_project['id']
            }).eq("id", task['id']).execute()
            updated_count += 1
            print(f"   ✓ Updated task: {task['title']}")
        except Exception as e:
            print(f"   ✗ Failed to update task {task['id']}: {e}")

    print(f"\n✓ Successfully updated {updated_count}/{len(invalid_tasks)} tasks!")
    print(f"All updated tasks are now assigned to project: {selected_project['name']}")

if __name__ == "__main__":
    main()
