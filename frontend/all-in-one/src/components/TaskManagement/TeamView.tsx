import { useState, useEffect, useCallback } from 'react';
import { Calendar, User, Filter, AlertCircle, CheckCircle, Clock, XCircle, Users } from 'lucide-react';
import LogoutButton from '../../components/auth/logoutbtn';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';
import type { Task, User as UserType, TaskStatus, TaskPriority} from '../../types/Task';

interface Team {
  id: string;
  name: string;
  department?: string;
  member_count?: number;
}

interface TaskWithAssignee extends Task {
  assignee_names?: string[];
  isSubtask?: boolean;
  parent_task_title?: string;
}

const TeamView = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [tasks, setTasks] = useState<TaskWithAssignee[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<TaskWithAssignee[]>([]);
  const [teamMembers, setTeamMembers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

interface UserInfo {
  role: string;
  department: string;
  id: string;
  teams: string[];
}

const [userInfo, setUserInfo] = useState<UserInfo | null>(null);

  // Filters
  const [selectedMember, setSelectedMember] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('due_date');

useEffect(() => {
  const user = getUserFromToken();
  if (user) {
    setUserInfo({
      role: user.role,
      department: user.department,
      id: user.id,
      teams: user.teams,
    });
  }
}, []);


  // Fetch user's teams
  const fetchTeams = useCallback(async () => {
    try {
      const data = await apiFetch("team/my-teams");
      setTeams(data.teams || []);
    } catch (err: unknown) {
      console.error(`Failed to fetch teams: ${err instanceof Error ? err.message : String(err)}`);
      setError(`Failed to fetch teams: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, []);

  // Fetch team members
  const fetchTeamMembers = useCallback(async () => {
    try {
      const data = await apiFetch("auth/users");
      setTeamMembers(data.users || []);
    } catch (err: unknown) {
      console.error(`Failed to fetch team members: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, []);

  // Fetch all team tasks
  const fetchTeamTasks = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("team/team-tasks");
      
      // Flatten tasks and subtasks with assignee info
      const allTasks: TaskWithAssignee[] = [];
      
      data.tasks.forEach((task: Task) => {
        // Get assignee names
        const assigneeNames = task.assignee_ids?.map(id => {
          const member = teamMembers.find(m => m.id === id);
          return member?.username || member?.email?.split('@')[0] || 'Unknown';
        }) || [];

        // Add main task
        allTasks.push({
          ...task,
          assignee_names: assigneeNames,
          isSubtask: false
        });
        
        // Add subtasks if they exist
        if (task.subtasks && task.subtasks.length > 0) {
          task.subtasks.forEach(subtask => {
            const subtaskAssigneeNames = subtask.assignee_ids?.map(id => {
              const member = teamMembers.find(m => m.id === id);
              return member?.username || member?.email?.split('@')[0] || 'Unknown';
            }) || [];

            allTasks.push({
              ...subtask,
              owner_user_id: task.owner_user_id,
              assignee_names: subtaskAssigneeNames,
              isSubtask: true,
              parent_task_title: task.title
            });
          });
        }
      });
      
      setTasks(allTasks);
      setFilteredTasks(allTasks);
    } catch (err: unknown) {
      setError(`Failed to fetch team tasks: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  }, [teamMembers]);

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...tasks];

    // Filter by team member
    if (selectedMember !== 'all') {
      filtered = filtered.filter(task => 
        task.assignee_ids && task.assignee_ids.includes(selectedMember)
      );
    }

    // Filter by status
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(task => task.status === selectedStatus);
    }

    // Sort tasks
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'due_date':
          if (!a.due_date) return 1;
          if (!b.due_date) return -1;
          return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
        case 'priority':
          const priorityOrder: Record<TaskPriority, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
          return priorityOrder[a.priority] - priorityOrder[b.priority];
        case 'status':
          const statusOrder: Record<TaskStatus, number> = { BLOCKED: 0, IN_PROGRESS: 1, TO_DO: 2, COMPLETED: 3 };
          return statusOrder[a.status] - statusOrder[b.status];
        default:
          return 0;
      }
    });

    setFilteredTasks(filtered);
  }, [tasks, selectedMember, selectedStatus, sortBy]);

  // Load data on mount
  useEffect(() => {
    document.title = "Teams";
    fetchTeams();
    fetchTeamMembers();
  }, [fetchTeams, fetchTeamMembers]);

  // Fetch tasks after team members are loaded
  useEffect(() => {
    if (teamMembers.length > 0) {
      fetchTeamTasks();
    }
  }, [teamMembers.length, fetchTeamTasks]);

  // Calculate task statistics by status
  const getTaskStats = () => {
    const total = filteredTasks.length;
    const completed = filteredTasks.filter(t => t.status === 'COMPLETED').length;
    const inProgress = filteredTasks.filter(t => t.status === 'IN_PROGRESS').length;
    const toDo = filteredTasks.filter(t => t.status === 'TO_DO').length;
    const blocked = filteredTasks.filter(t => t.status === 'BLOCKED').length;
    const overdue = filteredTasks.filter(t => {
      if (!t.due_date || t.status === 'COMPLETED') return false;
      return new Date(t.due_date) < new Date();
    }).length;
    
    return { total, completed, inProgress, toDo, blocked, overdue };
  };

  const stats = getTaskStats();

  // Get status icon
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4" />;
      case 'IN_PROGRESS': return <Clock className="w-4 h-4" />;
      case 'BLOCKED': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  // Get priority color
  const getPriorityColor = (priority: TaskPriority): string => {
    switch (priority) {
      case 'HIGH': return 'bg-red-100 text-red-700';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-700';
      case 'LOW': return 'bg-green-100 text-green-700';
    }
  };

  // Get status color
  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-100 text-green-700';
      case 'IN_PROGRESS': return 'bg-blue-100 text-blue-700';
      case 'TO_DO': return 'bg-gray-100 text-gray-700';
      case 'BLOCKED': return 'bg-red-100 text-red-700';
    }
  };

  // Check if task is overdue
  const isOverdue = (dueDate: string | undefined, status: TaskStatus): boolean => {
    if (!dueDate || status === 'COMPLETED') return false;
    return new Date(dueDate) < new Date();
  };

  // Get progress percentage
  const getProgressPercentage = () => {
    if (stats.total === 0) return 0;
    return Math.round((stats.completed / stats.total) * 100);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Teams</h1>
          <LogoutButton />
        </div>
        <p className="text-gray-600">Your Projects Tracker</p>

        {userInfo && (
          <div className="mt-4 p-4 bg-white border rounded-lg shadow-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">
                <strong>Department:</strong> {userInfo.department || 'N/A'}
              </span>
              <span className="text-gray-700">
                <strong>Role:</strong> <span className="uppercase text-sm font-semibold">{userInfo.role}</span>
              </span>
            </div>
          </div>
        )}
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
            ×
          </button>
        </div>
      )}

      {/* Teams List */}
      <div className="mb-6 bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center mb-3">
          <Users className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Your Teams</h2>
        </div>
        {teams.length === 0 ? (
          <p className="text-gray-500 text-sm">No teams found</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {teams.map(team => (
              <div key={team.id} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-gray-900">{team.name}</h3>
                {team.department && (
                  <p className="text-sm text-gray-600">{team.department}</p>
                )}
                {team.member_count && (
                  <p className="text-xs text-gray-500 mt-1">{team.member_count} members</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-sm text-gray-600">Total Tasks</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
          <div className="text-sm text-gray-600">In Progress</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-gray-600">{stats.toDo}</div>
          <div className="text-sm text-gray-600">To Do</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-red-600">{stats.blocked}</div>
          <div className="text-sm text-gray-600">Blocked</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-orange-600">{stats.overdue}</div>
          <div className="text-sm text-gray-600">Overdue</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-semibold text-gray-900">{getProgressPercentage()}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-green-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center mb-3">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filters & Sorting</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Team Member</label>
            <select
              value={selectedMember}
              onChange={(e) => setSelectedMember(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Members</option>
              {teamMembers.map(member => (
                <option key={member.id} value={member.id}>
                  {member.username || member.email?.split('@')[0]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="TO_DO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="BLOCKED">Blocked</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="due_date">Due Date</option>
              <option value="priority">Priority</option>
              <option value="status">Status</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      )}

      {/* Tasks List */}
      {!loading && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">
              Team Tasks ({filteredTasks.length})
            </h2>
          </div>
          <div className="divide-y">
            {filteredTasks.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No tasks found matching the selected filters.
              </div>
            ) : (
              filteredTasks.map((task) => (
                <div key={task.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {task.isSubtask && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded mb-2 inline-block">
                          Subtask of: {task.parent_task_title}
                        </span>
                      )}
                      <h3 className="text-base font-semibold text-gray-900 mb-1">
                        {task.title}
                      </h3>
                      {task.description && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">{task.description}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                          {getStatusIcon(task.status)}
                          <span className="ml-1">{task.status.replace('_', ' ')}</span>
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                          {task.priority}
                        </span>
                        {task.due_date && (
                          <span className={`flex items-center text-xs ${isOverdue(task.due_date, task.status) ? 'text-red-600 font-semibold' : 'text-gray-600'}`}>
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(task.due_date).toLocaleDateString()}
                            {isOverdue(task.due_date, task.status) && ' (Overdue)'}
                          </span>
                        )}
                        {task.assignee_names && task.assignee_names.length > 0 && (
                          <span className="flex items-center text-xs text-gray-600">
                            <User className="w-3 h-3 mr-1" />
                            {task.assignee_names.join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamView;