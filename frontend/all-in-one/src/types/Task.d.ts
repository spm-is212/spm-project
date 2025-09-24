export interface Task {
    id: string;
    title: string;
    description: string;
    dueDate?: string;
    notes?: string;
    assignedTo?: string;
    completed: boolean;
}
