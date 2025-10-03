"""
Script to fix task-project relationships
Ensures all tasks are linked to valid projects
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
import uuid

def fix_task_project_links():
    """Fix tasks that are missing project_id or have invalid references"""
    crud = SupabaseCRUD()
    client = crud.client

    print("=" * 80)
    print("FIXING TASK-PROJECT RELATIONSHIPS")
    print("=" * 80)

    try:
        # Fetch all data
        tasks = client.table('tasks').select('*').execute().data or []
        projects = client.table('projects').select('*').execute().data or []
        users = client.table('users').select('*').execute().data or []

        print(f"\nCurrent State:")
        print(f"   Users: {len(users)}")
        print(f"   Projects: {len(projects)}")
        print(f"   Tasks: {len(tasks)}")

        # Get valid project IDs
        project_ids = {p['id'] for p in projects}
        project_by_team = {p['id']: p['team_id'] for p in projects}

        # Create default project if none exist
        if not projects:
            print("\n[WARNING] No projects found. Creating default project...")
            default_project = {
                "name": "Default Project",
                "description": "Default project for uncategorized tasks",
                "team_id": "team1"
            }
            result = client.table('projects').insert(default_project).execute()
            if result.data:
                default_project_id = result.data[0]['id']
                projects.append(result.data[0])
                project_ids.add(default_project_id)
                print(f"[SUCCESS] Created default project: {default_project_id}")
            else:
                print("[ERROR] Failed to create default project")
                return
        else:
            default_project_id = projects[0]['id']

        # Track fixes
        fixes = {
            'tasks_without_project': 0,
            'tasks_with_invalid_project': 0,
            'orphaned_subtasks': 0,
            'errors': []
        }

        # Fix 1: Tasks without project_id
        print("\n" + "=" * 80)
        print("FIX 1: Assigning Projects to Tasks Without project_id")
        print("=" * 80)

        tasks_without_project = [t for t in tasks if not t.get('project_id')]

        if tasks_without_project:
            print(f"\nFound {len(tasks_without_project)} tasks without project_id")
            print("Strategy: Assign to default project")

            for task in tasks_without_project:
                try:
                    # Assign to default project
                    update_data = {"project_id": default_project_id}

                    result = client.table('tasks').update(update_data).eq('id', task['id']).execute()

                    if result.data:
                        fixes['tasks_without_project'] += 1
                        print(f"   [SUCCESS] Updated: {task['title']}")
                    else:
                        print(f"   [WARNING] Failed to update: {task['title']}")

                except Exception as e:
                    error_msg = f"Error updating task {task['id']}: {str(e)}"
                    fixes['errors'].append(error_msg)
                    print(f"   [ERROR] {error_msg}")

            print(f"\n[DONE] Fixed {fixes['tasks_without_project']} tasks without project_id")
        else:
            print("\n[OK] No tasks without project_id found")

        # Fix 2: Tasks with invalid project_id
        print("\n" + "=" * 80)
        print("FIX 2: Fixing Tasks With Invalid Project References")
        print("=" * 80)

        tasks_with_invalid_project = []
        for task in tasks:
            if task.get('project_id') and task['project_id'] not in project_ids:
                tasks_with_invalid_project.append(task)

        if tasks_with_invalid_project:
            print(f"\nFound {len(tasks_with_invalid_project)} tasks with invalid project_id")
            print("Strategy: Reassign to default project")

            for task in tasks_with_invalid_project:
                try:
                    update_data = {"project_id": default_project_id}

                    result = client.table('tasks').update(update_data).eq('id', task['id']).execute()

                    if result.data:
                        fixes['tasks_with_invalid_project'] += 1
                        print(f"   [SUCCESS] Fixed: {task['title']} (was: {task['project_id']})")
                    else:
                        print(f"   [WARNING] Failed to fix: {task['title']}")

                except Exception as e:
                    error_msg = f"Error fixing task {task['id']}: {str(e)}"
                    fixes['errors'].append(error_msg)
                    print(f"   [ERROR] {error_msg}")

            print(f"\n[DONE] Fixed {fixes['tasks_with_invalid_project']} tasks with invalid project_id")
        else:
            print("\n[OK] No tasks with invalid project_id found")

        # Fix 3: Orphaned subtasks
        print("\n" + "=" * 80)
        print("FIX 3: Fixing Orphaned Subtasks")
        print("=" * 80)

        # Refresh tasks data
        tasks = client.table('tasks').select('*').execute().data or []
        task_ids = {t['id'] for t in tasks}
        subtasks = [t for t in tasks if t.get('parent_id')]

        orphaned_subtasks = []
        for subtask in subtasks:
            if subtask.get('parent_id') not in task_ids:
                orphaned_subtasks.append(subtask)

        if orphaned_subtasks:
            print(f"\nFound {len(orphaned_subtasks)} orphaned subtasks")
            print("Strategy: Convert to main tasks (remove parent_id)")

            for subtask in orphaned_subtasks:
                try:
                    update_data = {"parent_id": None}

                    result = client.table('tasks').update(update_data).eq('id', subtask['id']).execute()

                    if result.data:
                        fixes['orphaned_subtasks'] += 1
                        print(f"   [SUCCESS] Converted to main task: {subtask['title']}")
                    else:
                        print(f"   [WARNING] Failed to convert: {subtask['title']}")

                except Exception as e:
                    error_msg = f"Error fixing subtask {subtask['id']}: {str(e)}"
                    fixes['errors'].append(error_msg)
                    print(f"   [ERROR] {error_msg}")

            print(f"\n[DONE] Fixed {fixes['orphaned_subtasks']} orphaned subtasks")
        else:
            print("\n[OK] No orphaned subtasks found")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        total_fixes = (fixes['tasks_without_project'] +
                      fixes['tasks_with_invalid_project'] +
                      fixes['orphaned_subtasks'])

        print(f"\nFixes Applied:")
        print(f"   - Tasks assigned project: {fixes['tasks_without_project']}")
        print(f"   - Tasks with corrected project: {fixes['tasks_with_invalid_project']}")
        print(f"   - Orphaned subtasks converted: {fixes['orphaned_subtasks']}")
        print(f"   Total fixes: {total_fixes}")

        if fixes['errors']:
            print(f"\n[WARNING] Errors encountered: {len(fixes['errors'])}")
            for error in fixes['errors'][:5]:
                print(f"   - {error}")
            if len(fixes['errors']) > 5:
                print(f"   ... and {len(fixes['errors']) - 5} more errors")

        print("\n[SUCCESS] Task-project relationship fixes complete!")
        print("\nNext step: Run verify_task_project_links_simple.py to confirm all issues are resolved")

        print("\n" + "=" * 80)

        return fixes

    except Exception as e:
        print(f"\n[ERROR] Error during fix process: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    fix_task_project_links()
