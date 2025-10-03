"""
Script to list all projects in the database
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

def list_projects():
    """List all projects in the database"""
    crud = SupabaseCRUD()
    client = crud.client

    try:
        result = client.table('projects').select('*').execute()

        if result.data:
            print("=" * 60)
            print(f"FOUND {len(result.data)} PROJECTS IN DATABASE")
            print("=" * 60)

            for project in result.data:
                print(f"\n📁 {project['name']}")
                print(f"   ID: {project['id']}")
                print(f"   Team ID: {project['team_id']}")
                print(f"   Description: {project.get('description', 'N/A')}")
                print(f"   Created: {project.get('created_at', 'N/A')}")
        else:
            print("No projects found in database")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    list_projects()
