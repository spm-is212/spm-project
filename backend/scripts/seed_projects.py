"""
Script to seed sample projects into the database
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import datetime

def seed_projects():
    """Seed sample projects with collaborators (no teams)"""
    crud = SupabaseCRUD()
    client = crud.client

    # Note: Get user UUIDs from your database and update these
    # For now using placeholder UUIDs - update with real user IDs
    sample_projects = [
        {
            "name": "Payment Gateway Integration",
            "description": "Integrate Stripe and PayPal payment systems",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "name": "User Authentication System",
            "description": "JWT-based authentication with OAuth integration",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "name": "Dashboard UI Redesign",
            "description": "Modern React dashboard with improved UX",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "name": "Mobile App MVP",
            "description": "React Native mobile application",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "name": "CI/CD Pipeline Setup",
            "description": "Automated deployment pipeline with GitHub Actions",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "name": "Infrastructure Monitoring",
            "description": "Setup monitoring and alerting with Prometheus & Grafana",
            "collaborator_ids": [],  # Add actual user UUIDs here
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    try:
        # Insert projects
        result = client.table('projects').insert(sample_projects).execute()

        if result.data:
            print(f"✅ Successfully created {len(result.data)} sample projects!")
            print("\nCreated projects:")
            for project in result.data:
                collab_count = len(project.get('collaborator_ids', []))
                print(f"  - {project['name']} ({collab_count} collaborators)")
        else:
            print("⚠️  No projects were created.")

    except Exception as e:
        print(f"❌ Error creating projects: {str(e)}")
        print("\nMake sure:")
        print("1. The projects table exists in your database")
        print("2. Update collaborator_ids with actual user UUIDs from your database")

if __name__ == "__main__":
    print("Seeding sample projects...")
    print("-" * 60)
    seed_projects()
    print("-" * 60)
