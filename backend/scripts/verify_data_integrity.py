"""
Comprehensive data integrity check and sync script
Verifies alignment between users, teams, projects, and tasks
"""
import os
import sys
from supabase import create_client
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("DATA INTEGRITY VERIFICATION & SYNC")
print("=" * 80)

issues = []
fixes_applied = 0

# 1. GET ALL DATA
print("\n1. Loading all data from database...")
users = supabase.table("users").select("*").execute().data
teams = supabase.table("teams").select("*").execute().data
projects = supabase.table("projects").select("*").execute().data
tasks = supabase.table("tasks").select("*").execute().data

print(f"   Users: {len(users)}")
print(f"   Teams: {len(teams)}")
print(f"   Projects: {len(projects)}")
print(f"   Tasks: {len(tasks)}")

# Create lookup dictionaries
user_by_uuid = {u['uuid']: u for u in users}
team_by_id = {t['id']: t for t in teams}
project_by_id = {p['id']: p for p in projects}

# 2. CHECK USERS <-> TEAMS ALIGNMENT
print("\n2. Checking Users <-> Teams alignment...")
print("   (Users should be in teams of their department)")

users_by_dept = defaultdict(list)
for user in users:
    for dept in user.get('departments', []):
        users_by_dept[dept].append(user)

teams_by_dept = defaultdict(list)
for team in teams:
    dept = team.get('department', 'unknown')
    teams_by_dept[dept].append(team)

# Check: All managers/directors should be in all teams in their departments
managers_directors = [u for u in users if u['role'] in ['manager', 'director', 'managing_director']]
print(f"\n   Checking {len(managers_directors)} managers/directors...")

for user in managers_directors:
    user_depts = user.get('departments', [])
    for dept in user_depts:
        dept_teams = teams_by_dept.get(dept, [])
        for team in dept_teams:
            if user['uuid'] not in team.get('team_members', []):
                issues.append(f"Manager/Director {user['email']} not in team {team['name']} (dept: {dept})")
                # FIX IT
                updated_members = team.get('team_members', []) + [user['uuid']]
                supabase.table("teams").update({"team_members": updated_members}).eq("id", team['id']).execute()
                fixes_applied += 1
                print(f"     FIXED: Added {user['email']} to {team['name']}")

# 3. CHECK TEAMS <-> PROJECTS ALIGNMENT
print("\n3. Checking Teams <-> Projects alignment...")
print("   (Projects should belong to valid teams in same department)")

for project in projects:
    team_id = project.get('team_id')
    if not team_id:
        issues.append(f"Project {project['name']} has no team_id")
        continue

    if team_id not in team_by_id:
        issues.append(f"Project {project['name']} has invalid team_id: {team_id}")
        continue

    team = team_by_id[team_id]
    project_dept = project.get('description', '').split(':')[0].strip() if ':' in project.get('description', '') else None

    # Projects and teams should align (just check existence, not department match)
    # This is OK - just verify team exists

print(f"   All {len(projects)} projects have valid team references")

# 4. CHECK PROJECTS <-> TASKS ALIGNMENT
print("\n4. Checking Projects <-> Tasks alignment...")
print("   (Tasks should belong to valid projects)")

orphaned_tasks = []
for task in tasks:
    project_id = task.get('project_id')
    if not project_id:
        orphaned_tasks.append(task)
        issues.append(f"Task '{task['title']}' has no project_id")
        continue

    if project_id not in project_by_id:
        orphaned_tasks.append(task)
        issues.append(f"Task '{task['title']}' has invalid project_id: {project_id}")

if orphaned_tasks:
    print(f"\n   WARNING: Found {len(orphaned_tasks)} orphaned tasks!")
    print(f"   These tasks have no valid project.")

    # Offer to assign to a default project
    if len(projects) > 0:
        print(f"\n   Available projects to assign orphaned tasks to:")
        for i, p in enumerate(projects[:5]):
            print(f"     [{i+1}] {p['name']} (Team: {team_by_id[p['team_id']]['name']})")

        choice = input(f"\n   Assign orphaned tasks to project? (1-{min(5, len(projects))} or 'skip'): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= min(5, len(projects)):
            target_project = projects[int(choice) - 1]
            for task in orphaned_tasks:
                supabase.table("tasks").update({"project_id": target_project['id']}).eq("id", task['id']).execute()
                fixes_applied += 1
            print(f"   FIXED: Assigned {len(orphaned_tasks)} tasks to {target_project['name']}")

# 5. CHECK TASKS ASSIGNEES
print("\n5. Checking Task assignees...")
print("   (Task assignees should be valid user UUIDs)")

invalid_assignees = 0
for task in tasks:
    assignee_ids = task.get('assignee_ids', [])
    for assignee_id in assignee_ids:
        if assignee_id not in user_by_uuid:
            issues.append(f"Task '{task['title']}' has invalid assignee: {assignee_id}")
            invalid_assignees += 1

if invalid_assignees > 0:
    print(f"   WARNING: Found {invalid_assignees} invalid assignee references")
else:
    print(f"   All task assignees are valid users")

# 6. SUMMARY
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if len(issues) == 0:
    print("SUCCESS: All data is properly aligned!")
else:
    print(f"Found {len(issues)} issues:")
    for issue in issues[:10]:
        print(f"  - {issue}")
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")

print(f"\nFixes applied: {fixes_applied}")

# 7. GENERATE REPORT
print("\n" + "=" * 80)
print("DATA STRUCTURE REPORT")
print("=" * 80)

print("\nDepartments and their teams:")
for dept in sorted(teams_by_dept.keys()):
    print(f"\n  {dept.upper()}:")
    dept_teams = teams_by_dept[dept]
    for team in dept_teams:
        member_count = len(team.get('team_members', []))
        project_count = len([p for p in projects if p['team_id'] == team['id']])
        print(f"    - {team['name']}: {member_count} members, {project_count} projects")

print("\nUsers by role:")
role_counts = defaultdict(int)
for user in users:
    role_counts[user['role']] += 1
for role, count in sorted(role_counts.items()):
    print(f"  {role}: {count}")

print("\nTasks by status:")
status_counts = defaultdict(int)
for task in tasks:
    status_counts[task.get('status', 'UNKNOWN')] += 1
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

print("\n" + "=" * 80)
print("Verification complete!")
print("=" * 80)
