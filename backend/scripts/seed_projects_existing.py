"""
Script to seed sample projects based on existing teams
"""
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import datetime

def seed_projects_for_existing_teams():
    """Seed sample projects for existing teams"""
    crud = SupabaseCRUD()
    client = crud.client

    try:
        # Get existing teams from database
        teams_result = client.table('teams').select('id, name, department').execute()

        if not teams_result.data:
            print("[WARN]  No teams found in database. Please run seed_teams_existing.py first!")
            return None

        print(f"Found {len(teams_result.data)} teams in database")

        # Project templates by team type
        project_templates = {
            # Engineering teams
            "developers": [
                ("Web Application Development", "Build responsive web application with React and Node.js"),
                ("Mobile App Integration", "Develop mobile app integration with existing systems"),
                ("API Modernization", "Refactor legacy APIs to RESTful architecture"),
            ],
            "senior engineers": [
                ("System Architecture Review", "Review and optimize current system architecture"),
                ("Performance Optimization", "Improve application performance and scalability"),
                ("Code Quality Initiative", "Implement code review process and quality standards"),
            ],
            "junior engineers": [
                ("Bug Tracking System", "Set up and maintain bug tracking workflow"),
                ("Documentation Project", "Create comprehensive technical documentation"),
                ("Unit Testing Implementation", "Add unit tests to existing codebase"),
            ],
            "support team": [
                ("Customer Support Portal", "Build self-service customer support portal"),
                ("Ticket Management System", "Implement automated ticket routing and tracking"),
                ("Knowledge Base Development", "Create searchable knowledge base for common issues"),
            ],

            # IT teams
            "it team": [
                ("Network Infrastructure Upgrade", "Upgrade network infrastructure for better performance"),
                ("Security Audit", "Conduct comprehensive security audit and remediation"),
                ("Cloud Migration", "Migrate on-premise services to cloud infrastructure"),
            ],

            # Sales teams
            "account managers": [
                ("CRM System Implementation", "Deploy and customize CRM for account management"),
                ("Client Onboarding Process", "Streamline client onboarding workflow"),
                ("Sales Dashboard", "Create real-time sales metrics dashboard"),
            ],
            "sales manager": [
                ("Sales Strategy Planning", "Develop Q4 sales strategy and targets"),
                ("Territory Optimization", "Optimize sales territory assignments"),
                ("Sales Training Program", "Implement comprehensive sales training"),
            ],

            # Finance teams
            "finance executives": [
                ("Financial Reporting Automation", "Automate monthly financial report generation"),
                ("Expense Management System", "Implement digital expense tracking and approval"),
                ("Budget Tracking Tool", "Build budget vs actual tracking dashboard"),
            ],
            "finance managers": [
                ("Annual Budget Planning", "Plan and allocate annual departmental budgets"),
                ("Cost Optimization Initiative", "Identify and implement cost-saving measures"),
                ("Financial Compliance Review", "Ensure compliance with financial regulations"),
            ],

            # HR & Admin teams
            "hr team": [
                ("Employee Onboarding Portal", "Create digital employee onboarding system"),
                ("Performance Review System", "Implement 360-degree performance review process"),
                ("Benefits Administration", "Modernize employee benefits management"),
            ],
            "admin team": [
                ("Office Management System", "Digitize office management and booking systems"),
                ("Document Management", "Implement document management and archival system"),
                ("Facility Maintenance Tracking", "Create facility maintenance request system"),
            ],
            "l&d team": [
                ("Learning Management System", "Deploy LMS for employee training"),
                ("Skills Development Program", "Create skills assessment and development program"),
                ("Leadership Training", "Develop leadership training curriculum"),
            ],

            # Engineering Operations
            "operation planning team": [
                ("Resource Planning Tool", "Build resource allocation and planning dashboard"),
                ("Project Timeline Optimization", "Optimize project scheduling and dependencies"),
                ("Capacity Planning", "Implement capacity planning and forecasting"),
            ],
            "call centre": [
                ("Call Center Software Upgrade", "Upgrade call center management software"),
                ("Customer Satisfaction Tracking", "Implement NPS and CSAT tracking system"),
                ("Call Quality Monitoring", "Set up automated call quality monitoring"),
            ],

            # Consultancy
            "consultant": [
                ("Client Assessment Framework", "Develop standardized client assessment process"),
                ("Consulting Methodology", "Create consulting engagement methodology"),
                ("Best Practices Database", "Build searchable best practices repository"),
            ],
        }

        # Default projects for teams without specific templates
        default_projects = [
            ("Team Collaboration Enhancement", "Improve team collaboration and communication tools"),
            ("Process Improvement Initiative", "Streamline and optimize team workflows"),
            ("Quality Assurance Program", "Implement quality assurance best practices"),
        ]

        sample_projects = []

        # Create projects for each team
        for team in teams_result.data:
            team_id = team['id']
            team_name = team['name']

            # Get project templates for this team (or use defaults)
            templates = project_templates.get(team_name, default_projects)

            # Take first 2-3 projects per team to keep it manageable
            for name, description in templates[:3]:
                project = {
                    "name": f"{team_name.replace('_', ' ').title()}: {name}",
                    "description": description,
                    "team_id": team_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                sample_projects.append(project)

        if not sample_projects:
            print("[WARN]  No projects to create")
            return None

        print(f"\n[NOTE] Creating {len(sample_projects)} projects...")

        # Insert projects
        result = client.table('projects').insert(sample_projects).execute()

        if result.data:
            print(f"[OK] Successfully created {len(result.data)} sample projects!")

            # Group by team for display
            team_map = {t['id']: t['name'] for t in teams_result.data}
            projects_by_team = {}

            for project in result.data:
                team_name = team_map.get(project['team_id'], 'Unknown')
                if team_name not in projects_by_team:
                    projects_by_team[team_name] = []
                projects_by_team[team_name].append(project)

            print("\nCreated projects by team:")
            for team_name, projects in sorted(projects_by_team.items()):
                print(f"\n  {team_name} ({len(projects)} projects):")
                for project in projects:
                    print(f"    - {project['name']}")

            # Return project IDs for use in tasks seed script
            return {p['name']: p['id'] for p in result.data}
        else:
            print("[WARN]  No projects were created.")
            return None

    except Exception as e:
        print(f"[ERROR] Error creating projects: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. The projects table exists in your database")
        print("2. The teams have been seeded (run seed_teams_existing.py first)")
        return None

if __name__ == "__main__":
    print("Seeding sample projects for existing teams...")
    print("-" * 60)
    project_ids = seed_projects_for_existing_teams()
    print("-" * 60)
    if project_ids:
        print(f"\n[INFO] Created {len(project_ids)} projects")
