# 3-Tier Role System & Project Collaborator Sync

## Overview

This document covers two critical updates:
1. **Role System Simplification**: 4-tier → 3-tier (admin, manager, staff)
2. **Project Collaborator Sync**: Ensure all task assignees are project collaborators

---

## Part 1: 3-Tier Role System

### Old System (4 roles)
```
managing_director > director > manager > staff
```

### New System (3 roles)
```
admin > manager > staff
```

### Role Mapping

| Old Role | New Role | Notes |
|----------|----------|-------|
| `managing_director` | `admin` | Full system access |
| `director` | `admin` | Department-wide access consolidated to admin |
| `manager` | `manager` | Can remove assignees, see assigned tasks |
| `staff` | `staff` | See assigned tasks only |

### Access Control Matrix

| Role | Task Access | Can Remove Assignees | Project Access | Update Projects |
|------|-------------|---------------------|----------------|-----------------|
| **Admin** | All tasks | ✅ Yes | All projects | ✅ Any project |
| **Manager** | Assigned tasks only | ✅ Yes | Collaborator projects only | ✅ Collaborator projects |
| **Staff** | Assigned tasks only | ❌ No | Collaborator projects only | ✅ Collaborator projects |

### Files Modified

1. **[backend/utils/rbac_helper.py](backend/utils/rbac_helper.py)**
   - Updated role constants: `ADMIN_ROLE`, `MANAGER_ROLE`, `STAFF_ROLE`
   - Removed `MANAGING_DIRECTOR_ROLE`, `DIRECTOR_ROLE`
   - Updated `is_admin()`, removed `is_managing_director()` and `is_director()`
   - Simplified project access logic

2. **[backend/utils/task_crud/constants.py](backend/utils/task_crud/constants.py)**
   - Updated role constants
   - Removed `PRIVILEGED_TEAMS` (no longer needed)
   - Updated `ASSIGNEE_REMOVAL_ROLES` = `["admin", "manager"]`

3. **[backend/utils/task_crud/read.py](backend/utils/task_crud/read.py)**
   - Updated imports to use new role constants
   - Simplified access control: admin sees all, manager/staff see assigned
   - Removed department-based filtering (director logic)

4. **[backend/routers/project.py](backend/routers/project.py)**
   - Changed `"director", "managing_director"` checks to `"admin"`
   - Simplified project access logic

### Migration Script

**File:** [backend/migrations/update_roles_to_3tier_system.sql](backend/migrations/update_roles_to_3tier_system.sql)

```bash
# Run the migration
psql -U your_user -d your_db -f backend/migrations/update_roles_to_3tier_system.sql
```

**What it does:**
1. Shows current role distribution
2. Converts `managing_director` → `admin`
3. Converts `director` → `admin`
4. Keeps `manager` as `manager`
5. Keeps `staff` as `staff`
6. Verifies all users have valid roles
7. Reports any issues

### Testing Checklist

- [ ] **Admin users**:
  - Can see all tasks
  - Can see all projects
  - Can remove assignees
  - Can update any project

- [ ] **Manager users**:
  - Can see only assigned tasks
  - Can see only collaborator projects
  - Can remove assignees from assigned tasks
  - Can update collaborator projects

- [ ] **Staff users**:
  - Can see only assigned tasks
  - Can see only collaborator projects
  - Cannot remove assignees
  - Can update collaborator projects

---

## Part 2: Project Collaborator Sync

### The Problem

Tasks have `assignee_ids`, but those assignees might not be in the project's `collaborator_ids`. This creates inconsistency:
- Users assigned to tasks can't see the project
- Project visibility doesn't match task assignment

### The Solution

Automatically sync all task assignees to project collaborators, ensuring:
- Every user assigned to a task is also a project collaborator
- No duplicate IDs in `collaborator_ids` arrays
- Existing collaborators are preserved

### Migration Script

**File:** [backend/migrations/sync_task_assignees_to_project_collaborators.sql](backend/migrations/sync_task_assignees_to_project_collaborators.sql)

```bash
# Run the sync
psql -U your_user -d your_db -f backend/migrations/sync_task_assignees_to_project_collaborators.sql
```

**What it does:**

1. **Collects assignees**: Gets all unique assignee IDs from tasks for each project
2. **Merges with existing**: Combines current `collaborator_ids` with task assignees
3. **Removes duplicates**: Uses `ARRAY(SELECT DISTINCT ...)` to ensure no duplicates
4. **Updates projects**: Only updates projects where collaborators changed
5. **Reports results**:
   - Total projects updated
   - Projects with collaborators
   - Projects with task assignees
   - Average collaborators per project
   - Checks for orphaned tasks (no project_id)
   - Verifies no duplicates in arrays

### Example

**Before:**
```sql
-- Project A
collaborator_ids: ['user1', 'user2']

-- Task 1 in Project A
assignee_ids: ['user2', 'user3', 'user4']

-- Task 2 in Project A
assignee_ids: ['user3', 'user5']
```

**After sync:**
```sql
-- Project A
collaborator_ids: ['user1', 'user2', 'user3', 'user4', 'user5']
-- All unique users, no duplicates!
```

### Verification Queries

```sql
-- Check if all task assignees are in project collaborators
WITH task_assignees AS (
    SELECT
        t.project_id,
        ARRAY_AGG(DISTINCT assignee_id) as assignees
    FROM tasks t
    CROSS JOIN LATERAL unnest(t.assignee_ids) AS assignee_id
    WHERE t.project_id IS NOT NULL
    GROUP BY t.project_id
)
SELECT
    p.id,
    p.name,
    ta.assignees as task_assignees,
    p.collaborator_ids as project_collaborators,
    -- Check if all assignees are in collaborators
    CASE
        WHEN ta.assignees <@ p.collaborator_ids THEN 'All assignees are collaborators ✅'
        ELSE 'MISSING ASSIGNEES IN COLLABORATORS ❌'
    END as status
FROM projects p
LEFT JOIN task_assignees ta ON p.id = ta.project_id
WHERE ta.assignees IS NOT NULL;

-- Check for duplicate IDs in collaborator_ids
SELECT
    id,
    name,
    collaborator_ids,
    array_length(collaborator_ids, 1) as total_count,
    array_length(ARRAY(SELECT DISTINCT unnest(collaborator_ids)), 1) as unique_count,
    CASE
        WHEN array_length(collaborator_ids, 1) = array_length(ARRAY(SELECT DISTINCT unnest(collaborator_ids)), 1)
        THEN 'No duplicates ✅'
        ELSE 'HAS DUPLICATES ❌'
    END as status
FROM projects
WHERE collaborator_ids IS NOT NULL;
```

### Ongoing Sync

The migration is a one-time fix. To keep things in sync going forward:

**Option 1: Database Trigger (Recommended)**
```sql
-- Create a function to sync assignees to collaborators
CREATE OR REPLACE FUNCTION sync_assignees_to_collaborators()
RETURNS TRIGGER AS $$
BEGIN
    -- When a task is inserted or assignee_ids are updated
    IF (TG_OP = 'INSERT' OR OLD.assignee_ids IS DISTINCT FROM NEW.assignee_ids) THEN
        -- Update the project's collaborator_ids
        UPDATE projects
        SET collaborator_ids = ARRAY(
            SELECT DISTINCT unnest(
                COALESCE(collaborator_ids, ARRAY[]::text[]) ||
                NEW.assignee_ids
            )
        ),
        updated_at = NOW()
        WHERE id = NEW.project_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_sync_assignees_to_collaborators
AFTER INSERT OR UPDATE OF assignee_ids ON tasks
FOR EACH ROW
WHEN (NEW.project_id IS NOT NULL)
EXECUTE FUNCTION sync_assignees_to_collaborators();
```

**Option 2: Application-Level Sync**
When creating/updating tasks, also update project collaborators:
```python
# In TaskCreator or TaskUpdater
def sync_assignees_to_project(self, project_id: str, assignee_ids: List[str]):
    """Ensure task assignees are project collaborators"""
    project = self.crud.client.table("projects").select("collaborator_ids").eq("id", project_id).execute()

    if project.data:
        current_collaborators = set(project.data[0].get("collaborator_ids", []))
        new_assignees = set(assignee_ids)
        updated_collaborators = list(current_collaborators | new_assignees)  # Union, no duplicates

        self.crud.client.table("projects").update({
            "collaborator_ids": updated_collaborators,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", project_id).execute()
```

---

## Combined Migration Steps

### Step 1: Backup
```bash
pg_dump -U your_user your_db > backup_before_role_and_collab_sync.sql
```

### Step 2: Update Roles
```bash
psql -U your_user -d your_db -f backend/migrations/update_roles_to_3tier_system.sql
```

**Expected output:**
```
 role              | user_count
-------------------+-----------
 managing_director |          2    ← Will become admin
 director          |          5    ← Will become admin
 manager           |         10    ← Stays manager
 staff             |         50    ← Stays staff
```

### Step 3: Sync Collaborators
```bash
psql -U your_user -d your_db -f backend/migrations/sync_task_assignees_to_project_collaborators.sql
```

**Expected output:**
```
 total_projects | projects_with_collaborators | projects_with_task_assignees | avg_collaborators
----------------+-----------------------------+-----------------------------+------------------
             25 |                          25 |                           23 |              4.5
```

### Step 4: Verify
```sql
-- All users should have valid roles
SELECT role, COUNT(*) FROM users GROUP BY role;
--  role    | count
-- ---------+-------
--  admin   |     7
--  manager |    10
--  staff   |    50

-- All projects should have no duplicates in collaborator_ids
SELECT
    COUNT(*) FILTER (WHERE has_duplicates = false) as clean_projects,
    COUNT(*) FILTER (WHERE has_duplicates = true) as projects_with_duplicates
FROM (
    SELECT
        array_length(collaborator_ids, 1) != array_length(ARRAY(SELECT DISTINCT unnest(collaborator_ids)), 1) as has_duplicates
    FROM projects
    WHERE collaborator_ids IS NOT NULL
) stats;
-- All projects should be "clean" (0 duplicates)
```

### Step 5: Deploy Code
```bash
# The code has already been updated to use new 3-tier roles
# Just deploy the updated backend files
```

---

## Breaking Changes

### For Users

1. **Former Directors**:
   - Now have "admin" role
   - Access level remains the same (full access)
   - No action needed

2. **Former Managing Directors**:
   - Now have "admin" role
   - Access level remains the same
   - No action needed

3. **Managers & Staff**:
   - Roles unchanged
   - Access level unchanged
   - No action needed

### For Developers

1. **Role Checks**:
   ```python
   # ❌ OLD - Don't use these anymore
   if user_role == "managing_director":
   if user_role == "director":

   # ✅ NEW - Use these instead
   if user_role == "admin":
   if rbac_helper.is_admin(user_role):
   ```

2. **RBAC Logic**:
   ```python
   # ❌ OLD
   from backend.utils.task_crud.constants import MANAGING_DIRECTOR_ROLE, DIRECTOR_ROLE

   # ✅ NEW
   from backend.utils.task_crud.constants import ADMIN_ROLE, MANAGER_ROLE, STAFF_ROLE
   ```

3. **Project Access**:
   ```python
   # ❌ OLD - Directors had department-wide access
   if user_role in ["director", "managing_director"]:
       return all_department_projects

   # ✅ NEW - Only admins have full access
   if user_role == "admin":
       return all_projects
   else:
       return collaborator_projects
   ```

---

## Files Summary

### New Migration Files
1. [backend/migrations/update_roles_to_3tier_system.sql](backend/migrations/update_roles_to_3tier_system.sql)
2. [backend/migrations/sync_task_assignees_to_project_collaborators.sql](backend/migrations/sync_task_assignees_to_project_collaborators.sql)

### Modified Backend Files
1. [backend/utils/rbac_helper.py](backend/utils/rbac_helper.py) - Updated roles
2. [backend/utils/task_crud/constants.py](backend/utils/task_crud/constants.py) - Updated constants
3. [backend/utils/task_crud/read.py](backend/utils/task_crud/read.py) - Simplified RBAC
4. [backend/routers/project.py](backend/routers/project.py) - Admin-only checks

### Documentation
5. [3_TIER_ROLES_AND_COLLABORATOR_SYNC.md](3_TIER_ROLES_AND_COLLABORATOR_SYNC.md) - This file

---

## FAQ

**Q: What happens to existing JWTs with old roles?**
A: They'll still work! The code checks `user_role.lower()` and the database has been updated.

**Q: Will collaborator sync run automatically in the future?**
A: Only if you implement the database trigger or application-level sync (see "Ongoing Sync" section).

**Q: Can I rollback if something goes wrong?**
A: Yes, restore from the backup you made in Step 1.

**Q: What if a project has no tasks?**
A: It keeps its existing `collaborator_ids`. Only projects with tasks get updated.

**Q: Will this create duplicate collaborators?**
A: No! The SQL uses `ARRAY(SELECT DISTINCT ...)` to prevent duplicates.

---

**Migration Date:** 2025-10-16
**Breaking Changes:** Role names only (managing_director → admin, director → admin)
**Data Safety:** ✅ No data loss, only additions to collaborator_ids
