import { useState, useEffect, useCallback } from 'react';
import { AlertCircle, Folder, Users, Building} from 'lucide-react';
import { apiFetch } from "../../utils/api";
import { getUserFromToken } from '../../utils/auth';
import { API_ENDPOINTS } from '../../config/api';
import type { Task, User as UserType } from '../../types/Task';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, addMonths, subMonths } from "date-fns";

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

const CalendarView = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<TaskWithProject[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<TaskWithProject[]>([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [userInfo, setUserInfo] = useState<{ email: string; role: string; department?: string; department_id?: string; user_id?: string } | null>(null);

  // Filters
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [selectedAssignees, setSelectedAssignees] = useState<string[]>([]);
  const [teamMembers, setTeamMembers] = useState<UserType[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [filteredPersons, setFilteredPersons] = useState<UserType[]>(teamMembers);
  const [sortBy, setSortBy] = useState<string>('priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');


  const [currentMonth, setCurrentMonth] = useState(new Date());
  const daysInMonth = eachDayOfInterval({
    start: startOfMonth(currentMonth),
    end: endOfMonth(currentMonth),
  });
  const padDays = getDay(startOfMonth(currentMonth)); // Blank cells before first day

  const handlePrevMonth = () => setCurrentMonth((prev) => subMonths(prev, 1));
  const handleNextMonth = () => setCurrentMonth((prev) => addMonths(prev, 1));

  const tasksByDate: Record<string, TaskWithProject[]> = {};
    (filteredTasks || []).forEach(task => {
    if (task.due_date) {
      const dateKey = format(new Date(task.due_date), "yyyy-MM-dd");
      if (!tasksByDate[dateKey]) tasksByDate[dateKey] = [];
      tasksByDate[dateKey].push(task);
    }
  });

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
    sorted.sort((a, b) => {
      let result = 0;
      switch (sortBy) {
        case 'priority': {
          result = (a.priority ?? 0) - (b.priority ?? 0);
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

  const userProjects = getUserCollaboratorProjects();

  useEffect(() => {
    if (userInfo?.role?.toLowerCase() === 'staff') {
    // Staff users don't see persons dropdown
      setFilteredPersons([]);
      setSelectedPersonId(null);
    } else {
      if (selectedProjectId) {
        const personsInProject = teamMembers.filter(member => {
          return tasks.some(task =>
            task.project_id?.toString() === selectedProjectId &&
            (task.owner_user_id?.toString() === member.id?.toString() ||
            task.assignee_ids?.map(String).includes(member.id?.toString()))
          );
        });
        setFilteredPersons(personsInProject);

        if (selectedPersonId && !personsInProject.find(p => p.id === selectedPersonId)) {
          setSelectedPersonId(null);
        }
      } else {
        setFilteredPersons(teamMembers);
      }
    }
  }, [selectedProjectId, userInfo?.role, tasks, teamMembers, selectedPersonId]);

  useEffect(() => {
    if (loading) return; // wait until tasks are loaded

    let filtered = [...tasks];
    if (selectedProjectId) {
      filtered = filtered.filter(t => t.project_id === selectedProjectId);
    }
    if (selectedPersonId) {
      filtered = filtered.filter(t =>
        t.owner_user_id === selectedPersonId ||
        t.assignee_ids?.includes(selectedPersonId)
      );
    }
    setFilteredTasks(filtered);
  }, [selectedProjectId, selectedPersonId, tasks, loading]);


  const resetFilters = () => {
    setSelectedProjectId(null);
    setSelectedPersonId(null);
    setFilteredTasks(tasks);
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



  const isOverdue = (dueDate: string | undefined, status: string | undefined): boolean => {
    if (!dueDate || status === 'COMPLETED') return false;
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return due < today;
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

      {/* Project Dropdown */}
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
    <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>

    <div className="flex flex-wrap items-center space-x-4">
    {/* Project Dropdown */}
    <div className="flex flex-col flex-1 min-w-0">
        <label htmlFor="project-select" className="font-medium text-gray-700 mb-1">Select Project</label>
        <select
        id="project-select"
        className="border rounded p-2 w-full"
        value={selectedProjectId ?? ''}
        onChange={e => setSelectedProjectId(e.target.value || null)}
        >
        <option value="">-- All Projects --</option>
        {userProjects.map(project => (
            <option key={project.id} value={project.id}>{project.name}</option>
        ))}
        </select>
    </div>

    {/* Person Dropdown */}
    {userInfo?.role?.toLowerCase() !== 'staff' && (
        <div className="flex flex-col flex-1 min-w-0">
        <label htmlFor="person-select" className="font-medium text-gray-700 mb-1">Select Person</label>
        <select
            id="person-select"
            className="border rounded p-2 w-full"
            value={selectedPersonId ?? ''}
            onChange={e => setSelectedPersonId(e.target.value || null)}
        >
            <option value="">-- All Persons --</option>
            {filteredPersons.map(person => (
            <option key={person.id} value={person.id}>
                {person.email}
            </option>
            ))}
        </select>
        </div>
    )}

    {/* Reset Button */}
    <div className="flex flex-col justify-end min-w-[100px]">
        <button
        onClick={resetFilters}
        className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 w-full sm:w-auto"
        >
        Reset
        </button>
    </div>
    </div>

    </div>

      <div>

      {/* Month navigation header */}
      <div>
      <div className="flex items-center w-full max-w-xl mx-auto">
        <header className="flex justify-between items-center mb-6 w-full">
            <button
            onClick={handlePrevMonth}
            className="px-3 py-1 border rounded hover:bg-gray-200"
            >
            Prev
            </button>
            <div className="text-center">
            <div className="text-2xl font-bold">{format(currentMonth, "MMMM")}</div>
            <div className="text-xl font-semibold">{format(currentMonth, "yyyy")}</div>
            </div>
            <button
            onClick={handleNextMonth}
            className="px-3 py-1 border rounded hover:bg-gray-200"
            >
            Next
            </button>
        </header>
        </div>

      {/* Legend */}
      <div>
        <div className="flex flex-wrap items-center gap-6 mb-4">
      <div className="flex items-center gap-2">
        <span className="inline-block w-4 h-4 rounded bg-green-100 border-l-4 border-green-500"></span>
        <span className="text-xs text-green-800">Completed</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block w-4 h-4 rounded bg-blue-100 border-l-4 border-blue-500"></span>
        <span className="text-xs text-blue-800">In Progress</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block w-4 h-4 rounded bg-yellow-100 border-l-4 border-yellow-500"></span>
        <span className="text-xs text-yellow-800">To Do</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block w-4 h-4 rounded bg-red-100 border-l-4 border-red-500"></span>
        <span className="text-xs text-red-800 font-bold">Overdue</span>
      </div>

      {/* Calendar grid */}
      </div>
        <div className="grid grid-cols-7 gap-2 md:gap-3 lg:gap-4">
        {/* Day Headers */}
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
        <div
            key={day}
            className="text-center font-semibold text-gray-500 py-2 bg-gray-100"
        >
            {day}
        </div>
        ))}

        {/* Padding cells for calendar alignment */}
            {Array(padDays).fill(null).map((_, idx) => (
            <div key={`pad-${idx}`} />
            ))}

        {/* Date cells */}
        {daysInMonth.map((day) => {
        const dateStr = format(day, "yyyy-MM-dd");
        const dayTasks = tasksByDate[dateStr] || [];
        return (
            <div
                key={dateStr}
                className="h-[120px] border p-2 bg-white flex flex-col items-start"
            >
            <div className="text-sm font-semibold mb-2">{format(day, "d")}</div>
            <div className="flex flex-col gap-1 overflow-auto max-h-[90px] w-full">
                {dayTasks.length === 0 ? (
                <div className="text-xs text-gray-400">No tasks</div>
                ) : (
                dayTasks.map((task) => (
                    <div
                    key={task.id}
                    onClick={() => setSelectedTask(task)}
                    className={
                        "cursor-pointer text-xs p-1 rounded truncate w-full " +
                        (
                          isOverdue(task.due_date, task.status)
                            ? "bg-red-100 border-l-4 border-red-500 text-red-800 font-bold"
                            : task.status === "COMPLETED"
                            ? "bg-green-100 border-l-4 border-green-500 text-green-800"
                            : task.status === "IN_PROGRESS"
                            ? "bg-blue-100 border-l-4 border-blue-500 text-blue-800"
                            : task.status === "TO_DO"
                            ? "bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800"
                            : "bg-gray-100 border-l-4 border-gray-400 text-gray-600"
                        )
                      }
                    title={task.title}
                    >
                    {task.title}
                    </div>
                ))
                )}
            </div>
            </div>
        );
        })}
    </div>
    </div>

    </div>

    {selectedTask && (
      <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md relative">
          <button
            onClick={() => setSelectedTask(null)}
            className="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-xl"
            aria-label="Close"
          >×</button>
          <h2 className="text-2xl font-bold mb-1">{selectedTask.title}</h2>
          <p className="text-gray-500 mb-3">{selectedTask.description}</p>
          <div className="flex gap-2 mb-2">
            <span className={`px-3 py-1 rounded-xl text-xs font-medium ${
              selectedTask.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' : ''
            } ${selectedTask.status === "COMPLETED" ? 'bg-green-100 text-green-700' : ''} ${selectedTask.status === 'TO DO' ? 'bg-gray-100 text-gray-700' : ''}`}>
              {selectedTask.status}
            </span>
            <span className={`px-3 py-1 rounded-xl text-xs font-medium ${
              selectedTask.priority === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700' : ''
            }`}>
              {selectedTask.priority}
            </span>
          </div>
          <div className="flex gap-2 text-gray-500 text-sm mb-2">
            <span>📅 {selectedTask.due_date}</span>
          </div>
          <div className="flex flex-wrap gap-2 mb-2">
            {selectedTask.assignees?.map((user) => (
              <span
                key={user}
                className="bg-blue-100 text-blue-600 px-3 py-1 rounded-xl text-xs"
              >
                {user}
              </span>
            ))}
          </div>
          {/* Subtasks, if any */}
          {selectedTask.subtasks && selectedTask.subtasks.length > 0 && (
            <div>
              <h3 className="font-semibold text-md mt-2 mb-1">Subtasks ({selectedTask.subtasks.length})</h3>
              <div className="space-y-2">
                {selectedTask.subtasks.map((sub, idx) => (
                  <div
                    key={idx}
                    className="border bg-gray-50 rounded-xl p-3"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded-xl text-xs font-medium ${
                        sub.status === "COMPLETED" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                      }`}>
                        {sub.status}
                      </span>
                      <span className="px-2 py-0.5 rounded-xl text-xs font-medium bg-yellow-100 text-yellow-700">
                        {sub.priority}
                      </span>
                    </div>
                    <div className="font-semibold text-sm">{sub.title}</div>
                    <div className="text-xs text-gray-500">{sub.due_date}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {sub.assignees?.map((u) => (
                        <span key={u} className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded-xl text-xs">{u}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )}


      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      )}

    </div>
    </div>
  );
};

export default CalendarView;
