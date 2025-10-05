import { useState, useEffect, useCallback } from 'react';
import { Calendar, User, Filter, AlertCircle, CheckCircle, Clock, XCircle, Folder, Users, Building, ChevronDown, ChevronRight, ArrowUp, ArrowDown } from 'lucide-react';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';
import { API_ENDPOINTS } from '../../config/api';
import type { Task, User as UserType } from '../../types/Task';

interface Project {
  id: string;
  name: string;
  description?: string;
  collaborator_ids: string[];
  team_id?: string; // Deprecated, for backward compatibility
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

interface TaskWithProject extends Omit<Task, 'owner_user_id' | 'is_archived'> {
  project_name?: string;
  project_id: string;
  isSubtask?: boolean;
  parent_id?: string | null;
  parent_task_title?: string;
  created_at?: string;
  updated_at?: string;
  owner_user_id?: string;
  is_archived?: boolean;
}

interface Team {
  id: string;
  name: string;
  department_id?: string;
  member_count?: number;
}

const TeamView = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<TaskWithProject[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<TaskWithProject[]>([]);
  const [teamMembers, setTeamMembers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [userInfo, setUserInfo] = useState<{ email: string; role: string; department?: string; department_id?: string; user_id?: string } | null>(null);

  // Filters
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  useEffect(() => {
    const user = getUserFromToken();
    console.log('[TeamView] User from token:', user);
    if (user) {
      const userInfoData = {
        email: '', // Email not available from token
        role: user.role || '',
        department: user.department || '',
        department_id: user.department || '',
        user_id: user.id || ''
      };
      console.log('[TeamView] Setting userInfo:', userInfoData);
      setUserInfo(userInfoData);
    } else {
      console.log('[TeamView] No user from token!');
    }
  }, []);

  // Fetch user's teams
  const fetchTeams = useCallback(async () => {
    try {
      const data = await apiFetch(API_ENDPOINTS.TEAMS.MY_TEAMS);

      // Backend should return team objects with valid UUIDs
      const teamsData = data.teams || [];

      // Validate that we have proper team objects with UUIDs
      const validTeams = teamsData.filter((team: Team) =>
        team && typeof team === 'object' && team.id && team.name
      );

      setTeams(validTeams);
      if (validTeams.length > 0 && !selectedTeam) {
        setSelectedTeam(validTeams[0].id || '');
      }
    } catch (err: unknown) {
      console.error(`Failed to fetch teams: ${err instanceof Error ? err.message : String(err)}`);
      setError('Failed to load teams');
    }
  }, [selectedTeam]);

  // Fetch all projects accessible to the user
  const fetchProjects = useCallback(async () => {
    try {
      // Fetch all projects the user has access to
      const data = await apiFetch(API_ENDPOINTS.PROJECTS.LIST);
      const allProjects = data || [];

      console.log('[TeamView] Fetched projects:', allProjects.length, allProjects);
      setProjects(allProjects);
    } catch (err: unknown) {
      console.error(`Failed to fetch projects: ${err instanceof Error ? err.message : String(err)}`);
      setProjects([]);
    }
  }, []);

  // Fetch tasks from backend - returns tasks user has access to (as assignee or via role)
  const fetchTeamTasks = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Use filter endpoint if date range is set, otherwise use regular read
      let endpoint: string = API_ENDPOINTS.TASKS.READ;
      const params = new URLSearchParams();

      if (startDate || endDate) {
        endpoint = API_ENDPOINTS.TASKS.FILTER_BY_DUE_DATE;
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
      }

      const url = params.toString() ? `${endpoint}?${params.toString()}` : endpoint;
      const data = await apiFetch(url);
      const tasksData = data.tasks || [];

      // Transform tasks to include parent/subtask information
      const transformedTasks: TaskWithProject[] = tasksData.map((task: TaskWithProject) => ({
        ...task,
        isSubtask: task.parent_id !== null && task.parent_id !== undefined,
        parent_id: task.parent_id,
        project_id: task.project_id,
        project_name: task.project_name,
      }));

      // Tasks are already filtered by backend access control:
      // - Directors/Managing Directors: see all tasks in their scope
      // - Regular users: see tasks where they are assignees
      setTasks(transformedTasks);
      setFilteredTasks(transformedTasks);
    } catch (err: unknown) {
      setError(`Failed to fetch tasks: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  // Fetch team members
  const fetchTeamMembers = useCallback(async () => {
    try {
      const data = await apiFetch(API_ENDPOINTS.AUTH.USERS);
      setTeamMembers(data.users || []);
    } catch (err: unknown) {
      console.error(`Failed to fetch team members: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, []);

  // Apply sorting only (no filtering)
  useEffect(() => {
    let sorted = [...tasks];

    // Sort tasks (priority, status, title only - no due_date)
    const priorityOrder: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    sorted.sort((a, b) => {
      let result = 0;
      switch (sortBy) {
        case 'priority': {
          result = (priorityOrder[a.priority?.toUpperCase()] || 3) - (priorityOrder[b.priority?.toUpperCase()] || 3);
          break;
        }
        case 'status': {
          result = (a.status || '').localeCompare(b.status || '');
          break;
        }
        case 'title': {
          result = a.title.localeCompare(b.title);
          break;
        }
        default:
          return 0;
      }
      return sortOrder === 'asc' ? result : -result;
    });

    setFilteredTasks(sorted);
  }, [tasks, sortBy, sortOrder]);

  // Load data on mount
  useEffect(() => {
    document.title = "My Teams";
    fetchTeams();
    fetchTeamMembers();
    fetchTeamTasks();
    fetchProjects();
  }, [fetchTeams, fetchTeamMembers, fetchTeamTasks, fetchProjects]);

  // Get projects where current user is a collaborator or has tasks assigned
  const getUserCollaboratorProjects = () => {
    if (!userInfo?.user_id) {
      console.log('[TeamView] No user_id, returning empty projects');
      return [];
    }

    const userId = userInfo.user_id;
    const userRole = userInfo.role?.toLowerCase();

    console.log('[TeamView] getUserCollaboratorProjects - userId:', userId, 'role:', userRole, 'total projects:', projects.length);

    // Directors and Managing Directors see ALL projects (backend already filtered)
    if (userRole === 'director' || userRole === 'managing_director') {
      console.log('[TeamView] Director/MD - returning all projects:', projects.length);
      return projects;
    }

    // Method 1: Check if user is in collaborator_ids (primary method)
    const directCollaboratorProjects = projects.filter(p =>
      p.collaborator_ids && p.collaborator_ids.includes(userId)
    );
    console.log('[TeamView] Direct collaborator projects:', directCollaboratorProjects.length);

    // Method 2: Also include projects where user has tasks (fallback/additional)
    const userTaskProjectIds = new Set<string>();
    tasks.forEach(task => {
      // Check if user is owner or assignee
      const isUserTask = task.owner_user_id === userId ||
                        task.assignee_ids?.includes(userId);
      if (isUserTask && task.project_id) {
        userTaskProjectIds.add(task.project_id);
      }
    });
    console.log('[TeamView] Task-based project IDs:', userTaskProjectIds.size);

    // Combine both methods and remove duplicates
    const allCollaboratorProjectIds = new Set([
      ...directCollaboratorProjects.map(p => p.id),
      ...userTaskProjectIds
    ]);

    const result = projects.filter(p => allCollaboratorProjectIds.has(p.id));
    console.log('[TeamView] Final user projects:', result.length);
    return result;
  };

  // Calculate task statistics
  const getTaskStats = () => {
    const total = filteredTasks.length;
    const completed = filteredTasks.filter(t => t.status === 'COMPLETED').length;
    const inProgress = filteredTasks.filter(t => t.status === 'IN_PROGRESS').length;
    const pending = filteredTasks.filter(t => t.status === 'TO_DO').length;
    const blocked = filteredTasks.filter(t => t.status === 'BLOCKED').length;
    const overdue = filteredTasks.filter(t => {
      if (!t.due_date || t.status === 'COMPLETED') return false;
      const dueDate = new Date(t.due_date);
      dueDate.setHours(0, 0, 0, 0);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return dueDate < today;
    }).length;

    const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    return { total, completed, inProgress, pending, blocked, overdue, completionRate };
  };

  const stats = getTaskStats();

  // Get priority and status colors
  const getPriorityLabel = (priority: string | number | undefined): string => {
    if (typeof priority === 'number') {
      switch (priority) {
        case 1: return 'LOW';
        case 2: return 'MEDIUM';
        case 3: return 'HIGH';
        default: return 'UNKNOWN';
      }
    }
    return (priority || 'UNKNOWN').toString().toUpperCase();
  };

  const getPriorityColor = (priority: string | number | undefined): string => {
    const label = getPriorityLabel(priority);
    switch (label) {
      case 'HIGH': return 'text-red-600 bg-red-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (status: string | undefined): string => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED': return 'text-green-600 bg-green-100';
      case 'IN_PROGRESS': return 'text-blue-600 bg-blue-100';
      case 'TO_DO': return 'text-gray-600 bg-gray-100';
      case 'BLOCKED': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string | undefined) => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4" />;
      case 'IN_PROGRESS': return <Clock className="w-4 h-4" />;
      case 'BLOCKED': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const isOverdue = (dueDate: string | undefined, status: string | undefined): boolean => {
    if (!dueDate || status === 'COMPLETED') return false;
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return due < today;
  };

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const toggleProjectExpansion = (projectId: string) => {
    setExpandedProjects(prev => {
      const newSet = new Set(prev);
      if (newSet.has(projectId)) {
        newSet.delete(projectId);
      } else {
        newSet.add(projectId);
      }
      return newSet;
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">

        {userInfo && (
          <div className="mt-4 p-4 bg-white border rounded-lg shadow-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Building className="w-5 h-5 text-blue-600" />
                <span className="text-gray-700">
                  <strong>Department:</strong> {userInfo.department || 'N/A'}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Folder className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">
                  <strong>My Projects:</strong> {getUserCollaboratorProjects().length} {getUserCollaboratorProjects().length === 1 ? 'Project' : 'Projects'}
                </span>
              </div>
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

      {/* Teams List - Hidden for Staff */}
      {userInfo?.role?.toLowerCase() !== 'staff' && (
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
          <div className="flex items-center mb-4">
            <Users className="w-5 h-5 text-gray-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">My Teams</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {teams.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                {loading ? 'Loading projects...' : 'You are not assigned to any projects yet.'}
              </div>
            ) : (
              teams.map(team => (
                <div
                  key={team.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedTeam === team.id
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow'
                  }`}
                  onClick={() => setSelectedTeam(team.id)}
                >
                  <h3 className="font-semibold text-gray-900">{team.name}</h3>
                  {team.member_count !== undefined && (
                    <p className="text-sm text-gray-600 mt-2">{team.member_count} members</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {projects.filter(p => p.team_id === team.id).length} projects
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-1">
            <Folder className="w-5 h-5 text-gray-500" />
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-xs font-medium text-gray-600 uppercase tracking-wide">Total Tasks</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg shadow-sm border border-green-200">
          <div className="flex items-center justify-between mb-1">
            <CheckCircle className="w-5 h-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-700">{stats.completed}</div>
          <div className="text-xs font-medium text-green-700 uppercase tracking-wide">Completed</div>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg shadow-sm border border-blue-200">
          <div className="flex items-center justify-between mb-1">
            <Clock className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-blue-700">{stats.inProgress}</div>
          <div className="text-xs font-medium text-blue-700 uppercase tracking-wide">In Progress</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg shadow-sm border border-yellow-200">
          <div className="flex items-center justify-between mb-1">
            <Clock className="w-5 h-5 text-yellow-600" />
          </div>
          <div className="text-3xl font-bold text-yellow-700">{stats.pending}</div>
          <div className="text-xs font-medium text-yellow-700 uppercase tracking-wide">To Do</div>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg shadow-sm border border-orange-200">
          <div className="flex items-center justify-between mb-1">
            <XCircle className="w-5 h-5 text-orange-600" />
          </div>
          <div className="text-3xl font-bold text-orange-700">{stats.blocked}</div>
          <div className="text-xs font-medium text-orange-700 uppercase tracking-wide">Blocked</div>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg shadow-sm border border-red-200">
          <div className="flex items-center justify-between mb-1">
            <AlertCircle className="w-5 h-5 text-red-600" />
          </div>
          <div className="text-3xl font-bold text-red-700">{stats.overdue}</div>
          <div className="text-xs font-medium text-red-700 uppercase tracking-wide">Overdue</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white p-4 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-semibold text-gray-900">{stats.completionRate}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${stats.completionRate}%` }}
          ></div>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          {stats.completed} of {stats.total} tasks completed
        </div>
      </div>


      {/* Filter and Sort Combined */}
      <div className="bg-white p-4 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filter & Sort Tasks</h2>
        </div>

        <div className="flex flex-wrap gap-4 items-end">
          {/* Date Filter Section */}
          <div className="flex-1 min-w-[300px]">
            <label className="block text-xs text-gray-600 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
          <div className="flex-1 min-w-[300px]">
            <label className="block text-xs text-gray-600 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
          <button
            onClick={() => {
              setStartDate('');
              setEndDate('');
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700 whitespace-nowrap"
          >
            Clear
          </button>

          {/* Sort Section */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-600 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="priority">Priority</option>
              <option value="status">Status</option>
              <option value="title">Title</option>
            </select>
          </div>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center"
            title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
          >
            {sortOrder === 'asc' ? (
              <ArrowUp className="w-5 h-5 text-blue-600" />
            ) : (
              <ArrowDown className="w-5 h-5 text-blue-600" />
            )}
          </button>
        </div>

        {(startDate || endDate) && (
          <div className="mt-2 text-xs text-blue-600">
            Filtering tasks {startDate && `from ${startDate}`} {startDate && endDate && 'to'} {endDate && endDate}
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      )}

      {/* Cross-Functional Project → Task → Subtask View */}
      {!loading && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">My Projects</h2>

          {getUserCollaboratorProjects().length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
              <p className="text-lg font-semibold mb-2">No Projects Found</p>
              <p className="text-sm">You are not currently a collaborator on any projects.</p>
            </div>
          ) : (
            // Show only projects where current user is a collaborator
            getUserCollaboratorProjects().map((project) => {
              const projectTasks = filteredTasks.filter(t => t.project_id === project.id && !t.isSubtask);
              const isProjectExpanded = expandedProjects.has(project.id);
              const completedTasks = projectTasks.filter(t => t.status === 'COMPLETED').length;

              return (
                
                <div key={project.id} className="bg-white rounded-lg shadow-sm border">
                  
                  <div
                    className="p-4 bg-gradient-to-r from-green-50 to-green-100 border-b cursor-pointer hover:from-green-100 hover:to-green-150 transition-colors"
                    onClick={() => toggleProjectExpansion(project.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1">
                        {isProjectExpanded ? (
                          <ChevronDown className="w-5 h-5 text-green-600" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-green-600" />
                        )}
                        <Folder className="w-5 h-5 text-green-600" />
                        <div className="flex-1">
                          <h2 className="text-lg font-bold text-gray-900">{project.name}</h2>
                          {project.description && (
                            <p className="text-sm text-gray-600 mt-1">{project.description}</p>
                          )}
                          {project.collaborator_ids && project.collaborator_ids.length > 0 && (
                            <p className="text-xs text-green-700 mt-1">
                              Cross-functional • {project.collaborator_ids.length} {project.collaborator_ids.length === 1 ? 'collaborator' : 'collaborators'}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                          {completedTasks}/{projectTasks.length} Tasks
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Project Tasks */}
                  {isProjectExpanded && (
                    <div className="bg-white divide-y">
                      {projectTasks.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                          No tasks in this project yet.
                        </div>
                      ) : (
                        projectTasks.map((task) => {
                          const subtasks = filteredTasks.filter(t => t.isSubtask && t.parent_id === task.id);
                          const isTaskExpanded = expandedTasks.has(task.id);

                          return (
                            <div key={task.id}>
                              {/* Task */}
                              <div className="p-4 pl-12 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2 mb-2">
                                      {subtasks.length > 0 && (
                                        <button
                                          onClick={() => toggleTaskExpansion(task.id)}
                                          className="flex items-center text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded font-medium hover:bg-gray-200 transition-colors"
                                        >
                                          {isTaskExpanded ? (
                                            <ChevronDown className="w-3 h-3 mr-1" />
                                          ) : (
                                            <ChevronRight className="w-3 h-3 mr-1" />
                                          )}
                                          {subtasks.filter(st => st.status === 'COMPLETED').length}/{subtasks.length} subtasks
                                        </button>
                                      )}
                                    </div>
                                    <h4 className="text-sm font-semibold text-gray-900 mb-1">
                                      {task.title}
                                    </h4>
                                    {task.description && (
                                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{task.description}</p>
                                    )}
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                                        {getStatusIcon(task.status)}
                                        <span className="ml-1">{task.status?.replace('_', ' ')}</span>
                                      </span>
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                                        {getPriorityLabel(task.priority)}
                                      </span>
                                      {task.due_date && (
                                        <span className={`flex items-center text-xs ${isOverdue(task.due_date, task.status) ? 'text-red-600 font-semibold' : 'text-gray-600'}`}>
                                          <Calendar className="w-3 h-3 mr-1" />
                                          {new Date(task.due_date).toLocaleDateString()}
                                          {isOverdue(task.due_date, task.status) && ' (Overdue)'}
                                        </span>
                                      )}
                                      {task.assignee_ids && task.assignee_ids.length > 0 && (
                                        <span className="flex items-center text-xs text-gray-600">
                                          <User className="w-3 h-3 mr-1" />
                                          {task.assignee_ids.map(id => {
                                            const member = teamMembers.find(m => m.id === id);
                                            return member?.username || member?.email?.split('@')[0] || 'Unknown';
                                          }).join(', ')}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Subtasks */}
                              {subtasks.length > 0 && isTaskExpanded && (
                                <div className="bg-purple-50 border-l-4 border-purple-300">
                                  {subtasks.map((subtask) => (
                                    <div key={subtask.id} className="p-3 pl-20 hover:bg-purple-100 transition-colors border-t border-purple-200">
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          <div className="flex items-center space-x-2 mb-1">
                                            <span className="text-xs text-purple-700 bg-purple-200 px-2 py-0.5 rounded font-medium">
                                              Subtask
                                            </span>
                                          </div>
                                          <h5 className="text-sm font-medium text-gray-900 mb-1">
                                            {subtask.title}
                                          </h5>
                                          {subtask.description && (
                                            <p className="text-xs text-gray-600 mb-2 line-clamp-1">{subtask.description}</p>
                                          )}
                                          <div className="flex flex-wrap items-center gap-2">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(subtask.status)}`}>
                                              {getStatusIcon(subtask.status)}
                                              <span className="ml-1">{subtask.status?.replace('_', ' ')}</span>
                                            </span>
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(subtask.priority)}`}>
                                              {getPriorityLabel(subtask.priority)}
                                            </span>
                                            {subtask.due_date && (
                                              <span className={`flex items-center text-xs ${isOverdue(subtask.due_date, subtask.status) ? 'text-red-600 font-semibold' : 'text-gray-600'}`}>
                                                <Calendar className="w-3 h-3 mr-1" />
                                                {new Date(subtask.due_date).toLocaleDateString()}
                                                {isOverdue(subtask.due_date, subtask.status) && ' (Overdue)'}
                                              </span>
                                            )}
                                            {subtask.assignee_ids && subtask.assignee_ids.length > 0 && (
                                              <span className="flex items-center text-xs text-gray-600">
                                                <User className="w-3 h-3 mr-1" />
                                                {subtask.assignee_ids.map(id => {
                                                  const member = teamMembers.find(m => m.id === id);
                                                  return member?.username || member?.email?.split('@')[0] || 'Unknown';
                                                }).join(', ')}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default TeamView;