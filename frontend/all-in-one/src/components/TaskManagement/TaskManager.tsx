import { useState, useEffect, useCallback } from 'react';
import { Plus, Edit, Save, X, Calendar, User, AlertCircle, Archive, ArchiveRestore, Shield, Paperclip, FileText, Trash2 } from 'lucide-react';
import { apiFetch } from "../../utils/api";
import { getUserFromToken, getAccessToken } from '../../utils/auth';
import type { Task, NewTask, NewSubtask, User as UserType, TaskPriority } from '../../types/Task';

const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface Project {
  id: string;
  name: string;
  description?: string;
  team_id: string;
}

const TaskManager = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editingAssignees, setEditingAssignees] = useState<string[]>([]);
  const [showAddForm, setShowAddForm] = useState<boolean>(false);
  const [users, setUsers] = useState<UserType[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedAssignees, setSelectedAssignees] = useState<string[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<'priority' | 'date'>('priority');
  const [newTask, setNewTask] = useState<NewTask>({
    title: '',
    description: '',
    project_id: '',
    status: 'TO_DO',
    priority: 5,
    due_date: '',
    comments: '',
    recurrence_rule: '',       // DAILY, WEEKLY, MONTHLY
    recurrence_interval: 1,    // how many units
    recurrence_end_date: ''    // optional end date
  });
  const [subtasks, setSubtasks] = useState<NewSubtask[]>([]);
  const [showSubtaskForm, setShowSubtaskForm] = useState<boolean>(false);
  const [newSubtask, setNewSubtask] = useState<NewSubtask>({
    title: '',
    description: '',
    project_id: '',
    status: 'TO_DO',
    priority: 5,
    due_date: '',
    comments: ''
  });
  const [userInfo, setUserInfo] = useState<{ email: string; role: string; department?: string } | null>(null);
  const [editingNewSubtasks, setEditingNewSubtasks] = useState<NewSubtask[]>([]);
  const [showAddSubtaskInEdit, setShowAddSubtaskInEdit] = useState<boolean>(false);
  const [editingSubtaskIndex, setEditingSubtaskIndex] = useState<number | null>(null);
  const [editingSubtaskData, setEditingSubtaskData] = useState<NewSubtask | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [editingFile, setEditingFile] = useState<File | null>(null);
  const [removeFile, setRemoveFile] = useState<boolean>(false);

  useEffect(() => {
    const user = getUserFromToken();
    if (user) setUserInfo(user);
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      try {
        const payloadBase64 = token.split(".")[1];
        const payloadDecoded = JSON.parse(atob(payloadBase64));
        console.log("Decoded JWT payload:", payloadDecoded);
      } catch (e) {
        console.error("Failed to decode JWT", e);
      }
    }
  }, []);

// fetch projects
const fetchProjects = useCallback(async () => {
  try {
    const data = await apiFetch("projects/list");
    setProjects(data || []);
  } catch (err: unknown) {
    console.error(`Failed to fetch projects: ${err instanceof Error ? err.message : String(err)}`);
  }
}, []);

// fetch tasks
const fetchTasks = useCallback(async () => {
  setLoading(true);
  setError("");
  try {
    const data = await apiFetch("tasks/readTasks");  // <-- use apiFetch

    // Organize tasks: separate main tasks and subtasks
    const allTasks = data.tasks;
    const mainTasks = allTasks.filter(task => task.parent_id === null);
    const subtasksByParent = allTasks.filter(task => task.parent_id !== null)
      .reduce((acc, subtask) => {
        if (!acc[subtask.parent_id]) {
          acc[subtask.parent_id] = [];
        }
        acc[subtask.parent_id].push(subtask);
        return acc;
      }, {});

  const organizedTasks = mainTasks.map(mainTask => ({
    ...mainTask,
    subtasks: sortMode === 'priority'
    ? sortByPriority(subtasksByParent[mainTask.id] || [])
    : sortByDueDate(subtasksByParent[mainTask.id] || [])
  }));

  const sortedTasks =
  sortMode === 'priority'
    ? sortByPriority(organizedTasks)
    : sortByDueDate(organizedTasks);

  setTasks(sortedTasks);

  } catch (err: unknown) {
    setError(`Failed to fetch tasks: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
}, [sortMode]);

function sortByPriority(tasks: Task[]): Task[] {
  // Sort descending: higher number = higher priority
  return [...tasks].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));
}

function sortByDueDate(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });
}

function getUserIdFromToken(): string | null {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const payloadBase64 = token.split(".")[1];
    const payloadDecoded = JSON.parse(atob(payloadBase64));
    return payloadDecoded.sub || null;  // backend expects "sub" field
  } catch (e) {
    console.error("Failed to decode JWT", e);
    return null;
  }
}

function validateTask(task: NewTask, assignees: string[], currentUserId: string | null): string | null {
  if (!task.title.trim()) return "Task title is required";
  if (!task.description.trim()) return "Task description is required";
  if (!task.project_id) return "Project selection is required";

  const allowedStatuses = ["TO_DO", "IN_PROGRESS", "COMPLETED", "BLOCKED"];
  if (!allowedStatuses.includes(task.status.toUpperCase())) {
    return "Invalid status value";
  }

  if (task.priority < 1 || task.priority > 10) {
    return "Priority must be between 1 and 10";
  }

  if (!task.due_date) {
    return "Due date is required";
  } else {
    const today = new Date().toISOString().split("T")[0];
    if (task.due_date < today) {
      return "Due date cannot be in the past";
    }
  }

  // 🔹 Recurrence validation
  if (task.recurrence_rule) {
    if (!task.recurrence_end_date) {
      return "Recurrence end date is required for recurring tasks";
    }

    const dueDate = new Date(task.due_date);
    const endDate = new Date(task.recurrence_end_date);

    if (endDate < dueDate) {
      return "Recurrence end date cannot be before the due date";
    }
  }

  if (assignees.length === 0 && !currentUserId) {
    return "At least one assignee is required";
  }

  return null;
}

// fetch users from current user's department
const fetchUsers = useCallback(async () => {
  try {
    const data = await apiFetch("auth/users");
    setUsers(data.users);

    // Set current user as default assignee
    const userId = getUserIdFromToken();
    if (userId) {
      setCurrentUserId(userId);
      const currentUser = data.users.find(user => user.id === userId);
      if (currentUser) {
        setSelectedAssignees([userId]);
      }
    }
  } catch (err: unknown) {
    console.error(`Failed to fetch users: ${err instanceof Error ? err.message : String(err)}`);
    setError(`Failed to fetch team members: ${err instanceof Error ? err.message : String(err)}`)

    // Fallback: just set current user as available
    const userId = getUserIdFromToken();
    if (userId) {
      setCurrentUserId(userId);
      setSelectedAssignees([userId]);
      // Create a minimal user object for current user
      setUsers([{
        id: userId,
        email: 'current.user@company.com',
        username: 'current.user',
        role: 'staff',
        departments: []
      }]);
    }
  }
}, []);


const createTask = async (taskData: NewTask): Promise<void> => {
  setLoading(true);
  setError("");

  if (selectedFile && selectedFile.size > MAX_FILE_SIZE_BYTES) {
    setError(`File size exceeds maximum of ${MAX_FILE_SIZE_MB}MB`);
    setLoading(false);
    return;
  }

  if (taskData.due_date) {
    const selectedDate = taskData.due_date;
    const today = new Date().toISOString().split('T')[0];
    if (selectedDate < today) {
      setError('Due date cannot be in the past');
      setLoading(false);
      return;
    }
  }

  for (const subtask of subtasks) {
    if (subtask.due_date) {
      const selectedDate = subtask.due_date;
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate < today) {
        setError('Subtask due date cannot be in the past');
        setLoading(false);
        return;
      }
    }
  }

  try {
    const userId = getUserIdFromToken();

    const formattedSubtasks = subtasks.map(subtask => ({
      title: subtask.title,
      description: subtask.description,
      project_id: subtask.project_id,
      due_date: subtask.due_date,
      priority: subtask.priority,
      assignee_ids: userId ? [userId] : []
    }));

    const mainTaskAssignees = selectedAssignees.length > 0 ? selectedAssignees : (userId ? [userId] : []);

    const payload = {
      main_task: {
        title: taskData.title,
        description: taskData.description,
        project_id: taskData.project_id,
        due_date: taskData.due_date,
        priority: taskData.priority,
        assignee_ids: mainTaskAssignees,
        recurrence_rule: taskData.recurrence_rule || null,
        recurrence_interval: taskData.recurrence_interval || 1,
        recurrence_end_date: taskData.recurrence_end_date || null
      },
      subtasks: formattedSubtasks
    };

    const formData = new FormData();
    formData.append('task_data', JSON.stringify(payload));
    if (selectedFile) {
      formData.append('file', selectedFile);
    }

    const token = getAccessToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/tasks/createTask`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create task');
    }

    await fetchTasks();
    setShowAddForm(false);
    setNewTask({ title: "", description: "", project_id: "", status: "TO_DO", priority: 5, due_date: "", comments: "" });
    setSubtasks([]);
    setShowSubtaskForm(false);
    setSelectedFile(null);

    const currentUser = getUserIdFromToken();
    setSelectedAssignees(currentUser ? [currentUser] : []);
  } catch (err: unknown) {
    setError(`Failed to create task: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
};


const updateTask = async (taskId: string, taskData: Partial<Task>): Promise<void> => {
  setLoading(true);
  setError("");

  if (editingFile && editingFile.size > MAX_FILE_SIZE_BYTES) {
    setError(`File size exceeds maximum of ${MAX_FILE_SIZE_MB}MB`);
    setLoading(false);
    return;
  }

  try {
    const userId = getUserIdFromToken();

    const assigneeIds = editingAssignees.length > 0 ? editingAssignees : (userId ? [userId] : []);

    const formattedNewSubtasks = editingNewSubtasks.map(subtask => ({
      title: subtask.title,
      description: subtask.description,
      due_date: subtask.due_date,
      status: subtask.status,
      priority: subtask.priority,
      assignee_ids: selectedAssignees.length > 0 ? selectedAssignees : (userId ? [userId] : [])
    }));

    const payload = {
      main_task_id: taskId,
      main_task: {
        title: taskData.title,
        description: taskData.description,
        due_date: taskData.due_date,
        priority: taskData.priority,
        status: taskData.status,
        assignee_ids: assigneeIds,
        recurrence_rule: taskData.recurrence_rule || null,
        recurrence_interval: taskData.recurrence_interval || 1,
        recurrence_end_date: taskData.recurrence_end_date || null,
        ...(taskData.is_archived !== undefined && { is_archived: taskData.is_archived })
      },
      subtasks: {},
      ...(formattedNewSubtasks.length > 0 && { new_subtasks: formattedNewSubtasks })
    };

    const formData = new FormData();
    formData.append('task_data', JSON.stringify(payload));
    if (editingFile) {
      formData.append('file', editingFile);
    }
    formData.append('remove_file', removeFile.toString());

    const token = getAccessToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/tasks/updateTask`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update task');
    }

    await fetchTasks();
    setEditingTask(null);
    setEditingNewSubtasks([]);
    setShowAddSubtaskInEdit(false);
    setEditingFile(null);
    setRemoveFile(false);
  } catch (err: unknown) {
    setError(`Failed to update task: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
};


// archive/unarchive task
const archiveTask = async (taskId: string, isArchived: boolean): Promise<void> => {

  setLoading(true);
  setError("");
  try {
    const payload = {
      main_task_id: taskId,
      main_task: {
        is_archived: isArchived
      },
      subtasks: {}
    };

    const formData = new FormData();
    formData.append('task_data', JSON.stringify(payload));
    formData.append('remove_file', 'false');

    const token = getAccessToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/tasks/updateTask`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to archive/unarchive task');
    }

    await fetchTasks(); // Refresh the task list
  } catch (err: unknown) {
    setError(`Failed to archive/unarchive task: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
};

// Update subtask function
const updateSubtask = async (mainTaskId: string, subtaskId: string, subtaskData: Partial<Task>): Promise<void> => {
  setLoading(true);
  setError("");

  // Validate assignees
  if (!editingAssignees || editingAssignees.length === 0) {
    setError('Subtask must have at least one assignee');
    setLoading(false);
    return;
  }

  // Validate date
  if (subtaskData.due_date) {
    const selectedDate = subtaskData.due_date;
    const today = new Date().toISOString().split('T')[0];
    if (selectedDate < today) {
      setError('Due date cannot be in the past');
      setLoading(false);
      return;
    }
  }

  try {
    const userId = getUserIdFromToken();
    const assigneeIds = editingAssignees.length > 0 ? editingAssignees : (userId ? [userId] : []);
    const payload = {
      main_task_id: mainTaskId,
      main_task: {},
      subtasks: {
        [subtaskId]: {
          title: subtaskData.title,
          description: subtaskData.description,
          due_date: subtaskData.due_date,
          priority: subtaskData.priority,
          status: subtaskData.status,
          assignee_ids: assigneeIds,
          ...(subtaskData.is_archived !== undefined && { is_archived: subtaskData.is_archived })
        }
      }
    };

    const formData = new FormData();
    formData.append('task_data', JSON.stringify(payload));
    formData.append('remove_file', 'false');

    const token = getAccessToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/tasks/updateTask`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update subtask');
    }

    await fetchTasks();
    setEditingTask(null);
  } catch (err: unknown) {
    setError(`Failed to update subtask: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
};

// Archive/unarchive subtask function
const archiveSubtask = async (mainTaskId: string, subtaskId: string, isArchived: boolean): Promise<void> => {

  setLoading(true);
  setError("");
  try {
    const payload = {
      main_task_id: mainTaskId,
      main_task: {},
      subtasks: {
        [subtaskId]: {
          is_archived: isArchived
        }
      }
    };

    const formData = new FormData();
    formData.append('task_data', JSON.stringify(payload));
    formData.append('remove_file', 'false');

    const token = getAccessToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/tasks/updateTask`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to archive/unarchive subtask');
    }

    await fetchTasks(); // Refresh the task list
  } catch (err: unknown) {
    setError(`Failed to archive/unarchive subtask: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
};


  // Load tasks and users on component mount
  useEffect(() => {
    document.title = "Your task manager";
    fetchTasks();
    fetchUsers();
    fetchProjects();
  }, [fetchTasks, fetchUsers, fetchProjects]);

  // Subtask management functions
  const addSubtask = () => {
    if (!newSubtask.title.trim()) {
      setError('Subtask title is required');
      return;
    }

    // Validate date
    if (newSubtask.due_date) {
      const selectedDate = newSubtask.due_date;
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate < today) {
        setError('Subtask due date cannot be in the past');
        return;
      }
    }

    // Auto-populate project_id from main task
    const subtaskWithProject = { ...newSubtask, project_id: newTask.project_id, id: Date.now().toString() };
    setSubtasks([...subtasks, subtaskWithProject]);
    setNewSubtask({ title: '', description: '', project_id: '', status: 'TO_DO', priority: 5, due_date: '', comments: '' });
    setShowSubtaskForm(false);
  };

  const removeSubtask = (index: number) => {
    setSubtasks(subtasks.filter((_, i) => i !== index));
  };

  // New subtask management for editing
  const addNewSubtaskInEdit = () => {
    if (!newSubtask.title.trim()) {
      setError('Subtask title is required');
      return;
    }

    // Validate assignees
    if (!selectedAssignees || selectedAssignees.length === 0) {
      setError('Subtask must have at least one assignee');
      return;
    }

    // Validate date
    if (newSubtask.due_date) {
      const selectedDate = newSubtask.due_date;
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate < today) {
        setError('Subtask due date cannot be in the past');
        return;
      }
    }

    setEditingNewSubtasks([...editingNewSubtasks, { ...newSubtask, id: Date.now().toString() }]);
    setNewSubtask({ title: '', description: '', status: 'TO_DO', priority: 5, due_date: '', comments: '' });
    setShowAddSubtaskInEdit(false);
  };

  const removeNewSubtaskInEdit = (index: number) => {
    setEditingNewSubtasks(editingNewSubtasks.filter((_, i) => i !== index));
  };

  // Subtask editing functions for creation mode
  const startEditingSubtask = (index: number) => {
    setEditingSubtaskIndex(index);
    setEditingSubtaskData({ ...subtasks[index] });
  };

  const cancelEditingSubtask = () => {
    setEditingSubtaskIndex(null);
    setEditingSubtaskData(null);
  };

  const saveEditingSubtask = () => {
    if (!editingSubtaskData || editingSubtaskIndex === null) return;

    if (!editingSubtaskData.title.trim()) {
      setError('Subtask title is required');
      return;
    }

    // Validate date
    if (editingSubtaskData.due_date) {
      const selectedDate = editingSubtaskData.due_date;
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate < today) {
        setError('Subtask due date cannot be in the past');
        return;
      }
    }

    const updatedSubtasks = [...subtasks];
    updatedSubtasks[editingSubtaskIndex] = editingSubtaskData;
    setSubtasks(updatedSubtasks);

    setEditingSubtaskIndex(null);
    setEditingSubtaskData(null);
  };

  // Handle form submissions
  const handleCreateSubmit = () => {
    const userId = getUserIdFromToken();

    const errorMsg = validateTask(newTask, selectedAssignees, userId);
    if (errorMsg) {
      setError(errorMsg);
      return;
    }

    // Validate assignees
    if (!selectedAssignees || selectedAssignees.length === 0) {
      setError('Task must have at least one assignee');
      return;
    }
    createTask(newTask);
  };


  const handleUpdateSubmit = () => {
    if (!editingTask.title.trim()) {
      setError('Task title is required');
      return;
    }

    // Validate assignees
    if (!editingAssignees || editingAssignees.length === 0) {
      setError('Task must have at least one assignee');
      return;
    }

    // Validate date
    if (editingTask.due_date) {
      const selectedDate = editingTask.due_date;
      const today = new Date().toISOString().split('T')[0];
      if (selectedDate < today) {
        setError('Due date cannot be in the past');
        return;
      }
    }

    updateTask(editingTask.id, editingTask);
  };

  // Convert numeric priority to string label
  const getPriorityLabel = (priority: number | string | undefined): string => {
    const num = Number(priority);
    if (isNaN(num)) return 'UNKNOWN';
    if (num >= 8) return 'HIGH';
    if (num >= 4) return 'MEDIUM';
    return 'LOW';
  };

  // Get priority color
  const getPriorityColor = (priority: number | undefined): string => {
    if (!priority) return 'text-gray-600 bg-gray-100';

    if (priority >= 8) return 'text-red-600 bg-red-100';    // High
    if (priority >= 4) return 'text-yellow-600 bg-yellow-100'; // Medium
    return 'text-green-600 bg-green-100';                   // Low
  };

  // Get status color
  const getStatusColor = (status: string | undefined): string => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED': return 'text-green-600 bg-green-100';
      case 'IN_PROGRESS': return 'text-blue-600 bg-blue-100';
      case 'TO_DO': return 'text-gray-600 bg-gray-100';
      case 'BLOCKED': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Check if current user can remove assignees (mirrors backend logic)
  const canRemoveAssignees = (): boolean => {
    if (!userInfo) return false;

    // Check role
    if (['manager', 'director', 'managing_director'].includes(userInfo.role)) {
      return true;
    }

    // Check privileged teams (note: userInfo doesn't have teams, so this will always be false for now)
    // This would need to be extended when team information is available in userInfo
    const privilegedTeams = ['sales manager', 'finance managers'];
    // return userInfo.teams?.some(team => privilegedTeams.includes(team)) || false;

    return false;
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 className="text-3xl font-bold text-gray-900">Smart Task Manager</h1>
        </div>
        <p className="text-gray-600">Manage your tasks efficiently with full CRUD operations</p>
        <div className="flex space-x-2">
  <label className="text-sm text-gray-600">Sort by:</label>
  <select
    value={sortMode}
    onChange={(e) => setSortMode(e.target.value as 'priority' | 'date')}
    className="border rounded px-2 py-1 text-sm"
  >
    <option value="priority">Priority</option>
    <option value="date">Due Date</option>
  </select>
</div>


        {userInfo && (
          <div className="mb-6 p-4 bg-gray-50 border rounded-lg flex items-center space-x-4 shadow-sm">
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-blue-600" />
              <span className="text-gray-800 font-medium">{userInfo.department}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-green-600" />
              <span className="uppercase text-sm font-semibold text-green-700">
                {userInfo.role}
              </span>
            </div>
          </div>
        )}


      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={() => setError('')}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mb-6 flex space-x-4">
        <button
          onClick={() => setShowAddForm(true)}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add New Task
        </button>
      </div>

      {/* Add Task Form */}
      {showAddForm && (
        <div className="mb-8 p-6 bg-gray-50 rounded-lg border">
          <h2 className="text-xl font-semibold mb-4">Create New Task</h2>
                        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={newTask.title}
                  onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter task title"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Project *</label>
                <select
                  value={newTask.project_id}
                  onChange={(e) => setNewTask({...newTask, project_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a project...</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={newTask.status}
                  onChange={(e) => setNewTask({...newTask, status: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="TO_DO">To Do</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="BLOCKED">Blocked</option>
                </select>
              </div>
             <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority (1–10)</label>
              <input
                type="number"
                min="1"
                max="10"
                value={newTask.priority}
                onChange={(e) => setNewTask({ ...newTask, priority: Number(e.target.value) })}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => {
                    setNewTask({...newTask, due_date: e.target.value});
                  }}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Recurrence</label>
                <select
                  value={newTask.recurrence_rule}
                  onChange={(e) => setNewTask({...newTask, recurrence_rule: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Does not repeat</option>
                  <option value="DAILY">Daily</option>
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                </select>
              </div>

              {newTask.recurrence_rule && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Repeat Every</label>
                    <input
                      type="number"
                      min="1"
                      value={newTask.recurrence_interval}
                      onChange={(e) => setNewTask({...newTask, recurrence_interval: parseInt(e.target.value)})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Recurrence</label>
                    <input
                      type="date"
                      value={newTask.recurrence_end_date}
                      onChange={(e) => setNewTask({...newTask, recurrence_end_date: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                <div className="relative">
                  <div className="w-full min-h-[40px] p-2 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 bg-white">
                    {/* Selected Users */}
                    <div className="flex flex-wrap gap-2 mb-2">
                      {selectedAssignees.map(userId => {
                        const user = users.find(u => u.id === userId);
                        const isCurrentUser = userId === currentUserId;
                        return (
                          <span
                            key={userId}
                            className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${
                              isCurrentUser
                                ? 'bg-blue-100 text-blue-800 opacity-75'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                            {isCurrentUser && ' (You)'}
                            {(!isCurrentUser || canRemoveAssignees()) && (
                              <button
                                type="button"
                                onClick={() => setSelectedAssignees(prev => prev.filter(id => id !== userId))}
                                className="ml-1 text-gray-500 hover:text-gray-700"
                              >
                                ×
                              </button>
                            )}
                          </span>
                        );
                      })}
                    </div>

                    {/* Dropdown */}
                    <select
                      onChange={(e) => {
                        const userId = e.target.value;
                        if (userId && !selectedAssignees.includes(userId)) {
                          if (selectedAssignees.length >= 5) {
                            setError('Maximum of 5 assignees allowed per task');
                            e.target.value = ''; // Reset selection
                            return;
                          }
                          setSelectedAssignees(prev => [...prev, userId]);
                        }
                        e.target.value = ''; // Reset selection
                      }}
                      className="w-full text-sm bg-transparent border-none focus:outline-none"
                    >
                      <option value="">Add team member...</option>
                      {users
                        .filter(user => !selectedAssignees.includes(user.id))
                        .map(user => (
                          <option key={user.id} value={user.id}>
                            {user.username || user.email?.split('@')[0]} ({user.email})
                          </option>
                        ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows="3"
                placeholder="Enter task description"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Attachment (Max {MAX_FILE_SIZE_MB}MB)</label>
              <div className="flex items-center space-x-2">
                <input
                  type="file"
                  id="task-file-input"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      if (file.size > MAX_FILE_SIZE_BYTES) {
                        setError(`File size exceeds maximum of ${MAX_FILE_SIZE_MB}MB`);
                        e.target.value = '';
                        return;
                      }
                      setSelectedFile(file);
                    }
                  }}
                  className="hidden"
                />
                <label
                  htmlFor="task-file-input"
                  className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Paperclip className="w-4 h-4 mr-2" />
                  Choose File
                </label>
                {selectedFile && (
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-gray-600">{selectedFile.name}</span>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="text-red-600 hover:text-red-800"
                      type="button"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Subtasks Section */}
            <div className="border-t pt-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-md font-semibold text-gray-800">Subtasks ({subtasks.length})</h3>
                <button
                  type="button"
                  onClick={() => setShowSubtaskForm(!showSubtaskForm)}
                  className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 flex items-center"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Add Subtask
                </button>
              </div>

              {/* Existing Subtasks */}
              {subtasks.length > 0 && (
                <div className="space-y-2 mb-3">
                  {subtasks.map((subtask, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded border">
                      {editingSubtaskIndex === index ? (
                        /* Subtask Edit Form */
                        <div className="space-y-3">
                          <input
                            type="text"
                            value={editingSubtaskData?.title || ''}
                            onChange={(e) => setEditingSubtaskData(prev => prev ? {...prev, title: e.target.value} : null)}
                            className="w-full p-2 border border-gray-300 rounded text-sm font-medium"
                            placeholder="Subtask title"
                          />
                          <textarea
                            value={editingSubtaskData?.description || ''}
                            onChange={(e) => setEditingSubtaskData(prev => prev ? {...prev, description: e.target.value} : null)}
                            className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
                            rows={2}
                            placeholder="Subtask description"
                          />
                          <div className="grid grid-cols-3 gap-2">
                            <select
                              value={editingSubtaskData?.status || 'TO_DO'}
                              onChange={(e) => setEditingSubtaskData(prev => prev ? {...prev, status: e.target.value} : null)}
                              className="p-2 border border-gray-300 rounded text-sm"
                            >
                              <option value="TO_DO">To Do</option>
                              <option value="IN_PROGRESS">In Progress</option>
                              <option value="COMPLETED">Completed</option>
                              <option value="BLOCKED">Blocked</option>
                            </select>
                            <input
                              type="number"
                              min="1"
                              max="10"
                              value={editingSubtaskData?.priority ?? 5}
                              onChange={(e) => setEditingSubtaskData(prev => prev ? {...prev, priority: Number(e.target.value)} : null)}
                              className="p-2 border border-gray-300 rounded text-sm"
                            />
                            <input
                              type="date"
                              value={editingSubtaskData?.due_date || ''}
                              onChange={(e) => setEditingSubtaskData(prev => prev ? {...prev, due_date: e.target.value} : null)}
                              className="p-2 border border-gray-300 rounded text-sm"
                            />
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={saveEditingSubtask}
                              className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 flex items-center"
                            >
                              <Save className="w-3 h-3 mr-1" />
                              Save
                            </button>
                            <button
                              onClick={cancelEditingSubtask}
                              className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                            >
                              <X className="w-3 h-3 mr-1" />
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        /* Subtask Display */
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-medium text-sm">{subtask.title}</div>
                            {subtask.description && <div className="text-xs text-gray-600 mt-1">{subtask.description}</div>}
                            <div className="flex space-x-2 mt-1">
                              <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">{subtask.status?.replace('_', ' ')}</span>
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{subtask.priority}</span>
                              {subtask.due_date && <span className="text-xs text-gray-500">Due: {new Date(subtask.due_date).toLocaleDateString()}</span>}
                            </div>
                          </div>
                          <div className="flex space-x-1 ml-2">
                            <button
                              type="button"
                              onClick={() => startEditingSubtask(index)}
                              className="text-blue-600 hover:text-blue-800 p-1"
                              title="Edit subtask"
                            >
                              <Edit className="w-3 h-3" />
                            </button>
                            <button
                              type="button"
                              onClick={() => removeSubtask(index)}
                              className="text-red-500 hover:text-red-700 p-1"
                              title="Remove subtask"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Add Subtask Form */}
              {showSubtaskForm && (
                <div className="bg-blue-50 p-4 rounded border space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Subtask Title</label>
                      <input
                        type="text"
                        value={newSubtask.title}
                        onChange={(e) => setNewSubtask({...newSubtask, title: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Enter subtask title"
                        required
                      />
                    </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Priority (1–10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={newSubtask.priority}
                      onChange={(e) => setNewSubtask({ ...newSubtask, priority: Number(e.target.value) })}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                      <input
                        type="date"
                        value={newSubtask.due_date}
                        onChange={(e) => {
                          setNewSubtask({...newSubtask, due_date: e.target.value});
                        }}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={newSubtask.description}
                      onChange={(e) => setNewSubtask({...newSubtask, description: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows="2"
                      placeholder="Enter subtask description"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={addSubtask}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 flex items-center"
                    >
                      <Save className="w-3 h-3 mr-1" />
                      Add Subtask
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowSubtaskForm(false)}
                      className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                    >
                      <X className="w-3 h-3 mr-1" />
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                type="button"
                onClick={handleCreateSubmit}
                disabled={loading}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <Save className="w-4 h-4 mr-2" />
                Create Task
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setSubtasks([]);
                  setShowSubtaskForm(false);
                  setSelectedFile(null);
                }}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      )}

      {/* Tasks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
            {editingTask && editingTask.id === task.id ? (
              /* Edit Form */
              <div className="space-y-3">
                <input
                  type="text"
                  value={editingTask.title}
                  onChange={(e) => setEditingTask({...editingTask, title: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded text-lg font-semibold"
                  required
                />
                <textarea
                  value={editingTask.description}
                  onChange={(e) => setEditingTask({...editingTask, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded text-sm"
                  rows="2"
                />
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={editingTask.status}
                    onChange={(e) => setEditingTask({...editingTask, status: e.target.value})}
                    className="p-1 border border-gray-300 rounded text-xs"
                  >
                    <option value="TO_DO">To Do</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="BLOCKED">Blocked</option>
                  </select>
                 <input
                  type="number"
                  min="1"
                  max="10"
                  value={editingTask.priority ?? 5}
                  onChange={(e) => setEditingTask({...editingTask, priority: Number(e.target.value)})}
                  className="p-1 border border-gray-300 rounded text-xs"
                />

                </div>
                <input
                  type="date"
                  value={editingTask.due_date}
                  onChange={(e) => {
                    setEditingTask({...editingTask, due_date: e.target.value});
                  }}
                  className="w-full p-1 border border-gray-300 rounded text-xs"
                /><select
                  value={editingTask.recurrence_rule || ""}
                  onChange={(e) => setEditingTask({ ...editingTask, recurrence_rule: e.target.value })}
                  className="p-1 border border-gray-300 rounded text-xs"
                >
                  <option value="">Does not repeat</option>
                  <option value="DAILY">Daily</option>
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                </select>

                {editingTask.recurrence_rule && (
                  <>
                    <input
                      type="number"
                      min="1"
                      value={editingTask.recurrence_interval || 1}
                      onChange={(e) =>
                        setEditingTask({
                          ...editingTask,
                          recurrence_interval: parseInt(e.target.value) || 1,
                        })
                      }
                      className="p-1 border border-gray-300 rounded text-xs"
                      placeholder="Interval"
                    />
                    <input
                      type="date"
                      value={editingTask.recurrence_end_date || ""}
                      onChange={(e) =>
                        setEditingTask({ ...editingTask, recurrence_end_date: e.target.value })
                      }
                      className="p-1 border border-gray-300 rounded text-xs"
                    />
                  </>
                )}
                <div className="relative">
                  <div className="w-full min-h-[32px] p-1 border border-gray-300 rounded text-xs bg-white">
                    {/* Selected Users */}
                    <div className="flex flex-wrap gap-1 mb-1">
                      {editingAssignees.map(userId => {
                        const user = users.find(u => u.id === userId);
                        const isCurrentUser = userId === currentUserId;
                        return (
                          <span
                            key={userId}
                            className={`inline-flex items-center px-1 py-0.5 text-xs rounded-full ${
                              isCurrentUser
                                ? 'bg-blue-100 text-blue-800 opacity-75'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                            {isCurrentUser && ' (You)'}
                            {(!isCurrentUser || canRemoveAssignees()) && (
                              <button
                                type="button"
                                onClick={() => setEditingAssignees(prev => prev.filter(id => id !== userId))}
                                className="ml-1 text-gray-500 hover:text-gray-700"
                              >
                                ×
                              </button>
                            )}
                          </span>
                        );
                      })}
                    </div>

                    {/* Dropdown */}
                    <select
                      onChange={(e) => {
                        const userId = e.target.value;
                        if (userId && !editingAssignees.includes(userId)) {
                          if (editingAssignees.length >= 5) {
                            setError('Maximum of 5 assignees allowed per task');
                            return;
                          }
                          setEditingAssignees(prev => [...prev, userId]);
                        }
                        e.target.value = '';
                      }}
                      className="w-full text-xs border-0 outline-none bg-transparent"
                      value=""
                    >
                      <option value="">Add assignee...</option>
                      {users
                        .filter(user => !editingAssignees.includes(user.id))
                        .map(user => (
                          <option key={user.id} value={user.id}>
                            {user.username || user.email?.split('@')[0] || 'Unknown'}
                            {user.team ? ` (${user.team})` : ''}
                          </option>
                        ))
                      }
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Attachment (Max {MAX_FILE_SIZE_MB}MB)</label>
                  {editingTask.file_url && !removeFile && !editingFile && (
                    <div className="flex items-center space-x-2 mb-2 p-2 bg-blue-50 border border-blue-200 rounded">
                      <FileText className="w-4 h-4 text-blue-600" />
                      <a
                        href={editingTask.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline flex-1"
                      >
                        View Current File
                      </a>
                      <button
                        onClick={() => setRemoveFile(true)}
                        className="text-red-600 hover:text-red-800"
                        type="button"
                        title="Remove file"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  {removeFile && (
                    <div className="text-xs text-red-600 mb-2">File will be removed on save</div>
                  )}
                  <div className="flex items-center space-x-2">
                    <input
                      type="file"
                      id="edit-task-file-input"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (file.size > MAX_FILE_SIZE_BYTES) {
                            setError(`File size exceeds maximum of ${MAX_FILE_SIZE_MB}MB`);
                            e.target.value = '';
                            return;
                          }
                          setEditingFile(file);
                          setRemoveFile(false);
                        }
                      }}
                      className="hidden"
                    />
                    <label
                      htmlFor="edit-task-file-input"
                      className="cursor-pointer inline-flex items-center px-2 py-1 border border-gray-300 rounded shadow-sm text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <Paperclip className="w-3 h-3 mr-1" />
                      {editingTask.file_url ? 'Replace File' : 'Add File'}
                    </label>
                    {editingFile && (
                      <div className="flex items-center space-x-2">
                        <FileText className="w-3 h-3 text-green-600" />
                        <span className="text-xs text-gray-600">{editingFile.name}</span>
                        <button
                          onClick={() => setEditingFile(null)}
                          className="text-red-600 hover:text-red-800"
                          type="button"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={handleUpdateSubmit}
                    disabled={loading}
                    className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50 flex items-center"
                  >
                    <Save className="w-3 h-3 mr-1" />
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingTask(null);
                      setEditingNewSubtasks([]);
                      setShowAddSubtaskInEdit(false);
                      setEditingFile(null);
                      setRemoveFile(false);
                    }}
                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Cancel
                  </button>
                </div>

                {/* Add New Subtask Section for Main Task Edit */}
                <div className="mt-4 pt-4 border-t">
                  {/* New Subtasks Display */}
                  {editingNewSubtasks.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">
                        New Subtasks ({editingNewSubtasks.length})
                      </div>
                      <div className="space-y-2">
                        {editingNewSubtasks.map((newSubtask, index) => (
                          <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <h4 className="text-sm font-medium text-gray-900">{newSubtask.title}</h4>
                                {newSubtask.description && (
                                  <p className="text-xs text-gray-600 mt-1">{newSubtask.description}</p>
                                )}
                                <div className="flex space-x-2 mt-2">
                                 <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(newSubtask.priority)}`}>
                                  {newSubtask.priority}
                                </span>

                                  {newSubtask.due_date && (
                                    <span className="text-xs text-gray-600">
                                      Due: {new Date(newSubtask.due_date).toLocaleDateString()}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <button
                                onClick={() => removeNewSubtaskInEdit(index)}
                                className="text-red-600 hover:text-red-800 p-1"
                                title="Remove subtask"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Add Subtask Button */}
                  {!showAddSubtaskInEdit && (
                    <button
                      onClick={() => setShowAddSubtaskInEdit(true)}
                      className="w-full p-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add New Subtask
                    </button>
                  )}

                  {/* Add Subtask Form */}
                  {showAddSubtaskInEdit && (
                    <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                      <div className="space-y-3">
                        <input
                          type="text"
                          placeholder="Subtask title"
                          value={newSubtask.title}
                          onChange={(e) => setNewSubtask({...newSubtask, title: e.target.value})}
                          className="w-full p-2 border border-gray-300 rounded text-sm"
                        />
                        <textarea
                          placeholder="Subtask description"
                          value={newSubtask.description}
                          onChange={(e) => setNewSubtask({...newSubtask, description: e.target.value})}
                          className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
                          rows={2}
                        />
                        <div className="grid grid-cols-3 gap-2">
                          <select
                            value={newSubtask.status || 'TO_DO'}
                            onChange={(e) => setNewSubtask({...newSubtask, status: e.target.value})}
                            className="p-2 border border-gray-300 rounded text-sm"
                          >
                            <option value="TO_DO">To Do</option>
                            <option value="IN_PROGRESS">In Progress</option>
                            <option value="COMPLETED">Completed</option>
                            <option value="BLOCKED">Blocked</option>
                          </select>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            value={newSubtask.priority ?? 5}
                            onChange={(e) => setNewSubtask({...newSubtask, priority: Number(e.target.value)})}
                            className="p-2 border border-gray-300 rounded text-sm"
                          />
                          <input
                            type="date"
                            value={newSubtask.due_date}
                            onChange={(e) => setNewSubtask({...newSubtask, due_date: e.target.value})}
                            className="p-2 border border-gray-300 rounded text-sm"
                          />
                        </div>

                        {/* Assignee Selection */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                          <div className="relative">
                            <div className="w-full min-h-[40px] p-2 border border-gray-300 rounded-lg bg-white">
                              {/* Selected Users */}
                              <div className="flex flex-wrap gap-1 mb-1">
                                {selectedAssignees.map(userId => {
                                  const user = users.find(u => u.id === userId);
                                  const isCurrentUser = userId === currentUserId;
                                  return (
                                    <span
                                      key={userId}
                                      className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${
                                        isCurrentUser
                                          ? 'bg-blue-100 text-blue-800 opacity-75'
                                          : 'bg-gray-100 text-gray-800'
                                      }`}
                                    >
                                      {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                                      {isCurrentUser && ' (You)'}
                                      {(!isCurrentUser || canRemoveAssignees()) && (
                                        <button
                                          type="button"
                                          onClick={() => setSelectedAssignees(prev => prev.filter(id => id !== userId))}
                                          className="ml-1 text-gray-500 hover:text-gray-700"
                                        >
                                          ×
                                        </button>
                                      )}
                                    </span>
                                  );
                                })}
                              </div>

                              {/* Dropdown */}
                              <select
                                onChange={(e) => {
                                  const userId = e.target.value;
                                  if (userId && !selectedAssignees.includes(userId)) {
                                    if (selectedAssignees.length >= 5) {
                                      setError('Maximum of 5 assignees allowed per task');
                                      e.target.value = '';
                                      return;
                                    }
                                    setSelectedAssignees(prev => [...prev, userId]);
                                  }
                                  e.target.value = '';
                                }}
                                className="w-full text-sm bg-transparent border-none focus:outline-none"
                              >
                                <option value="">Add team member...</option>
                                {users
                                  .filter(user => !selectedAssignees.includes(user.id))
                                  .map(user => (
                                    <option key={user.id} value={user.id}>
                                      {user.username || user.email?.split('@')[0] || 'Unknown'}
                                      {user.team ? ` (${user.team})` : ''}
                                    </option>
                                  ))
                                }
                              </select>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={addNewSubtaskInEdit}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 flex items-center"
                          >
                            <Plus className="w-3 h-3 mr-1" />
                            Add
                          </button>
                          <button
                            onClick={() => {
                              setShowAddSubtaskInEdit(false);
                              setNewSubtask({ title: '', description: '', status: 'TO_DO', priority: 5, due_date: '', comments: '' });
                            }}
                            className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                          >
                            <X className="w-3 h-3 mr-1" />
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Task Display */
              <>
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">{task.title}</h3>
                  <div className="flex space-x-1 ml-2">
                    <button
                      onClick={() => {
                        setEditingTask(task);
                        setEditingAssignees(task.assignee_ids || []);
                        setEditingFile(null);
                        setRemoveFile(false);
                      }}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Edit task"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => archiveTask(task.id, !task.is_archived)}
                      className={`p-1 ${task.is_archived ? 'text-green-600 hover:text-green-800' : 'text-orange-600 hover:text-orange-800'}`}
                      title={task.is_archived ? "Unarchive task" : "Archive task"}
                      disabled={loading}
                    >
                      {task.is_archived ? <ArchiveRestore className="w-4 h-4" /> : <Archive className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {task.description && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">{task.description}</p>
                )}

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status?.replace('_', ' ').toUpperCase()}
                      </span>
                      {task.is_archived && (
                        <span className="px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-200">
                          ARCHIVED
                        </span>
                      )}
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                      {getPriorityLabel(task.priority)}
                    </span>
                  </div>

                  {task.due_date && (
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}

                  {task.recurrence_rule && (
                    <div className="flex items-center text-sm text-gray-600">
                      Repeats every {task.recurrence_interval}{" "}
                      {task.recurrence_rule.toLowerCase()}
                      {task.recurrence_interval > 1 ? "s" : ""}
                      {task.recurrence_end_date &&
                        ` until ${new Date(task.recurrence_end_date).toLocaleDateString()}`}
                    </div>
                  )}


                  {task.assignee_ids && task.assignee_ids.length > 0 && (
                    <div className="flex items-center text-sm text-gray-600">
                      <User className="w-4 h-4 mr-1" />
                      <div className="flex flex-wrap gap-1">
                        {task.assignee_ids.map(assigneeId => {
                          const user = users.find(u => u.id === assigneeId);
                          return (
                            <span key={assigneeId} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs">
                              {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {task.file_url && (
                    <div className="flex items-center text-sm">
                      <Paperclip className="w-4 h-4 mr-1 text-gray-600" />
                      <a
                        href={task.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        View Attachment
                      </a>
                    </div>
                  )}

                  {/* Subtasks Display */}
                  {(task.subtasks && task.subtasks.length > 0) || (editingTask && editingTask.id === task.id) ? (
                    <div className="mt-4 pt-4 border-t">
                      {task.subtasks && task.subtasks.length > 0 && (
                        <>
                          <div className="text-sm font-medium text-gray-700 mb-3">
                            Subtasks ({task.subtasks.length})
                          </div>
                          <div className="space-y-3">
                            {task.subtasks.map((subtask, index) => (
                              <div key={subtask.id || index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                            {editingTask && editingTask.id === subtask.id ? (
                              /* Subtask Edit Form */
                              <div className="space-y-3">
                                <input
                                  type="text"
                                  value={editingTask.title}
                                  onChange={(e) => setEditingTask({...editingTask, title: e.target.value})}
                                  className="w-full p-2 border border-gray-300 rounded text-sm font-medium"
                                  required
                                />
                                <textarea
                                  value={editingTask.description}
                                  onChange={(e) => setEditingTask({...editingTask, description: e.target.value})}
                                  className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
                                  rows={2}
                                />
                                <div className="grid grid-cols-3 gap-2">
                                  <select
                                    value={editingTask.status}
                                    onChange={(e) => setEditingTask({...editingTask, status: e.target.value})}
                                    className="w-full p-1 border border-gray-300 rounded text-xs"
                                  >
                                    <option value="TO_DO">To Do</option>
                                    <option value="IN_PROGRESS">In Progress</option>
                                    <option value="COMPLETED">Completed</option>
                                    <option value="BLOCKED">Blocked</option>
                                  </select>
                                  <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={editingTask.priority ?? 5}
                                    onChange={(e) => setEditingTask({...editingTask, priority: Number(e.target.value)})}
                                    className="p-1 border border-gray-300 rounded text-xs"
                                  />
                                  <input
                                    type="date"
                                    value={editingTask.due_date}
                                    onChange={(e) => {
                                      setEditingTask({...editingTask, due_date: e.target.value});
                                    }}
                                    className="w-full p-1 border border-gray-300 rounded text-xs"
                                  />
                                </div>
                                <div className="relative">
                                  <div className="w-full min-h-[32px] p-1 border border-gray-300 rounded text-xs bg-white">
                                    {/* Selected Users */}
                                    <div className="flex flex-wrap gap-1 mb-1">
                                      {editingAssignees.map(userId => {
                                        const user = users.find(u => u.id === userId);
                                        const isCurrentUser = userId === currentUserId;
                                        return (
                                          <span
                                            key={userId}
                                            className={`inline-flex items-center px-1 py-0.5 text-xs rounded-full ${
                                              isCurrentUser
                                                ? 'bg-blue-100 text-blue-800 opacity-75'
                                                : 'bg-gray-100 text-gray-800'
                                            }`}
                                          >
                                            {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                                            {isCurrentUser && ' (You)'}
                                            {(!isCurrentUser || canRemoveAssignees()) && (
                                              <button
                                                type="button"
                                                onClick={() => setEditingAssignees(prev => prev.filter(id => id !== userId))}
                                                className="ml-1 text-gray-500 hover:text-gray-700"
                                              >
                                                ×
                                              </button>
                                            )}
                                          </span>
                                        );
                                      })}
                                    </div>

                                    {/* Dropdown */}
                                    <select
                                      onChange={(e) => {
                                        const userId = e.target.value;
                                        if (userId && !editingAssignees.includes(userId)) {
                                          if (editingAssignees.length >= 5) {
                                            setError('Maximum of 5 assignees allowed per task');
                                            return;
                                          }
                                          setEditingAssignees(prev => [...prev, userId]);
                                        }
                                        e.target.value = '';
                                      }}
                                      className="w-full text-xs border-0 outline-none bg-transparent"
                                      value=""
                                    >
                                      <option value="">Add assignee...</option>
                                      {users
                                        .filter(user => !editingAssignees.includes(user.id))
                                        .map(user => (
                                          <option key={user.id} value={user.id}>
                                            {user.username || user.email?.split('@')[0] || 'Unknown'}
                                            {user.team ? ` (${user.team})` : ''}
                                          </option>
                                        ))
                                      }
                                    </select>
                                  </div>
                                </div>
                                <div className="flex space-x-2">
                                  <button
                                    type="button"
                                    onClick={() => updateSubtask(task.id, subtask.id, editingTask)}
                                    disabled={loading}
                                    className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50 flex items-center"
                                  >
                                    <Save className="w-3 h-3 mr-1" />
                                    Save
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                      setEditingTask(null);
                      setEditingNewSubtasks([]);
                      setShowAddSubtaskInEdit(false);
                      setEditingFile(null);
                      setRemoveFile(false);
                    }}
                                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                                  >
                                    <X className="w-3 h-3 mr-1" />
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              /* Subtask Display */
                              <>
                                <div className="flex justify-between items-start mb-2">
                                  <h4 className="text-sm font-medium text-gray-900 flex-1">{subtask.title}</h4>
                                  <div className="flex space-x-1 ml-2">
                                    <button
                                      onClick={() => {
                                        setEditingTask(subtask);
                                        setEditingAssignees(subtask.assignee_ids || []);
                                      }}
                                      className="text-blue-600 hover:text-blue-800 p-1"
                                      title="Edit subtask"
                                    >
                                      <Edit className="w-3 h-3" />
                                    </button>
                                    <button
                                      onClick={() => archiveSubtask(task.id, subtask.id, !subtask.is_archived)}
                                      className={`p-1 ${subtask.is_archived ? 'text-green-600 hover:text-green-800' : 'text-orange-600 hover:text-orange-800'}`}
                                      title={subtask.is_archived ? "Unarchive subtask" : "Archive subtask"}
                                      disabled={loading}
                                    >
                                      {subtask.is_archived ? <ArchiveRestore className="w-3 h-3" /> : <Archive className="w-3 h-3" />}
                                    </button>
                                  </div>
                                </div>

                                {subtask.description && (
                                  <p className="text-gray-600 text-xs mb-2">{subtask.description}</p>
                                )}

                                <div className="space-y-1">
                                  <div className="flex justify-between items-center">
                                    <div className="flex space-x-2">
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(subtask.status)}`}>
                                        {subtask.status?.replace('_', ' ').toUpperCase()}
                                      </span>
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(subtask.priority)}`}>
                                        {getPriorityLabel(subtask.priority)}
                                      </span>
                                      {subtask.is_archived && (
                                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                                          ARCHIVED
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {subtask.due_date && (
                                    <div className="flex items-center text-xs text-gray-600">
                                      <Calendar className="w-3 h-3 mr-1" />
                                      {new Date(subtask.due_date).toLocaleDateString()}
                                    </div>
                                  )}

                                  {subtask.assignee_ids && subtask.assignee_ids.length > 0 && (
                                    <div className="flex items-center text-xs text-gray-600">
                                      <User className="w-3 h-3 mr-1" />
                                      <div className="flex flex-wrap gap-1">
                                        {subtask.assignee_ids.map(assigneeId => {
                                          const user = users.find(u => u.id === assigneeId);
                                          return (
                                            <span key={assigneeId} className="bg-blue-100 text-blue-800 px-1 py-0.5 rounded-full text-xs">
                                              {user?.username || user?.email?.split('@')[0] || 'Unknown'}
                                            </span>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </>
                            )}
                              </div>
                            ))}
                          </div>
                        </>
                      )}

                      {/* Add New Subtasks Section (only in edit mode) */}
                      {editingTask && editingTask.id === task.id && (
                        <div className="mt-4">
                          {/* New Subtasks Display */}
                          {editingNewSubtasks.length > 0 && (
                            <div className="mb-4">
                              <div className="text-sm font-medium text-gray-700 mb-2">
                                New Subtasks ({editingNewSubtasks.length})
                              </div>
                              <div className="space-y-2">
                                {editingNewSubtasks.map((newSubtask, index) => (
                                  <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                                    <div className="flex justify-between items-start">
                                      <div className="flex-1">
                                        <h4 className="text-sm font-medium text-gray-900">{newSubtask.title}</h4>
                                        {newSubtask.description && (
                                          <p className="text-xs text-gray-600 mt-1">{newSubtask.description}</p>
                                        )}
                                        <div className="flex space-x-2 mt-2">
                                          <span className={`px-1 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(newSubtask.priority)}`}>
                                            {getPriorityLabel(newSubtask.priority)}
                                          </span>
                                          {newSubtask.due_date && (
                                            <span className="text-xs text-gray-600">
                                              Due: {new Date(newSubtask.due_date).toLocaleDateString()}
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                      <button
                                        onClick={() => removeNewSubtaskInEdit(index)}
                                        className="text-red-600 hover:text-red-800 p-1"
                                        title="Remove subtask"
                                      >
                                        <X className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Add Subtask Button */}
                          {!showAddSubtaskInEdit && (
                            <button
                              onClick={() => setShowAddSubtaskInEdit(true)}
                              className="w-full p-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center"
                            >
                              <Plus className="w-4 h-4 mr-2" />
                              Add New Subtask
                            </button>
                          )}

                          {/* Add Subtask Form */}
                          {showAddSubtaskInEdit && (
                            <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                              <div className="space-y-3">
                                <input
                                  type="text"
                                  placeholder="Subtask title"
                                  value={newSubtask.title}
                                  onChange={(e) => setNewSubtask({...newSubtask, title: e.target.value})}
                                  className="w-full p-2 border border-gray-300 rounded text-sm"
                                />
                                <textarea
                                  placeholder="Subtask description"
                                  value={newSubtask.description}
                                  onChange={(e) => setNewSubtask({...newSubtask, description: e.target.value})}
                                  className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
                                  rows={2}
                                />
                                <div className="grid grid-cols-2 gap-2">
                                 <input
                                  type="number"
                                  min="1"
                                  max="10"
                                  value={newSubtask.priority ?? 5}
                                  onChange={(e) => setNewSubtask({...newSubtask, priority: Number(e.target.value)})}
                                  className="p-2 border border-gray-300 rounded text-sm"
                                />
                                  <input
                                    type="date"
                                    value={newSubtask.due_date}
                                    onChange={(e) => setNewSubtask({...newSubtask, due_date: e.target.value})}
                                    className="p-2 border border-gray-300 rounded text-sm"
                                  />
                                </div>
                                <div className="flex space-x-2">
                                  <button
                                    onClick={addNewSubtaskInEdit}
                                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 flex items-center"
                                  >
                                    <Plus className="w-3 h-3 mr-1" />
                                    Add
                                  </button>
                                  <button
                                    onClick={() => {
                                      setShowAddSubtaskInEdit(false);
                                      setNewSubtask({ title: '', description: '', status: 'TO_DO', priority: 5, due_date: '', comments: '' });
                                    }}
                                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                                  >
                                    <X className="w-3 h-3 mr-1" />
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {!loading && tasks.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <Plus className="w-16 h-16 mx-auto mb-4 opacity-50" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
          <p className="text-gray-600 mb-4">Get started by creating your first task.</p>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Create Task
          </button>
        </div>
      )}
    </div>
    </div>
  );
};

export default TaskManager;
