import React, { useState, useEffect } from 'react';
import { ArchiveRestore, Calendar, User, AlertCircle, X, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import LogoutButton from '../../components/auth/logoutbtn';
import { apiFetch } from "../../utils/api";

const ArchivedTasksView = () => {
  const [archivedSubtasks, setArchivedSubtasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Fetch archived subtasks
  const fetchArchivedTasks = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("tasks/readArchivedTasks");
      setArchivedSubtasks(data.archived_subtasks);
    } catch (err: any) {
      setError(`Failed to fetch archived tasks: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Unarchive a subtask
  const unarchiveSubtask = async (subtaskId: string, mainTaskId: string) => {

    setLoading(true);
    setError("");
    try {
      const payload = {
        main_task_id: mainTaskId,
        main_task: {},
        subtasks: {
          [subtaskId]: {
            is_archived: false
          }
        }
      };

      await apiFetch("tasks/updateTask", {
        method: "PUT",
        body: JSON.stringify(payload),
      });

      await fetchArchivedTasks(); // Refresh the list
    } catch (err: any) {
      setError(`Failed to unarchive subtask: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Load archived tasks on component mount
  useEffect(() => {
    document.title = "Archived Tasks";
    fetchArchivedTasks();
  }, []);

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'HIGH': return 'text-red-600 bg-red-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
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
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/taskmanager')}
              className="text-blue-600 hover:text-blue-800 flex items-center"
              title="Back to Task Manager"
            >
              <ArrowLeft className="w-5 h-5 mr-1" />
              Back
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Archived Tasks</h1>
          </div>
          <LogoutButton />
        </div>
        <p className="text-gray-600">View and manage archived subtasks</p>
      </div>

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

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading archived tasks...</p>
        </div>
      )}

      {/* Archived Subtasks */}
      <div className="space-y-6">
        {archivedSubtasks.map((item, index) => (
          <div key={`${item.subtask?.id}-${index}`} className="bg-gray-50 border border-gray-200 rounded-lg p-6 shadow-sm">
            {/* Main Task Info */}
            <div className="mb-4 p-4 bg-white rounded-lg border-l-4 border-blue-500">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Main Task: {item.main_task?.title || 'Unknown Task'}
              </h3>
              {item.main_task?.description && (
                <p className="text-gray-600 text-sm">{item.main_task.description}</p>
              )}
            </div>

            {/* Archived Subtask */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="text-md font-semibold text-gray-800 flex-1">
                  Subtask: {item.subtask?.title || 'Unknown Subtask'}
                </h4>
                <button
                  onClick={() => unarchiveSubtask(item.subtask?.id, item.main_task?.id)}
                  className="text-green-600 hover:text-green-800 p-1"
                  title="Unarchive subtask"
                  disabled={loading}
                >
                  <ArchiveRestore className="w-4 h-4" />
                </button>
              </div>

              {item.subtask?.description && (
                <p className="text-gray-600 text-sm mb-3">{item.subtask.description}</p>
              )}

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="flex space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.subtask?.status)}`}>
                      {item.subtask?.status?.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-200">
                      ARCHIVED
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.subtask?.priority)}`}>
                    {item.subtask?.priority?.toUpperCase()}
                  </span>
                </div>

                {item.subtask?.due_date && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="w-4 h-4 mr-1" />
                    {new Date(item.subtask.due_date).toLocaleDateString()}
                  </div>
                )}

                {item.subtask?.assignee_ids && item.subtask.assignee_ids.length > 0 && (
                  <div className="flex items-center text-sm text-gray-600">
                    <User className="w-4 h-4 mr-1" />
                    {item.subtask.assignee_ids.length} assignee(s)
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {!loading && archivedSubtasks.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <ArchiveRestore className="w-16 h-16 mx-auto mb-4 opacity-50" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No archived tasks found</h3>
          <p className="text-gray-600 mb-4">You don't have any archived subtasks yet.</p>
          <button
            onClick={() => navigate('/taskmanager')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Go to Task Manager
          </button>
        </div>
      )}
    </div>
  );
};

export default ArchivedTasksView;
