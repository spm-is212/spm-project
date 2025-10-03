-- Migration: Add foreign key constraint to enforce task-project relationship
-- This ensures all tasks must be linked to a valid project
-- Run this AFTER fixing existing data with fix_task_project_links.py

-- Step 1: First ensure project_id column exists and is not null for existing tasks
-- (This should already be done by fix_task_project_links.py)

-- Step 2: Make project_id NOT NULL (all tasks must have a project)
ALTER TABLE tasks
ALTER COLUMN project_id SET NOT NULL;

-- Step 3: Add foreign key constraint
-- This ensures project_id always references a valid project
ALTER TABLE tasks
ADD CONSTRAINT fk_tasks_project
FOREIGN KEY (project_id)
REFERENCES projects(id)
ON DELETE CASCADE;  -- If project is deleted, also delete its tasks

-- Step 4: Create index on project_id for better query performance
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);

-- Step 5: Add comment to document the constraint
COMMENT ON CONSTRAINT fk_tasks_project ON tasks IS
'Enforces that all tasks must belong to a valid project. Data model: User → Projects → Tasks → Subtasks';

-- Verification query - should return 0 rows
-- SELECT id, title FROM tasks WHERE project_id IS NULL;
-- SELECT id, title FROM tasks WHERE project_id NOT IN (SELECT id FROM projects);
