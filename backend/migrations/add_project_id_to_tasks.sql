-- Migration: Add project_id column to tasks table
-- This enforces the data model: User → Projects → Tasks → Subtasks
-- Run this migration BEFORE adding the NOT NULL constraint

-- Step 1: Add project_id column (nullable initially to allow data migration)
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS project_id UUID;

-- Step 2: Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);

-- Step 3: Add comment to document the relationship
COMMENT ON COLUMN tasks.project_id IS
'Foreign key to projects table. All tasks must belong to a project. Part of data model: User → Projects → Tasks → Subtasks';

-- Verification query - check which tasks don't have a project
-- SELECT id, title, project_id FROM tasks WHERE project_id IS NULL;
