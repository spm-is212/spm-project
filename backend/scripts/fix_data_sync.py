"""
Script to fix data synchronization issues
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import datetime

def fix_data_sync():
    """Fix all data synchronization issues"""
    crud = SupabaseCRUD()
    client = crud.client

    print("=" * 80)
    print("FIXING DATA SYNCHRONIZATION ISSUES")
    print("=" * 80)

    # Step 1: Create sample teams if teams table exists
    print("\n1️⃣ CREATING TEAMS...")
    try:
        # Check if teams table exists
        client.table('teams').select('id').limit(1).execute()

        # Create sample teams
        sample_teams = [
            {
                "id": "team1",
                "name": "Backend Development",
                "description": "Backend development team",
                "department_id": "Engineering",
                "member_count": 5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "team2",
                "name": "Frontend Development",
                "description": "Frontend development team",
                "department_id": "Engineering",
                "member_count": 4,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "team3",
                "name": "DevOps",
                "description": "DevOps and infrastructure team",
                "department_id": "Engineering",
                "member_count": 3,
                "created_at": datetime.utcnow().isoformat()
            }
        ]

        # Check if teams already exist
        existing_teams = client.table('teams').select('id').execute().data or []
        existing_ids = {t['id'] for t in existing_teams}

        teams_to_insert = [t for t in sample_teams if t['id'] not in existing_ids]

        if teams_to_insert:
            result = client.table('teams').insert(teams_to_insert).execute()
            print(f"   ✅ Created {len(teams_to_insert)} teams")
        else:
            print(f"   ℹ️  Teams already exist, skipping...")

    except Exception as e:
        print(f"   ⚠️  Teams table doesn't exist. Please create it first using:")
        print(f"      Run SQL: backend/migrations/create_teams_table.sql")
        print(f"   Error: {str(e)}")

    # Step 2: Ensure all users have departments and teams
    print("\n2️⃣ UPDATING USER DEPARTMENTS & TEAMS...")
    try:
        users = client.table('users').select('*').execute().data or []
        updated_count = 0

        for user in users:
            updates = {}

            # Ensure departments
            if not user.get('departments') or user.get('departments') == []:
                updates['departments'] = ['Engineering']  # Default department

            # Ensure teams (assign based on role or randomly)
            if not user.get('teams') or user.get('teams') == []:
                # Assign team based on role
                if user.get('role') == 'director' or user.get('role') == 'managing_director':
                    updates['teams'] = ['team1', 'team2', 'team3']  # Access all teams
                else:
                    # Assign to team1 by default
                    updates['teams'] = ['team1']

            if updates:
                client.table('users').update(updates).eq('uuid', user['uuid']).execute()
                updated_count += 1

        print(f"   ✅ Updated {updated_count} users with departments/teams")

    except Exception as e:
        print(f"   ❌ Error updating users: {str(e)}")

    # Step 3: Link tasks to projects
    print("\n3️⃣ LINKING TASKS TO PROJECTS...")
    try:
        tasks = client.table('tasks').select('*').execute().data or []
        projects = client.table('projects').select('*').execute().data or []

        if not projects:
            print("   ⚠️  No projects available. Create projects first!")
        else:
            # Get tasks without projects
            tasks_without_projects = [t for t in tasks if not t.get('project_id')]

            if tasks_without_projects:
                # Assign to first available project (you can customize this logic)
                default_project = projects[0]

                for task in tasks_without_projects:
                    client.table('tasks').update({
                        'project_id': default_project['id']
                    }).eq('id', task['id']).execute()

                print(f"   ✅ Linked {len(tasks_without_projects)} tasks to project '{default_project['name']}'")
            else:
                print(f"   ℹ️  All tasks already have projects")

    except Exception as e:
        print(f"   ❌ Error linking tasks: {str(e)}")

    # Step 4: Fix orphaned references
    print("\n4️⃣ FIXING ORPHANED REFERENCES...")
    try:
        tasks = client.table('tasks').select('*').execute().data or []
        users = client.table('users').select('uuid').execute().data or []
        projects = client.table('projects').select('id').execute().data or []

        user_ids = {u['uuid'] for u in users}
        project_ids = {p['id'] for p in projects}
        task_ids = {t['id'] for t in tasks}

        fixed_count = 0

        for task in tasks:
            updates = {}

            # Fix invalid owner_user_id
            if task.get('owner_user_id') and task['owner_user_id'] not in user_ids:
                # Assign to first available user
                if users:
                    updates['owner_user_id'] = users[0]['uuid']

            # Fix invalid assignee_ids
            if task.get('assignee_ids'):
                valid_assignees = [a for a in task['assignee_ids'] if a in user_ids]
                if valid_assignees != task['assignee_ids']:
                    updates['assignee_ids'] = valid_assignees if valid_assignees else [users[0]['uuid']]

            # Fix invalid project_id
            if task.get('project_id') and task['project_id'] not in project_ids:
                if projects:
                    updates['project_id'] = projects[0]['id']

            # Fix invalid parent_id
            if task.get('parent_id') and task['parent_id'] not in task_ids:
                updates['parent_id'] = None

            if updates:
                client.table('tasks').update(updates).eq('id', task['id']).execute()
                fixed_count += 1

        print(f"   ✅ Fixed {fixed_count} orphaned references")

    except Exception as e:
        print(f"   ❌ Error fixing orphaned references: {str(e)}")

    # Step 5: Update team member counts
    print("\n5️⃣ UPDATING TEAM MEMBER COUNTS...")
    try:
        users = client.table('users').select('teams').execute().data or []
        teams = client.table('teams').select('id').execute().data or []

        if teams:
            for team in teams:
                # Count users in this team
                member_count = sum(1 for u in users if u.get('teams') and team['id'] in u['teams'])

                client.table('teams').update({
                    'member_count': member_count
                }).eq('id', team['id']).execute()

            print(f"   ✅ Updated member counts for {len(teams)} teams")
        else:
            print(f"   ⚠️  Teams table not available")

    except Exception as e:
        print(f"   ⚠️  Could not update team member counts: {str(e)}")

    print("\n" + "=" * 80)
    print("✅ DATA SYNCHRONIZATION FIX COMPLETE!")
    print("=" * 80)
    print("\nRun 'py -m backend.scripts.verify_data_sync' to verify the fixes")
    print("=" * 80)

if __name__ == "__main__":
    fix_data_sync()
