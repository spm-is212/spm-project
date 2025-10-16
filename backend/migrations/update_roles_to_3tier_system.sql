-- Migration: Update roles from 4-tier to 3-tier system
-- Old roles: managing_director, director, manager, staff
-- New roles: admin, manager, staff

-- Step 1: Show current role distribution
SELECT
    role,
    COUNT(*) as user_count
FROM users
GROUP BY role
ORDER BY
    CASE role
        WHEN 'managing_director' THEN 1
        WHEN 'director' THEN 2
        WHEN 'manager' THEN 3
        WHEN 'staff' THEN 4
        ELSE 5
    END;

-- Step 2: Update roles to new 3-tier system
-- managing_director -> admin
UPDATE users
SET role = 'admin',
    updated_at = NOW()
WHERE role = 'managing_director';

-- director -> admin (directors become admins)
UPDATE users
SET role = 'admin',
    updated_at = NOW()
WHERE role = 'director';

-- manager stays manager
-- staff stays staff (no update needed)

-- Step 3: Verify role migration
SELECT
    role,
    COUNT(*) as user_count,
    CASE
        WHEN role IN ('admin', 'manager', 'staff') THEN 'Valid'
        ELSE 'INVALID - Needs attention!'
    END as validation_status
FROM users
GROUP BY role
ORDER BY
    CASE role
        WHEN 'admin' THEN 1
        WHEN 'manager' THEN 2
        WHEN 'staff' THEN 3
        ELSE 4
    END;

-- Step 4: Check for any remaining old roles
SELECT
    uuid,
    email,
    role,
    'OLD ROLE - UPDATE NEEDED' as issue
FROM users
WHERE role NOT IN ('admin', 'manager', 'staff');

-- Step 5: Add comment explaining new role system
COMMENT ON COLUMN users.role IS 'User role in 3-tier system: admin (full access), manager (can remove assignees, see assigned tasks), staff (see assigned tasks only)';
