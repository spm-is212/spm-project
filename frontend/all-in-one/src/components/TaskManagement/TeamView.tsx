import { useState, useEffect, useCallback } from 'react';
import { Calendar, User, Filter, AlertCircle, CheckCircle, Clock, XCircle, Folder, Users, Building, ChevronDown, ChevronRight } from 'lucide-react';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';
import type { Task, User as UserType } from '../../types/Task';

interface Project {
  id: string;
  name: string;
  description?: string;
  team_id: string;
  created_at?: string;
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
  const [selectedMember, setSelectedMember] = useState<string>('all');
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('due_date');
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  useEffect(() => {
    const user = getUserFromToken();
    if (user) {
      setUserInfo({
        email: '', // Email not available from token
        role: user.role || '',
        department: user.department || '',
        department_id: user.department || '',
        user_id: user.id || ''
      });
    }
  }, []);

  // Fetch user's teams in their department
  const fetchTeams = useCallback(async () => {
    try {
      const data = await apiFetch("teams/my-teams");

      // Transform string array to Team objects if needed (backend returns strings currently)
      let teamsData = data.teams || [];
      if (teamsData.length > 0 && typeof teamsData[0] === 'string') {
        teamsData = teamsData.map((teamName: string, index: number) => ({
          id: `team${index + 1}`,
          name: teamName,
          member_count: 0
        }));
      }

      setTeams(teamsData);
      if (teamsData.length > 0 && !selectedTeam) {
        setSelectedTeam(teamsData[0].id || '');
      }
    } catch (err: unknown) {
      console.error(`Failed to fetch teams: ${err instanceof Error ? err.message : String(err)}`);
      setError('Failed to load teams');
    }
  }, [selectedTeam]);

  // Fetch projects for selected team(s)
  const fetchProjects = useCallback(async () => {
    try {
      const endpoint = selectedTeam && selectedTeam !== ''
        ? `projects/list?team_id=${selectedTeam}`
        : 'projects/list';
      const data = await apiFetch(endpoint);
      setProjects(data || []);
    } catch (err: unknown) {
      console.error(`Failed to fetch projects: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, [selectedTeam]);

  // Fetch tasks from backend
  const fetchTeamTasks = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("tasks/readTasks");
      const tasksData = data.tasks || [];

      // Transform tasks to include parent/subtask information
      const transformedTasks: TaskWithProject[] = tasksData.map((task: any) => ({
        ...task,
        isSubtask: task.parent_id !== null && task.parent_id !== undefined,
        parent_id: task.parent_id,
        project_id: task.project_id,
        project_name: task.project_name,
      }));

      setTasks(transformedTasks);
      setFilteredTasks(transformedTasks);
    } catch (err: unknown) {
      setError(`Failed to fetch team tasks: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
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

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...tasks];

    // Filter by team
    if (selectedTeam !== '' && selectedTeam !== 'all') {
      const teamProjects = projects.filter(p => p.team_id === selectedTeam).map(p => p.id);
      filtered = filtered.filter(task => teamProjects.includes(task.project_id || ''));
    }

    // Filter by project
    if (selectedProject !== 'all') {
      filtered = filtered.filter(task => task.project_id === selectedProject);
    }

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
          const priorityOrder: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
          return (priorityOrder[a.priority?.toUpperCase()] || 3) - (priorityOrder[b.priority?.toUpperCase()] || 3);
        case 'status':
          return (a.status || '').localeCompare(b.status || '');
        case 'title':
          return a.title.localeCompare(b.title);
        default:
          return 0;
      }
    });

    setFilteredTasks(filtered);
  }, [tasks, selectedTeam, selectedProject, selectedMember, selectedStatus, sortBy, projects]);

  // Load data on mount
  useEffect(() => {
    document.title = "My Teams";
    fetchTeams();
    fetchTeamMembers();
    fetchTeamTasks();
  }, [fetchTeams, fetchTeamMembers, fetchTeamTasks]);

  // Reload projects when team changes
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Get filtered projects based on selected team
  const getFilteredProjects = () => {
    if (selectedTeam === '' || selectedTeam === 'all') return projects;
    return projects.filter(p => p.team_id === selectedTeam);
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
  const getPriorityColor = (priority: string | undefined): string => {
    switch (priority?.toUpperCase()) {
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
                <Users className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">
                  <strong>Projects:</strong> {teams.length}
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

      {/* Teams List */}
      <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center mb-4">
          <Users className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">My Projects</h2>
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

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
          <div className="text-sm text-gray-600">Done</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
          <div className="text-sm text-gray-600">Active</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-gray-600">{stats.pending}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-orange-600">{stats.blocked}</div>
          <div className="text-sm text-gray-600">Blocked</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="text-2xl font-bold text-red-600">{stats.overdue}</div>
          <div className="text-sm text-gray-600">Overdue</div>
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

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center mb-3">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filters & Sorting</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Projects</option>
              {getFilteredProjects().map(project => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Member</label>
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
              <option value="TO_DO">Pending</option>
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
              <option value="title">Title</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSelectedMember('all');
                setSelectedProject('all');
                setSelectedStatus('all');
                setSortBy('due_date');
              }}
              className="w-full p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Clear Filters
            </button>
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
              Tasks ({filteredTasks.filter(t => !t.isSubtask).length})
            </h2>
          </div>
          <div className="divide-y">
            {filteredTasks.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No tasks found matching the selected filters.
              </div>
            ) : (
              filteredTasks
                .filter(task => !task.isSubtask)
                .map((task) => {
                  const subtasks = filteredTasks.filter(t => t.isSubtask && t.parent_id === task.id);
                  const isExpanded = expandedTasks.has(task.id);

                  return (
                    <div key={task.id}>
                      {/* Parent Task */}
                      <div className="p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              {task.project_name && (
                                <span className="flex items-center text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                  <Folder className="w-3 h-3 mr-1" />
                                  {task.project_name}
                                </span>
                              )}
                              {subtasks.length > 0 && (
                                <button
                                  onClick={() => toggleTaskExpansion(task.id)}
                                  className="flex items-center text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded font-medium hover:bg-gray-200 transition-colors"
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="w-3 h-3 mr-1" />
                                  ) : (
                                    <ChevronRight className="w-3 h-3 mr-1" />
                                  )}
                                  {subtasks.filter(st => st.status === 'COMPLETED').length}/{subtasks.length} subtasks
                                </button>
                              )}
                            </div>
                            <h3 className="text-base font-semibold text-gray-900 mb-1">
                              {task.title}
                            </h3>
                            {task.description && (
                              <p className="text-sm text-gray-600 mb-2 line-clamp-2">{task.description}</p>
                            )}
                            <div className="flex flex-wrap items-center gap-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                                {getStatusIcon(task.status)}
                                <span className="ml-1">{task.status?.replace('_', ' ')}</span>
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

                      {/* Subtasks - Collapsible */}
                      {subtasks.length > 0 && isExpanded && (
                        <div className="bg-gray-50 border-l-4 border-purple-200">
                          {subtasks.map((subtask) => (
                            <div key={subtask.id} className="p-4 pl-8 hover:bg-gray-100 transition-colors border-t border-gray-200">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded font-medium">
                                      Subtask
                                    </span>
                                  </div>
                                  <h3 className="text-base font-medium text-gray-900 mb-1">
                                    {subtask.title}
                                  </h3>
                                  {subtask.description && (
                                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">{subtask.description}</p>
                                  )}
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(subtask.status)}`}>
                                      {getStatusIcon(subtask.status)}
                                      <span className="ml-1">{subtask.status?.replace('_', ' ')}</span>
                                    </span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(subtask.priority)}`}>
                                      {subtask.priority}
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
        </div>
      )}
    </div>
  );
};

export default TeamView;
