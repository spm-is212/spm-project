"""
Script to verify that all tasks are linked to projects
Based on data model: User -> Projects -> Tasks -> Subtasks
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

def verify_task_project_links():
    """Verify that all tasks have a valid project_id"""
    crud = SupabaseCRUD()
    client = crud.client

    print("=" * 80)
    print("TASK-PROJECT RELATIONSHIP VERIFICATION")
    print("=" * 80)
    print("\nData Model: User -> Projects -> Tasks -> Subtasks")
    print("Rule: ALL tasks must be tagged to a project\n")

    try:
        # Fetch all data
        tasks = client.table('tasks').select('*').execute().data or []
        projects = client.table('projects').select('*').execute().data or []
        users = client.table('users').select('*').execute().data or []

        print(f"📊 Current Database State:")
        print(f"   Users: {len(users)}")
        print(f"   Projects: {len(projects)}")
        print(f"   Tasks: {len(tasks)}")

        # Get valid project IDs
        project_ids = {p['id'] for p in projects}
        print(f"\n   Valid Project IDs: {len(project_ids)}")

        # Separate main tasks and subtasks
        main_tasks = [t for t in tasks if not t.get('parent_id')]
        subtasks = [t for t in tasks if t.get('parent_id')]

        print(f"   Main Tasks: {len(main_tasks)}")
        print(f"   Subtasks: {len(subtasks)}")

        # Check 1: Tasks without project_id
        print("\n" + "=" * 80)
        print("CHECK 1: Tasks Without Project Assignment")
        print("=" * 80)

        tasks_without_project = [t for t in tasks if not t.get('project_id')]

        if tasks_without_project:
            print(f"\n❌ VIOLATION: {len(tasks_without_project)} tasks have NO project_id")
            print("\nTasks missing project assignment:")
            for task in tasks_without_project[:10]:
                task_type = "Subtask" if task.get('parent_id') else "Main Task"
                print(f"   - [{task_type}] {task['title']} (ID: {task['id']})")
                if task.get('parent_id'):
                    print(f"     Parent ID: {task['parent_id']}")
            if len(tasks_without_project) > 10:
                print(f"   ... and {len(tasks_without_project) - 10} more")
        else:
            print("\n✅ PASS: All tasks have a project_id assigned")

        # Check 2: Tasks with invalid project_id
        print("\n" + "=" * 80)
        print("CHECK 2: Tasks With Invalid Project References")
        print("=" * 80)

        tasks_with_invalid_project = []
        for task in tasks:
            if task.get('project_id') and task['project_id'] not in project_ids:
                tasks_with_invalid_project.append(task)

        if tasks_with_invalid_project:
            print(f"\n❌ VIOLATION: {len(tasks_with_invalid_project)} tasks reference non-existent projects")
            print("\nTasks with invalid project_id:")
            for task in tasks_with_invalid_project[:10]:
                print(f"   - {task['title']}")
                print(f"     Task ID: {task['id']}")
                print(f"     Invalid Project ID: {task['project_id']}")
            if len(tasks_with_invalid_project) > 10:
                print(f"   ... and {len(tasks_with_invalid_project) - 10} more")
        else:
            print("\n✅ PASS: All tasks with project_id reference valid projects")

        # Check 3: Subtask parent relationships
        print("\n" + "=" * 80)
        print("CHECK 3: Subtask Parent Relationships")
        print("=" * 80)

        task_ids = {t['id'] for t in tasks}
        orphaned_subtasks = []

        for subtask in subtasks:
            if subtask.get('parent_id') not in task_ids:
                orphaned_subtasks.append(subtask)

        if orphaned_subtasks:
            print(f"\n❌ VIOLATION: {len(orphaned_subtasks)} subtasks have invalid parent_id")
            for subtask in orphaned_subtasks[:5]:
                print(f"   - {subtask['title']}")
                print(f"     Subtask ID: {subtask['id']}")
                print(f"     Invalid Parent ID: {subtask.get('parent_id')}")
        else:
            print("\n✅ PASS: All subtasks have valid parent tasks")

        # Check 4: Project ownership
        print("\n" + "=" * 80)
        print("CHECK 4: Project Ownership")
        print("=" * 80)

        user_ids = {u['uuid'] for u in users}

        # Count projects per user (from tasks)
        projects_by_user = {}
        for task in tasks:
            if task.get('owner_user_id') and task.get('project_id'):
                owner = task['owner_user_id']
                project = task['project_id']
                if owner not in projects_by_user:
                    projects_by_user[owner] = set()
                projects_by_user[owner].add(project)

        print(f"\n📊 User-Project Relationships:")
        if projects_by_user:
            for user_id, user_projects in list(projects_by_user.items())[:5]:
                # Try to get user email
                user_email = "Unknown"
                for u in users:
                    if u['uuid'] == user_id:
                        user_email = u.get('email', 'Unknown')
                        break
                print(f"   - {user_email}: {len(user_projects)} project(s)")
            if len(projects_by_user) > 5:
                print(f"   ... and {len(projects_by_user) - 5} more users")
        else:
            print("   No user-project relationships found through tasks")

        # Summary Report
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)

        total_violations = len(tasks_without_project) + len(tasks_with_invalid_project) + len(orphaned_subtasks)

        if total_violations == 0:
            print("\n✅ SUCCESS: Data model is correctly implemented!")
            print("   - All tasks are linked to valid projects")
            print("   - All subtasks have valid parent tasks")
            print("   - Data hierarchy is maintained: User -> Projects -> Tasks -> Subtasks")
        else:
            print(f"\n❌ VIOLATIONS FOUND: {total_violations} issues detected")
            print("\nIssues to fix:")
            if tasks_without_project:
                print(f"   - {len(tasks_without_project)} tasks missing project_id")
            if tasks_with_invalid_project:
                print(f"   - {len(tasks_with_invalid_project)} tasks with invalid project_id")
            if orphaned_subtasks:
                print(f"   - {len(orphaned_subtasks)} subtasks with invalid parent_id")

            print("\n⚠️  Recommended Actions:")
            print("   1. Run fix_task_project_links.py to automatically fix these issues")
            print("   2. Add database constraint: ALTER TABLE tasks ADD CONSTRAINT fk_project")
            print("      FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;")

        print("\n" + "=" * 80)

        return {
            'total_tasks': len(tasks),
            'tasks_without_project': len(tasks_without_project),
            'tasks_with_invalid_project': len(tasks_with_invalid_project),
            'orphaned_subtasks': len(orphaned_subtasks),
            'violations': total_violations
        }

    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    verify_task_project_links()
