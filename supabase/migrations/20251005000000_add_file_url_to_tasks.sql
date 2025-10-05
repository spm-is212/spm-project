-- Add file_url column to tasks tables
ALTER TABLE IF EXISTS tasks
    ADD COLUMN IF NOT EXISTS file_url TEXT;

ALTER TABLE IF EXISTS tasks_test
    ADD COLUMN IF NOT EXISTS file_url TEXT;
