// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    REGISTER: 'auth/register',
    LOGIN: 'auth/login',
    LOGOUT: 'auth/logout',
    USERS: 'auth/users',
  },

  // Project endpoints
  PROJECTS: {
    CREATE: 'projects/create',
    LIST: 'projects/list',
    GET_BY_ID: (id: string) => `projects/${id}`,
    UPDATE: (id: string) => `projects/${id}`,
    DELETE: (id: string) => `projects/${id}`,
  },

  // Task endpoints
  TASKS: {
    CREATE: 'tasks/createTask',
    READ: 'tasks/readTasks',
    READ_ARCHIVED: 'tasks/readArchivedTasks',
    UPDATE: 'tasks/updateTask',
    FILTER_BY_DUE_DATE: 'tasks/filterByDueDate',
  },
  
  NOTIFICATIONS: {
    LIST: 'notifications/',
  },

} as const;


