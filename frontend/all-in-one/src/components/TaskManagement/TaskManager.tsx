import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Save, X, Calendar, User, AlertCircle, Shield } from 'lucide-react'; 
import LogoutButton from '../../components/auth/logoutbtn';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';


const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [editingTask, setEditingTask] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    status: 'pending',
    priority: 'medium',
    due_date: '',
    assigned_to: ''
  });
  const [userInfo, setUserInfo] = useState<{ email: string; role: string } | null>(null);

  useEffect(() => {
    const user = getUserFromToken();
    if (user) setUserInfo(user);
  }, []);



// fetch tasks
const fetchTasks = async () => {
  setLoading(true);
  setError("");
  try {
    const data = await apiFetch("tasks/readTasks");  // <-- use apiFetch
    setTasks(data.tasks);
  } catch (err: any) {
    setError(`Failed to fetch tasks: ${err.message}`);
  } finally {
    setLoading(false);
  }
};

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


const createTask = async (taskData: any) => {
  setLoading(true);
  setError("");
  try {
    const userId = getUserIdFromToken();

    const payload = {
      main_task: {
        title: taskData.title,
        description: taskData.description,
        due_date: taskData.due_date,
        priority: taskData.priority.toUpperCase(),
        assignee_ids: userId ? [userId] : []   // auto-assign logged-in user
      },
      subtasks: {}
    };

    await apiFetch("tasks/createTask", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    await fetchTasks();
    setShowAddForm(false);
    setNewTask({ title: "", description: "", status: "pending", priority: "medium", due_date: "", assigned_to: "" });
  } catch (err: any) {
    setError(`Failed to create task: ${err.message}`);
  } finally {
    setLoading(false);
  }
};


const updateTask = async (taskId: string, taskData: any) => {
  setLoading(true);
  setError("");
  try {
    const userId = getUserIdFromToken();

    const payload = {
      main_task_id: taskId,
      main_task: {
        title: taskData.title,
        description: taskData.description,
        due_date: taskData.due_date,
        priority: taskData.priority.toUpperCase(),
        assignee_ids: userId ? [userId] : []
      },
      subtasks: {}
    };

    await apiFetch("tasks/updateTask", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

    await fetchTasks();
    setEditingTask(null);
  } catch (err: any) {
    setError(`Failed to update task: ${err.message}`);
  } finally {
    setLoading(false);
  }
};


// delete task
const deleteTask = async (taskId: string) => {
  if (!window.confirm("Are you sure you want to delete this task?")) return;
  setLoading(true);
  setError("");
  try {
    await apiFetch(`/tasks/deleteTask/${taskId}`, { method: "DELETE" }); // <-- use apiFetch
    setTasks(tasks.filter((task) => task.id !== taskId));
  } catch (err: any) {
    setError(`Failed to delete task: ${err.message}`);
  } finally {
    setLoading(false);
  }
};

  // Load tasks on component mount
  useEffect(() => {
    document.title = "Your task manager";
    fetchTasks();
  }, []);

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
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'pending': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 className="text-3xl font-bold text-gray-900">Smart Task Manager</h1>
          <LogoutButton />
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

      {/* Add Task Button */}
      <div className="mb-6">
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
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask({...newTask, priority: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask({...newTask, due_date: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                <input
                  type="text"
                  value={newTask.assigned_to}
                  onChange={(e) => setNewTask({...newTask, assigned_to: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter assignee name"
                />
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
                onClick={() => setShowAddForm(false)}
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
                  onChange={(e) => setEditingTask({...editingTask, due_date: e.target.value})}
                  className="w-full p-1 border border-gray-300 rounded text-xs"
                />
                <input
                  type="text"
                  value={editingTask.assigned_to}
                  onChange={(e) => setEditingTask({...editingTask, assigned_to: e.target.value})}
                  className="w-full p-1 border border-gray-300 rounded text-xs"
                  placeholder="Assigned to"
                />
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
                      onClick={() => setEditingTask(task)}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Edit task"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteTask(task.id)}
                      className="text-red-600 hover:text-red-800 p-1"
                      title="Delete task"
                      disabled={loading}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {task.description && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">{task.description}</p>
                )}
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                      {task.status?.replace('_', ' ').toUpperCase()}
                    </span>
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