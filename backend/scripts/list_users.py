"""
Script to list all users in the database
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

def list_users():
    """List all users in the database"""
    crud = SupabaseCRUD()
    client = crud.client

    try:
        result = client.table('users').select('uuid, email, role, departments, teams').execute()

        if result.data:
            print("=" * 60)
            print(f"FOUND {len(result.data)} USERS IN DATABASE")
            print("=" * 60)

            for user in result.data:
                print(f"\n👤 {user['email']}")
                print(f"   UUID: {user['uuid']}")
                print(f"   Role: {user.get('role', 'N/A')}")
                print(f"   Departments: {user.get('departments', [])}")
                print(f"   Teams: {user.get('teams', [])}")
                print("   ---")

            print("\n" + "=" * 60)
            print("NOTE: Passwords are hashed and not shown here")
            print("Try logging in with one of these emails")
            print("=" * 60)
        else:
            print("No users found in database")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    list_users()
