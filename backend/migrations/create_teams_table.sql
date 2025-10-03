-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    department_id VARCHAR(255),
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Create index on department_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_teams_department_id ON teams(department_id);

-- Add comments for documentation
COMMENT ON TABLE teams IS 'Stores team information within departments';
COMMENT ON COLUMN teams.id IS 'Unique team identifier (e.g., team1, team2)';
COMMENT ON COLUMN teams.name IS 'Team name';
COMMENT ON COLUMN teams.description IS 'Team description';
COMMENT ON COLUMN teams.department_id IS 'ID of the department this team belongs to';
COMMENT ON COLUMN teams.member_count IS 'Number of team members';
COMMENT ON COLUMN teams.created_at IS 'Timestamp when team was created';
COMMENT ON COLUMN teams.updated_at IS 'Timestamp when team was last updated';
