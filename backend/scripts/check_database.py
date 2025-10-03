"""
Script to check database tables and synchronization
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

def check_database():
    """Check what tables exist in the database"""
    crud = SupabaseCRUD()
    client = crud.client

    print("=" * 60)
    print("DATABASE TABLE CHECK")
    print("=" * 60)

    tables_to_check = ['users', 'tasks', 'projects', 'teams']

    for table in tables_to_check:
        try:
            result = client.table(table).select('*').limit(1).execute()
            count_result = client.table(table).select('*', count='exact').execute()
            count = count_result.count if hasattr(count_result, 'count') else 'unknown'
            print(f"\n✅ Table '{table}' EXISTS")
            print(f"   Total records: {count}")
            if result.data:
                print(f"   Sample columns: {list(result.data[0].keys())}")
        except Exception as e:
            print(f"\n❌ Table '{table}' DOES NOT EXIST or ERROR")
            print(f"   Error: {str(e)}")

    print("\n" + "=" * 60)
    print("\nRECOMMENDATIONS:")
    print("=" * 60)

    # Check if projects table exists
    try:
        client.table('projects').select('id').limit(1).execute()
        print("\n✅ Projects table exists - you can run seed_projects.py")
    except:
        print("\n❌ Projects table MISSING - please create it:")
        print("\n1. Go to Supabase Dashboard → SQL Editor")
        print("2. Run this SQL:")
        print("""
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    team_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);
        """)

    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_database()
