-- Add teams column to users table
ALTER TABLE users
ADD COLUMN teams TEXT[] DEFAULT '{}';

-- Add teams column to users_test table
ALTER TABLE users_test
ADD COLUMN teams TEXT[] DEFAULT '{}';

-- Create index for performance on teams column
CREATE INDEX IF NOT EXISTS idx_users_teams ON users USING GIN(teams);
CREATE INDEX IF NOT EXISTS idx_users_test_teams ON users_test USING GIN(teams);
