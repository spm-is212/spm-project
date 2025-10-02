-- Add recurrence_rule column (DAILY / WEEKLY / MONTHLY, stored as text)
ALTER TABLE tasks_test 
ADD COLUMN IF NOT EXISTS recurrence_rule TEXT;

-- Add recurrence_interval column (must be >=1)
ALTER TABLE tasks_test 
ADD COLUMN IF NOT EXISTS recurrence_interval INT DEFAULT 1 CHECK (recurrence_interval >= 1);

-- Add recurrence_end_date column
ALTER TABLE tasks_test 
ADD COLUMN IF NOT EXISTS recurrence_end_date DATE;
