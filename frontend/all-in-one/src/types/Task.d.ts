export type TaskStatus = 'TO_DO' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH';

export interface User {
    id: string;
    email: string;
    username?: string;
    role: string;
    departments: string[];
}

export interface Comment {
    text: string;
    author: string;
    timestamp: string;
}

export interface Subtask {
    id: string;
    title: string;
    description: string;
    due_date?: string;
    status: TaskStatus;
    priority: TaskPriority;
    assignee_ids: string[];
    file_url?: string;
    is_archived: boolean;
    comments?: Comment[];
}

export interface Task {
    id: string;
    title: string;
    description: string;
    project_id: string;
    due_date?: string;
    status: TaskStatus;
    priority: TaskPriority;
    assignee_ids: string[];
    file_url?: string;
    assigned_to?: string; // legacy field for display
    owner_user_id: string;
    comments?: Comment[];
    attachments?: string[];
    is_archived: boolean;
    subtasks?: Subtask[];
}

export interface NewTask {
    title: string;
    description: string;
    project_id: string;
    status: TaskStatus;
    priority: TaskPriority;
    due_date: string;
    comments: string;
}

export interface NewSubtask {
    title: string;
    description: string;
    project_id: string;
    status: TaskStatus;
    priority: TaskPriority;
    due_date: string;
    comments: string;
}

export interface TaskCreatePayload {
    main_task: {
        title: string;
        description: string;
        project_id: string;
        due_date: string;
        priority: TaskPriority;
        assignee_ids: string[];
        file_url?: string;
    };
    subtasks: Array<{
        title: string;
        description: string;
        project_id: string;
        due_date: string;
        priority: TaskPriority;
        assignee_ids: string[];
        file_url?: string;
    }>;
}

export interface TaskUpdatePayload {
    main_task_id: string;
    main_task: {
        title: string;
        description: string;
        due_date: string;
        priority: TaskPriority;
        assignee_ids: string[];
        file_url?: string;
        is_archived?: boolean;
    };
    subtasks: {};
}


