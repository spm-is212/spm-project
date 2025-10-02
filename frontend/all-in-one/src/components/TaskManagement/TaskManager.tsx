import { useState, useEffect, useCallback } from 'react';
import { Plus, Edit, Save, X, Calendar, User, AlertCircle, Archive, ArchiveRestore, Shield } from 'lucide-react';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';
import type { Task, NewTask, NewSubtask, User as UserType, TaskPriority } from '../../types/Task';


const TaskManager = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editingAssignees, setEditingAssignees] = useState<string[]>([]);
  const [showAddForm, setShowAddForm] = useState<boolean>(false);
  const [users, setUsers] = useState<UserType[]>([]);
  const [selectedAssignees, setSelectedAssignees] = useState<string[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [newTask, setNewTask] = useState<NewTask>({
    title: '',
    description: '',
    status: 'TO_DO',
    priority: 'MEDIUM',
    due_date: '',
    comments: ''
  });
  const [subtasks, setSubtasks] = useState<NewSubtask[]>([]);
  const [showSubtaskForm, setShowSubtaskForm] = useState<boolean>(false);
  const [newSubtask, setNewSubtask] = useState<NewSubtask>({
    title: '',
    description: '',
    priority: 'MEDIUM',
    due_date: '',
    comments: ''
  });
  const [userInfo, setUserInfo] = useState<{ email: string; role: string; department?: string } | null>(null);

  useEffect(() => {
    const user = getUserFromToken();
    if (user) setUserInfo(user);
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

    // Attach subtasks to their main tasks
    const organizedTasks = mainTasks.map(mainTask => ({
      ...mainTask,
      subtasks: subtasksByParent[mainTask.id] || []
    }));

    setTasks(organizedTasks);
  } catch (err: unknown) {
    setError(`Failed to fetch tasks: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    setLoading(false);
  }
}, []);

function getUserIdFromToken(): string | null {
  const token = localStorage.getItem("access_token");
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
  try {
    const userId = getUserIdFromToken();

    // Prepare subtasks for backend format
    const formattedSubtasks = subtasks.map(subtask => ({
      title: subtask.title,
      description: subtask.description,
      due_date: subtask.due_date,
      priority: subtask.priority,
      assignee_ids: userId ? [userId] : []
    }));

    const mainTaskAssignees = selectedAssignees.length > 0 ? selectedAssignees : (userId ? [userId] : []);

    const payload = {
      main_task: {
        title: taskData.title,
        description: taskData.description,
        due_date: taskData.due_date,
        priority: taskData.priority,
        assignee_ids: mainTaskAssignees
      },
      subtasks: formattedSubtasks
    };

    await apiFetch("tasks/createTask", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    await fetchTasks();
    setShowAddForm(false);
    setNewTask({ title: "", description: "", status: "TO_DO", priority: "MEDIUM", due_date: "", comments: "" });
    setSubtasks([]);
    setShowSubtaskForm(false);

    // Reset assignees to current user only
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
  try {
    const userId = getUserIdFromToken();

    // Use selectedAssignees for updates, fallback to current user if none selected
    const assigneeIds = selectedAssignees.length > 0 ? selectedAssignees : (userId ? [userId] : []);

    const payload = {
      main_task_id: taskId,
      main_task: {
        title: taskData.title,
        description: taskData.description,
        due_date: taskData.due_date,
        priority: taskData.priority,
        assignee_ids: assigneeIds,
        ...(taskData.is_archived !== undefined && { is_archived: taskData.is_archived })
      },
      subtasks: {}
    };

    await apiFetch("tasks/updateTask", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

    await fetchTasks();
    setEditingTask(null);
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

    await apiFetch("tasks/updateTask", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

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
  try {
    const userId = getUserIdFromToken();
    const assigneeIds = selectedAssignees.length > 0 ? selectedAssignees : (userId ? [userId] : []);
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

    await apiFetch("tasks/updateTask", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

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

    await apiFetch("tasks/updateTask", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

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
  }, [fetchTasks, fetchUsers]);

  // Subtask management functions
  const addSubtask = () => {
    if (!newSubtask.title.trim()) {
      setError('Subtask title is required');
      return;
    }
    setSubtasks([...subtasks, { ...newSubtask, id: Date.now().toString() }]);
    setNewSubtask({ title: '', description: '', priority: 'MEDIUM', due_date: '', comments: '' });
    setShowSubtaskForm(false);
  };

  const removeSubtask = (index: number) => {
    setSubtasks(subtasks.filter((_, i) => i !== index));
  };

  // Handle form submissions
  const handleCreateSubmit = () => {
    if (!newTask.title.trim()) {
      setError('Task title is required');
      return;
    }
    createTask(newTask);
  };

  const handleUpdateSubmit = () => {
    if (!editingTask.title.trim()) {
      setError('Task title is required');
      return;
    }
    updateTask(editingTask.id, editingTask);
  };

  // Get priority color
  const getPriorityColor = (priority: TaskPriority | undefined): string => {
    switch (priority?.toUpperCase()) {
      case 'HIGH': return 'text-red-600 bg-red-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
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

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 className="text-3xl font-bold text-gray-900">Smart Task Manager</h1>
        </div>
        <p className="text-gray-600">Manage your tasks efficiently with full CRUD operations</p>

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
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask({...newTask, priority: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => {
                    const selectedDate = e.target.value;
                    const today = new Date().toISOString().split('T')[0];
                    if (selectedDate && selectedDate < today) {
                      setError('Due date cannot be in the past');
                      return;
                    }
                    setNewTask({...newTask, due_date: selectedDate});
                  }}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
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
                            {!isCurrentUser && (
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Comments</label>
              <textarea
                value={newTask.comments}
                onChange={(e) => setNewTask({...newTask, comments: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows="2"
                placeholder="Enter initial comments (optional)"
              />
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
                    <div key={index} className="bg-gray-50 p-3 rounded border flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{subtask.title}</div>
                        {subtask.description && <div className="text-xs text-gray-600 mt-1">{subtask.description}</div>}
                        <div className="flex space-x-2 mt-1">
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{subtask.priority}</span>
                          {subtask.due_date && <span className="text-xs text-gray-500">{subtask.due_date}</span>}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeSubtask(index)}
                        className="text-red-500 hover:text-red-700 ml-2"
                      >
                        <X className="w-4 h-4" />
                      </button>
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
                      <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                      <select
                        value={newSubtask.priority}
                        onChange={(e) => setNewSubtask({...newSubtask, priority: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="LOW">Low</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="HIGH">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                      <input
                        type="date"
                        value={newSubtask.due_date}
                        onChange={(e) => {
                          const selectedDate = e.target.value;
                          const today = new Date().toISOString().split('T')[0];
                          if (selectedDate && selectedDate < today) {
                            setError('Due date cannot be in the past');
                            return;
                          }
                          setNewSubtask({...newSubtask, due_date: selectedDate});
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
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Comments</label>
                    <textarea
                      value={newSubtask.comments}
                      onChange={(e) => setNewSubtask({...newSubtask, comments: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows="2"
                      placeholder="Enter initial comments (optional)"
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
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                  <select
                    value={editingTask.priority}
                    onChange={(e) => setEditingTask({...editingTask, priority: e.target.value})}
                    className="p-1 border border-gray-300 rounded text-xs"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <input
                  type="date"
                  value={editingTask.due_date}
                  onChange={(e) => {
                    const selectedDate = e.target.value;
                    const today = new Date().toISOString().split('T')[0];
                    if (selectedDate && selectedDate < today) {
                      setError('Due date cannot be in the past');
                      return;
                    }
                    setEditingTask({...editingTask, due_date: selectedDate});
                  }}
                  className="w-full p-1 border border-gray-300 rounded text-xs"
                />
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
                            {!isCurrentUser && (
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
                    onClick={handleUpdateSubmit}
                    disabled={loading}
                    className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50 flex items-center"
                  >
                    <Save className="w-3 h-3 mr-1" />
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingTask(null)}
                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Cancel
                  </button>
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
                      {task.priority?.toUpperCase()}
                    </span>
                  </div>

                  {task.due_date && (
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}

                  {task.assigned_to && (
                    <div className="flex items-center text-sm text-gray-600">
                      <User className="w-4 h-4 mr-1" />
                      {task.assigned_to}
                    </div>
                  )}

                  {/* Subtasks Display */}
                  {task.subtasks && task.subtasks.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
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
                                  <select
                                    value={editingTask.priority}
                                    onChange={(e) => setEditingTask({...editingTask, priority: e.target.value})}
                                    className="w-full p-1 border border-gray-300 rounded text-xs"
                                  >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                  </select>
                                  <input
                                    type="date"
                                    value={editingTask.due_date}
                                    onChange={(e) => {
                                      const selectedDate = e.target.value;
                                      const today = new Date().toISOString().split('T')[0];
                                      if (selectedDate && selectedDate < today) {
                                        setError('Due date cannot be in the past');
                                        return;
                                      }
                                      setEditingTask({...editingTask, due_date: selectedDate});
                                    }}
                                    className="w-full p-1 border border-gray-300 rounded text-xs"
                                  />
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
                                    onClick={() => setEditingTask(null)}
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
                                        {subtask.priority?.toUpperCase()}
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
                                      {subtask.assignee_ids.length} assignee(s)
                                    </div>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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
