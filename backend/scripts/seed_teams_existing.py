"""
Script to create teams table entries based on existing user data
This script reads the teams from existing users and creates proper team records
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import datetime
import uuid

def seed_teams_from_users():
    """Create team records based on existing user team assignments"""
    crud = SupabaseCRUD()
    client = crud.client

    try:
        # Get all existing users
        users_result = client.table('users').select('uuid, email, departments, teams').execute()

        if not users_result.data:
            print("[WARN]  No users found in database!")
            return None

        print(f"Found {len(users_result.data)} existing users")

        # Collect all unique team names from users
        team_names = set()
        team_to_users = {}  # Map team name to list of user UUIDs
        team_to_dept = {}   # Map team name to department

        for user in users_result.data:
            user_teams = user.get('teams', [])
            user_uuid = user['uuid']
            user_depts = user.get('departments', [])
            primary_dept = user_depts[0] if user_depts else 'General'

            for team_name in user_teams:
                team_names.add(team_name)

                # Track which users belong to this team
                if team_name not in team_to_users:
                    team_to_users[team_name] = []
                    team_to_dept[team_name] = primary_dept
                team_to_users[team_name].append(user_uuid)

        print(f"\nFound {len(team_names)} unique teams in user data:")
        for team in sorted(team_names):
            print(f"  - {team} ({len(team_to_users[team])} members, {team_to_dept[team]} dept)")

        # Create team records with proper UUIDs
        teams_to_create = []

        for team_name in sorted(team_names):
            # Generate a consistent UUID based on team name (for idempotency)
            team_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"allinone.com.{team_name}"))

            team_record = {
                "id": team_id,
                "name": team_name,
                "description": f"{team_name.replace('_', ' ').title()} - Auto-generated from user data",
                "department": team_to_dept[team_name],
                "team_members": team_to_users[team_name],
                "created_at": datetime.utcnow().isoformat()
            }
            teams_to_create.append(team_record)

        # Check if teams already exist
        existing_teams = client.table('teams').select('id, name').execute()
        existing_team_names = set(t['name'] for t in (existing_teams.data or []))

        # Filter out existing teams
        new_teams = [t for t in teams_to_create if t['name'] not in existing_team_names]

        if not new_teams:
            print("\n[WARN]  All teams already exist in database. Skipping insert.")
            print("\n[TIP] Tip: Delete existing teams if you want to recreate them:")
            print("   DELETE FROM teams;")
            return None

        print(f"\n[NOTE] Creating {len(new_teams)} new teams...")

        # Insert teams
        result = client.table('teams').insert(new_teams).execute()

        if result.data:
            print(f"[OK] Successfully created {len(result.data)} teams!")
            print("\nCreated teams:")
            for team in result.data:
                print(f"  - {team['name']}")
                print(f"    ID: {team['id']}")
                print(f"    Members: {len(team.get('team_members', []))}")
                print(f"    Department: {team['department']}")

            # Now update users to have team UUID instead of team name
            print("\n[NOTE] Updating user records with team UUIDs...")
            team_name_to_id = {t['name']: t['id'] for t in result.data}

            for user in users_result.data:
                user_uuid = user['uuid']
                user_team_names = user.get('teams', [])

                # Convert team names to team UUIDs
                team_uuids = []
                for team_name in user_team_names:
                    if team_name in team_name_to_id:
                        team_uuids.append(team_name_to_id[team_name])
                    elif team_name in {t['id'] for t in (existing_teams.data or [])}:
                        # Already a UUID
                        team_uuids.append(team_name)

                if team_uuids and team_uuids != user_team_names:
                    # Update user with team UUIDs
                    client.table('users').update({'teams': team_uuids}).eq('uuid', user_uuid).execute()

            print("[OK] Users updated with team UUIDs!")

            # Return team mapping for use in other scripts
            return team_name_to_id
        else:
            print("[WARN]  No teams were created.")
            return None

    except Exception as e:
        print(f"[ERROR] Error creating teams: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. The teams table exists in your database")
        print("2. The users table is populated with team data")
        return None

if __name__ == "__main__":
    print("Seeding teams from existing user data...")
    print("-" * 60)
    team_mapping = seed_teams_from_users()
    print("-" * 60)
    if team_mapping:
        print(f"\n[INFO] Created teams mapping:")
        for name, tid in sorted(team_mapping.items()):
            print(f"  {name}: {tid}")
