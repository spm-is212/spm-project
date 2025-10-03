"""
Check the database schema for teams, projects, and tasks
"""
import os
import sys
from supabase import create_client

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("DATABASE SCHEMA CHECK")
print("=" * 80)

# Check users table
print("\n1. USERS TABLE (sample)")
users = supabase.table("users").select("uuid, email, role, departments").limit(1).execute()
if users.data:
    print(f"   Columns: {list(users.data[0].keys())}")
    print(f"   Sample: {users.data[0]}")

# Check teams table
print("\n2. TEAMS TABLE (sample)")
teams = supabase.table("teams").select("*").limit(1).execute()
if teams.data:
    print(f"   Columns: {list(teams.data[0].keys())}")
    print(f"   Sample: {teams.data[0]}")

# Check projects table
print("\n3. PROJECTS TABLE (sample)")
projects = supabase.table("projects").select("*").limit(1).execute()
if projects.data:
    print(f"   Columns: {list(projects.data[0].keys())}")
    print(f"   Sample: {projects.data[0]}")

# Check tasks table
print("\n4. TASKS TABLE (sample)")
tasks = supabase.table("tasks").select("*").limit(1).execute()
if tasks.data:
    print(f"   Columns: {list(tasks.data[0].keys())}")
    print(f"   Sample: {tasks.data[0]}")

print("\n" + "=" * 80)
print("KEY RELATIONSHIPS:")
print("=" * 80)
print("- Users have: departments[] (array of department IDs)")
print("- Teams have: department_id (belongs to a department)")
print("- Projects have: team_id (belongs to a team)")
print("- Tasks have: project_id (belongs to a project)")
print("- Tasks have: assignee_ids[] (array of user UUIDs)")
print("\nSo the chain is: User -> Department -> Teams -> Projects -> Tasks")
print("Users are assigned to tasks via assignee_ids[]")
