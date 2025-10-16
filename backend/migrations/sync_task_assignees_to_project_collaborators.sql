-- Migration: Sync all task assignee_ids to their respective projects' collaborator_ids
-- This ensures that all users assigned to tasks are also collaborators on the project
-- Prevents duplicates using array_agg(DISTINCT ...)

-- Step 1: For each project, collect all unique assignee IDs from its tasks
WITH project_task_assignees AS (
    SELECT
        t.project_id,
        ARRAY_AGG(DISTINCT assignee_id) as task_assignees
    FROM tasks t
    CROSS JOIN LATERAL unnest(t.assignee_ids) AS assignee_id
    WHERE t.project_id IS NOT NULL
    GROUP BY t.project_id
),
-- Step 2: Combine existing collaborators with task assignees (removing duplicates)
updated_collaborators AS (
    SELECT
        p.id as project_id,
        p.collaborator_ids as existing_collaborators,
        COALESCE(pta.task_assignees, ARRAY[]::text[]) as task_assignees,
        -- Combine and deduplicate
        ARRAY(
            SELECT DISTINCT unnest(
                COALESCE(p.collaborator_ids, ARRAY[]::text[]) ||
                COALESCE(pta.task_assignees, ARRAY[]::text[])
            )
        ) as new_collaborators
    FROM projects p
    LEFT JOIN project_task_assignees pta ON p.id = pta.project_id
)
-- Step 3: Update projects with the combined collaborator list (only if changed)
UPDATE projects p
SET collaborator_ids = uc.new_collaborators,
    updated_at = NOW()
FROM updated_collaborators uc
WHERE p.id = uc.project_id
  AND (
    -- Only update if the arrays are different
    p.collaborator_ids IS DISTINCT FROM uc.new_collaborators
  );

-- Report on what was updated
WITH project_stats AS (
    SELECT
        p.id,
        p.name,
        array_length(p.collaborator_ids, 1) as collaborator_count,
        (
            SELECT COUNT(DISTINCT assignee_id)
            FROM tasks t
            CROSS JOIN LATERAL unnest(t.assignee_ids) AS assignee_id
            WHERE t.project_id = p.id
        ) as unique_assignee_count
    FROM projects p
)
SELECT
    COUNT(*) as total_projects,
    SUM(CASE WHEN collaborator_count > 0 THEN 1 ELSE 0 END) as projects_with_collaborators,
    SUM(CASE WHEN unique_assignee_count > 0 THEN 1 ELSE 0 END) as projects_with_task_assignees,
    AVG(collaborator_count) as avg_collaborators_per_project,
    MAX(collaborator_count) as max_collaborators_in_project
FROM project_stats;

-- Check for any tasks without a project_id (orphaned tasks)
SELECT
    COUNT(*) as orphaned_tasks_count,
    STRING_AGG(DISTINCT id::text, ', ') as orphaned_task_ids
FROM tasks
WHERE project_id IS NULL;

-- Verify no duplicate IDs in collaborator_ids arrays
SELECT
    p.id,
    p.name,
    array_length(p.collaborator_ids, 1) as collaborator_count,
    array_length(ARRAY(SELECT DISTINCT unnest(p.collaborator_ids)), 1) as unique_collaborator_count,
    CASE
        WHEN array_length(p.collaborator_ids, 1) = array_length(ARRAY(SELECT DISTINCT unnest(p.collaborator_ids)), 1)
        THEN 'No duplicates'
        ELSE 'HAS DUPLICATES!'
    END as status
FROM projects p
WHERE p.collaborator_ids IS NOT NULL
  AND array_length(p.collaborator_ids, 1) > 0;
