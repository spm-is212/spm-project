-- Remove collaborators column from both tasks and tasks_test tables
-- This reverts the collaborators column addition

-- Drop the index first
DROP INDEX IF EXISTS idx_tasks_collaborators;
DROP INDEX IF EXISTS idx_tasks_test_collaborators;

-- Remove the collaborators column from production table
ALTER TABLE tasks DROP COLUMN IF EXISTS collaborators;

-- Remove the collaborators column from test table
ALTER TABLE tasks_test DROP COLUMN IF EXISTS collaborators;
