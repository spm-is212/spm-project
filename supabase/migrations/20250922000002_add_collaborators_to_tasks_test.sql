-- Add collaborators column to tasks_test table
-- This mirrors the same change made to the production tasks table

ALTER TABLE tasks_test
ADD COLUMN collaborators UUID[] DEFAULT '{}';

-- Create index for performance (same as production table)
CREATE INDEX IF NOT EXISTS idx_tasks_test_collaborators ON tasks_test USING GIN(collaborators);
