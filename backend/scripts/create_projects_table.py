"""
Script to create the projects table in Supabase
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

def create_projects_table():
    """Create the projects table in Supabase"""
    crud = SupabaseCRUD()
    client = crud.client

    # SQL to create projects table
    sql = """
    -- Create projects table if it doesn't exist
    CREATE TABLE IF NOT EXISTS projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(200) NOT NULL,
        description TEXT,
        team_id VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ
    );

    -- Create index on team_id for faster lookups
    CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);
    """

    try:
        # Execute the SQL using Supabase RPC or direct query
        # Note: Supabase client doesn't support direct SQL execution
        # You'll need to run this in Supabase SQL Editor
        print("=" * 60)
        print("PROJECTS TABLE CREATION SQL")
        print("=" * 60)
        print("\nPlease run the following SQL in your Supabase SQL Editor:")
        print("\n" + sql)
        print("\n" + "=" * 60)
        print("\nOR copy the SQL from: backend/migrations/create_projects_table.sql")
        print("=" * 60)

        # Alternative: Check if table exists
        try:
            result = client.table('projects').select('id').limit(1).execute()
            print("\n✅ Projects table already exists!")
            return True
        except Exception as e:
            print(f"\n⚠️  Projects table doesn't exist yet. Error: {str(e)}")
            print("\nPlease create it using the SQL above in Supabase Dashboard.")
            return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    create_projects_table()
