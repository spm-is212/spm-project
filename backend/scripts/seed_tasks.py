"""
Script to seed sample tasks into the database
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import datetime, timedelta
import random

def seed_tasks():
    """Seed sample tasks for projects"""
    crud = SupabaseCRUD()
    client = crud.client

    try:
        # Get existing users
        users_result = client.table('users').select('uuid, email').execute()
        if not users_result.data:
            print("[WARN]  No users found. Please run seed_users.py first!")
            return None

        # Get existing projects
        projects_result = client.table('projects').select('id, name, team_id').execute()
        if not projects_result.data:
            print("[WARN]  No projects found. Please run seed_projects_new.py first!")
            return None

        print(f"Found {len(users_result.data)} users and {len(projects_result.data)} projects")

        # Helper data
        statuses = ['TO_DO', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED']
        priorities = [1, 2, 3]  # 1=LOW, 2=MEDIUM, 3=HIGH
        user_uuids = [user['uuid'] for user in users_result.data]

        # Generate tasks for each project
        all_tasks = []
        task_templates = {
            "Payment Gateway Integration": [
                {
                    "title": "Research payment gateway options",
                    "description": "Compare Stripe, PayPal, and Square APIs for features, pricing, and integration complexity",
                    "priority": 3
                },
                {
                    "title": "Setup Stripe test account",
                    "description": "Create Stripe test account and obtain API keys for development environment",
                    "priority": 3
                },
                {
                    "title": "Implement payment processing endpoint",
                    "description": "Create REST API endpoint to handle payment transactions securely",
                    "priority": 3
                },
                {
                    "title": "Add webhook handlers",
                    "description": "Implement webhook endpoints for payment confirmations and failures",
                    "priority": 2
                }
            ],
            "User Authentication System": [
                {
                    "title": "Design authentication flow",
                    "description": "Design JWT-based authentication flow with refresh tokens",
                    "priority": 3
                },
                {
                    "title": "Implement login endpoint",
                    "description": "Create secure login endpoint with password hashing and JWT generation",
                    "priority": 3
                },
                {
                    "title": "Add OAuth integration",
                    "description": "Integrate Google and GitHub OAuth providers",
                    "priority": 2
                },
                {
                    "title": "Setup password reset flow",
                    "description": "Implement email-based password reset with secure tokens",
                    "priority": 2
                }
            ],
            "Dashboard UI Redesign": [
                {
                    "title": "Create design mockups",
                    "description": "Design new dashboard layout in Figma with modern UI patterns",
                    "priority": 3
                },
                {
                    "title": "Implement responsive grid layout",
                    "description": "Build responsive grid system using CSS Grid and Flexbox",
                    "priority": 3
                },
                {
                    "title": "Add data visualization charts",
                    "description": "Integrate Chart.js for analytics dashboards",
                    "priority": 2
                },
                {
                    "title": "Implement dark mode toggle",
                    "description": "Add dark/light theme switching with user preference persistence",
                    "priority": 1
                }
            ],
            "CI/CD Pipeline Setup": [
                {
                    "title": "Configure GitHub Actions",
                    "description": "Setup GitHub Actions workflow for automated testing and deployment",
                    "priority": 3
                },
                {
                    "title": "Setup Docker containers",
                    "description": "Create Dockerfile and docker-compose for consistent environments",
                    "priority": 3
                },
                {
                    "title": "Configure deployment to staging",
                    "description": "Setup automated deployment to staging environment on merge to develop",
                    "priority": 2
                },
                {
                    "title": "Add automated testing",
                    "description": "Integrate unit and integration tests in CI pipeline",
                    "priority": 2
                }
            ]
        }

        # Create tasks for each project
        for project in projects_result.data:
            project_name = project['name']
            project_id = project['id']

            # Get templates for this project (or use generic tasks)
            templates = task_templates.get(project_name, [
                {
                    "title": f"Initial planning for {project_name}",
                    "description": f"Define scope and requirements for {project_name}",
                    "priority": 3
                },
                {
                    "title": f"Implementation phase",
                    "description": f"Develop core features for {project_name}",
                    "priority": 2
                },
                {
                    "title": f"Testing and QA",
                    "description": f"Test functionality and fix bugs for {project_name}",
                    "priority": 2
                }
            ])

            # Create main tasks
            for idx, template in enumerate(templates):
                # Vary due dates
                due_date = (datetime.utcnow() + timedelta(days=random.randint(1, 30))).date().isoformat()

                # Randomly assign status (with bias towards realistic workflow)
                if idx == 0:
                    status = random.choice(['COMPLETED', 'IN_PROGRESS'])
                elif idx == len(templates) - 1:
                    status = random.choice(['TO_DO', 'IN_PROGRESS'])
                else:
                    status = random.choice(statuses)

                # Assign 1-3 random users
                num_assignees = random.randint(1, min(3, len(user_uuids)))
                assignee_ids = random.sample(user_uuids, num_assignees)
                owner_id = random.choice(user_uuids)

                task = {
                    "title": template['title'],
                    "description": template['description'],
                    "project_id": project_id,
                    "due_date": due_date,
                    "status": status,
                    "priority": template['priority'],
                    "owner_user_id": owner_id,
                    "assignee_ids": assignee_ids,
                    "comments": [],
                    "attachments": [],
                    "is_archived": False,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                all_tasks.append(task)

        if not all_tasks:
            print("[WARN]  No tasks to create")
            return None

        # Insert tasks
        result = client.table('tasks').insert(all_tasks).execute()

        if result.data:
            print(f"[OK] Successfully created {len(result.data)} sample tasks!")

            # Group by project for display
            project_map = {p['id']: p['name'] for p in projects_result.data}
            tasks_by_project = {}

            for task in result.data:
                project_name = project_map.get(task['project_id'], 'Unknown')
                if project_name not in tasks_by_project:
                    tasks_by_project[project_name] = []
                tasks_by_project[project_name].append(task)

            print("\nCreated tasks by project:")
            for project_name, tasks in tasks_by_project.items():
                print(f"\n  {project_name} ({len(tasks)} tasks):")
                for task in tasks:
                    print(f"    - [{task['status']}] {task['title']} (Priority: {task['priority']})")

            # Now create some subtasks for certain main tasks
            print("\n[NOTE] Creating subtasks...")
            subtasks = []

            # Select some completed or in-progress tasks to add subtasks to
            main_tasks = [t for t in result.data if t['status'] in ['IN_PROGRESS', 'COMPLETED']]
            selected_tasks = random.sample(main_tasks, min(5, len(main_tasks)))

            for main_task in selected_tasks:
                # Create 2-3 subtasks for each selected task
                num_subtasks = random.randint(2, 3)

                for i in range(num_subtasks):
                    subtask = {
                        "parent_id": main_task['id'],
                        "title": f"Subtask {i+1}: {main_task['title'][:30]}...",
                        "description": f"Detailed work item for: {main_task['title']}",
                        "project_id": main_task['project_id'],
                        "due_date": main_task['due_date'],
                        "status": random.choice(['COMPLETED', 'IN_PROGRESS', 'TO_DO']),
                        "priority": main_task['priority'],
                        "owner_user_id": main_task['owner_user_id'],
                        "assignee_ids": random.sample(user_uuids, random.randint(1, 2)),
                        "comments": [],
                        "attachments": [],
                        "is_archived": False,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    subtasks.append(subtask)

            if subtasks:
                subtask_result = client.table('tasks').insert(subtasks).execute()
                if subtask_result.data:
                    print(f"[OK] Created {len(subtask_result.data)} subtasks!")

            return result.data
        else:
            print("[WARN]  No tasks were created.")
            return None

    except Exception as e:
        print(f"[ERROR] Error creating tasks: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. The tasks table exists in your database")
        print("2. Users and projects have been seeded")
        return None

if __name__ == "__main__":
    print("Seeding sample tasks...")
    print("-" * 60)
    tasks = seed_tasks()
    print("-" * 60)
    if tasks:
        print(f"\n[INFO] Successfully seeded {len(tasks)} tasks!")
