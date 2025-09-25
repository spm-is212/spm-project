-- Create test tables with _test suffix to avoid conflicts with production tables

-- Test users table
CREATE TABLE IF NOT EXISTS users_test (
  uuid TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  departments TEXT[] NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test tasks table
CREATE TABLE IF NOT EXISTS tasks_test (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES tasks_test(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  due_date DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('TO_DO', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED')),
  priority TEXT NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
  owner_user_id TEXT NOT NULL,
  assignee_ids UUID[] NOT NULL,
  comments JSONB DEFAULT '[]'::jsonb,
  attachments JSONB DEFAULT '[]'::jsonb,
  is_archived BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for test tables
CREATE INDEX IF NOT EXISTS idx_users_test_email ON users_test(email);
CREATE INDEX IF NOT EXISTS idx_users_test_role ON users_test(role);
CREATE INDEX IF NOT EXISTS idx_users_test_departments ON users_test USING GIN(departments);

CREATE INDEX IF NOT EXISTS idx_tasks_test_owner ON tasks_test(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_test_assignees ON tasks_test USING GIN(assignee_ids);
CREATE INDEX IF NOT EXISTS idx_tasks_test_status ON tasks_test(status);
CREATE INDEX IF NOT EXISTS idx_tasks_test_priority ON tasks_test(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_test_due_date ON tasks_test(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_test_parent ON tasks_test(parent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_test_archived ON tasks_test(is_archived);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_tasks_test_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_tasks_test_updated_at ON tasks_test;
CREATE TRIGGER update_tasks_test_updated_at
    BEFORE UPDATE ON tasks_test
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_test_updated_at();
