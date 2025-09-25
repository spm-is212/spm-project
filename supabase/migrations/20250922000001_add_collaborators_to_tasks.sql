-- Add collaborators column to tasks table
ALTER TABLE tasks
ADD COLUMN collaborators UUID[] DEFAULT '{}';

-- Create index for performance on collaborators column
CREATE INDEX IF NOT EXISTS idx_tasks_collaborators ON tasks USING GIN(collaborators);
