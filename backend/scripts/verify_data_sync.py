"""
Script to verify data synchronization and relationships across all tables
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from collections import defaultdict

def verify_data_sync():
    """Verify data synchronization across users, tasks, projects"""
    crud = SupabaseCRUD()
    client = crud.client

    print("=" * 80)
    print("DATABASE SYNCHRONIZATION VERIFICATION")
    print("=" * 80)

    # Fetch all data
    try:
        users = client.table('users').select('*').execute().data or []
        tasks = client.table('tasks').select('*').execute().data or []
        projects = client.table('projects').select('*').execute().data or []
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return

    print(f"\n📊 SUMMARY:")
    print(f"   Users: {len(users)}")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Projects: {len(projects)}")

    # Extract unique IDs
    user_ids = {u['uuid'] for u in users}
    project_ids = {p['id'] for p in projects}
    team_ids = {p['team_id'] for p in projects}  # Get team_ids from projects

    print("\n" + "=" * 80)
    print("🔍 CHECKING DATA RELATIONSHIPS")
    print("=" * 80)

    # 1. Check tasks → users relationship
    print("\n1️⃣ TASK → USER RELATIONSHIPS:")
    orphaned_tasks_owner = []
    orphaned_tasks_assignee = []

    for task in tasks:
        # Check owner
        if task.get('owner_user_id') not in user_ids:
            orphaned_tasks_owner.append({
                'id': task['id'],
                'title': task['title'],
                'owner_id': task.get('owner_user_id')
            })

        # Check assignees
        for assignee_id in task.get('assignee_ids', []):
            if assignee_id not in user_ids:
                orphaned_tasks_assignee.append({
                    'id': task['id'],
                    'title': task['title'],
                    'missing_assignee': assignee_id
                })

    if orphaned_tasks_owner:
        print(f"   ⚠️  {len(orphaned_tasks_owner)} tasks have invalid owner_user_id:")
        for t in orphaned_tasks_owner[:5]:
            print(f"      - {t['title']} (owner: {t['owner_id']})")
        if len(orphaned_tasks_owner) > 5:
            print(f"      ... and {len(orphaned_tasks_owner) - 5} more")
    else:
        print("   ✅ All tasks have valid owners")

    if orphaned_tasks_assignee:
        print(f"   ⚠️  {len(orphaned_tasks_assignee)} task assignments reference non-existent users")
    else:
        print("   ✅ All task assignees are valid users")

    # 2. Check tasks → projects relationship
    print("\n2️⃣ TASK → PROJECT RELATIONSHIPS:")
    tasks_with_projects = [t for t in tasks if t.get('project_id')]
    tasks_without_projects = [t for t in tasks if not t.get('project_id')]

    print(f"   📋 {len(tasks_with_projects)} tasks linked to projects")
    print(f"   📋 {len(tasks_without_projects)} tasks WITHOUT projects")

    orphaned_tasks_project = []
    for task in tasks_with_projects:
        if task.get('project_id') not in project_ids:
            orphaned_tasks_project.append({
                'id': task['id'],
                'title': task['title'],
                'project_id': task.get('project_id')
            })

    if orphaned_tasks_project:
        print(f"   ⚠️  {len(orphaned_tasks_project)} tasks reference non-existent projects:")
        for t in orphaned_tasks_project[:5]:
            print(f"      - {t['title']} (project: {t['project_id']})")
    else:
        print("   ✅ All task project references are valid")

    # 3. Check projects → teams relationship
    print("\n3️⃣ PROJECT → TEAM RELATIONSHIPS:")
    print(f"   📁 {len(projects)} projects across {len(team_ids)} unique teams")
    print(f"   Team IDs found: {sorted(team_ids)}")
    print("   ⚠️  NOTE: Teams table doesn't exist - team_id is just a string reference")

    # 4. Check parent-child task relationships
    print("\n4️⃣ PARENT-CHILD TASK RELATIONSHIPS:")
    main_tasks = [t for t in tasks if not t.get('parent_id')]
    subtasks = [t for t in tasks if t.get('parent_id')]

    print(f"   🔷 {len(main_tasks)} main tasks (parent tasks)")
    print(f"   🔸 {len(subtasks)} subtasks")

    # Check if subtasks reference valid parent tasks
    task_ids = {t['id'] for t in tasks}
    orphaned_subtasks = []

    for subtask in subtasks:
        if subtask.get('parent_id') not in task_ids:
            orphaned_subtasks.append({
                'id': subtask['id'],
                'title': subtask['title'],
                'parent_id': subtask.get('parent_id')
            })

    if orphaned_subtasks:
        print(f"   ⚠️  {len(orphaned_subtasks)} subtasks have invalid parent_id:")
        for t in orphaned_subtasks[:5]:
            print(f"      - {t['title']} (parent: {t['parent_id']})")
    else:
        print("   ✅ All subtasks have valid parent tasks")

    # 5. User departments and teams
    print("\n5️⃣ USER DEPARTMENTS & TEAMS:")
    users_with_depts = [u for u in users if u.get('departments')]
    users_with_teams = [u for u in users if u.get('teams')]

    print(f"   👥 {len(users_with_depts)}/{len(users)} users have departments")
    print(f"   👥 {len(users_with_teams)}/{len(users)} users have teams")

    # Get unique departments
    all_departments = set()
    for user in users_with_depts:
        if isinstance(user.get('departments'), list):
            all_departments.update(user['departments'])

    print(f"   📍 Unique departments: {sorted(all_departments) if all_departments else 'None'}")

    # 6. Projects per team
    print("\n6️⃣ PROJECTS PER TEAM:")
    projects_by_team = defaultdict(list)
    for project in projects:
        projects_by_team[project['team_id']].append(project['name'])

    for team_id, project_names in sorted(projects_by_team.items()):
        print(f"   📁 {team_id}: {len(project_names)} projects")
        for name in project_names:
            print(f"      - {name}")

    # 7. Check for tasks without project but should have
    print("\n7️⃣ RECOMMENDATIONS:")
    print("=" * 80)

    if tasks_without_projects:
        print(f"\n⚠️  ACTION NEEDED: {len(tasks_without_projects)} tasks have no project assignment")
        print("   Consider linking these tasks to projects:")
        for t in tasks_without_projects[:5]:
            print(f"   - {t['title']}")

    if orphaned_tasks_owner or orphaned_tasks_assignee or orphaned_tasks_project:
        print("\n⚠️  DATA INTEGRITY ISSUES FOUND:")
        if orphaned_tasks_owner:
            print(f"   - Fix {len(orphaned_tasks_owner)} tasks with invalid owner_user_id")
        if orphaned_tasks_assignee:
            print(f"   - Fix {len(orphaned_tasks_assignee)} task assignments with invalid user IDs")
        if orphaned_tasks_project:
            print(f"   - Fix {len(orphaned_tasks_project)} tasks with invalid project_id")

    if not any([orphaned_tasks_owner, orphaned_tasks_assignee, orphaned_tasks_project, orphaned_subtasks]):
        print("\n✅ DATA INTEGRITY: All relationships are valid!")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("\n1. Create teams table to properly manage team data")
    print("2. Link all tasks to appropriate projects")
    print("3. Ensure all users have departments and teams assigned")
    print("4. Fix any orphaned references found above")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_data_sync()
