"""
Script to assign managers and directors to multiple teams
"""
import os
import sys
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("ASSIGN MANAGERS/DIRECTORS TO MULTIPLE TEAMS")
print("=" * 80)

# Get all managers and directors
print("\n1. Finding managers and directors...")
managers_directors = supabase.table("users").select("uuid, email, role, departments").in_("role", ["manager", "director", "managing_director"]).execute()

print(f"   Found {len(managers_directors.data)} managers/directors:")
for user in managers_directors.data[:5]:
    print(f"   - {user['email']} ({user['role']}) - Dept: {user['departments']}")
if len(managers_directors.data) > 5:
    print(f"   ... and {len(managers_directors.data) - 5} more")

# Get all teams
print("\n2. Getting all teams...")
all_teams = supabase.table("teams").select("*").execute()
print(f"   Found {len(all_teams.data)} teams")

# Group teams by department
teams_by_dept = {}
for team in all_teams.data:
    dept = team.get('department', 'unknown')
    if dept not in teams_by_dept:
        teams_by_dept[dept] = []
    teams_by_dept[dept].append(team)

print(f"   Teams grouped by department:")
for dept, teams in teams_by_dept.items():
    print(f"   - {dept}: {len(teams)} teams")

# Process each manager/director
print("\n3. Assigning managers/directors to teams in their departments...")
updated_count = 0

for user in managers_directors.data:
    user_depts = user.get('departments', [])
    if not user_depts:
        continue

    # Get all teams in user's departments
    user_teams = []
    for dept in user_depts:
        if dept in teams_by_dept:
            user_teams.extend(teams_by_dept[dept])

    if not user_teams:
        continue

    print(f"\n   Processing {user['email']}:")
    print(f"   - Departments: {user_depts}")
    print(f"   - Should be in {len(user_teams)} teams")

    # Add user to each team's team_members if not already there
    teams_added = 0
    for team in user_teams:
        current_members = team.get('team_members', [])

        if user['uuid'] not in current_members:
            # Add user to team
            updated_members = current_members + [user['uuid']]
            result = supabase.table("teams").update({
                "team_members": updated_members
            }).eq("id", team['id']).execute()

            if result.data:
                teams_added += 1
                print(f"     + Added to team: {team['name']}")

    if teams_added > 0:
        print(f"   -> Added to {teams_added} new teams")
        updated_count += 1
    else:
        print(f"   -> Already in all relevant teams")

print("\n" + "=" * 80)
print(f"COMPLETE - Updated {updated_count} managers/directors")
print("=" * 80)
print("\nManagers and directors are now members of ALL teams in their departments.")
print("Regular staff remain in their specific teams only.")
