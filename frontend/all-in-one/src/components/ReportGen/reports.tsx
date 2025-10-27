import { useState, useEffect, type ChangeEvent } from 'react';

// Backend API base URL
const API_BASE_URL = 'http://127.0.0.1:8000';

// Helper function to get auth token
const getAuthToken = () => {
  // Check common storage locations for the token
  return sessionStorage.getItem('access_token') ||
         localStorage.getItem('access_token') ||
         localStorage.getItem('token') ||
         sessionStorage.getItem('token');
};

// Helper function to create authenticated fetch headers
const getAuthHeaders = () => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json"
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
};

// Types for lists
type Project = { id: string; name: string };
type Staff = { id: string; email: string };
type Department = { id: string; name: string };

type FilterState = {
  scope_type?: string;
  scope_id?: string;
  start_date?: string;
  end_date?: string;
  time_frame?: string;
  export_format?: string;
};

interface TaskItem {
  title?: string;
  task_title?: string;
  priority?: string;
  status?: string;
  due_date?: string;
  overdue?: boolean;
}

interface StaffSummary {
  staff_name?: string;
  name?: string;
  blocked_count?: number;
  blocked?: number;
  in_progress_count?: number;
  in_progress?: number;
  completed_count?: number;
  completed?: number;
  overdue_count?: number;
  overdue?: number;
  total_tasks?: number;
  total?: number;
}

interface TimeEntry {
  staff_name?: string;
  name?: string;
  task_title?: string;
  title?: string;
  time_log?: number;
  time_logged?: number;
  status?: string;
  due_date?: string;
  overdue?: boolean;
}

interface ReportData {
  scope_type?: string;
  scope_name?: string;
  start_date?: string;
  end_date?: string;
  time_frame?: string;
  tasks?: TaskItem[];
  staff_summaries?: StaffSummary[];
  time_entries?: TimeEntry[];
  total_hours?: number;
  [key: string]: unknown;
}

type ReportDataType = ReportData | null;

const Reports = () => {
  const [selectedReport, setSelectedReport] = useState<string>("");
  const [filters, setFilters] = useState<FilterState>({});
  const [exportFormat, setExportFormat] = useState<"xlsx" | "pdf">("xlsx");
  const [reportData, setReportData] = useState<ReportDataType>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isLoadingLists, setIsLoadingLists] = useState<boolean>(true);

  // Lists from database
  const [projectList, setProjectList] = useState<Project[]>([]);
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [departmentList, setDepartmentList] = useState<Department[]>([]);

  useEffect(() => {
    async function fetchLists() {
      setIsLoadingLists(true);
      try {
        // Fetch projects
        try {
          const projectsResponse = await fetch(`${API_BASE_URL}/api/projects/list`, {
            credentials: "include",
            headers: getAuthHeaders()
          });

          if (projectsResponse.ok) {
            const projectsData = await projectsResponse.json();
            const projects = Array.isArray(projectsData) ? projectsData : [];
            setProjectList(projects.map((p: any) => ({
              id: p.id,
              name: p.name || 'Unnamed Project'
            })));
          }
        } catch (error) {
          console.error("Error fetching projects:", error);
        }

        // Fetch staff
        try {
          const staffResponse = await fetch(`${API_BASE_URL}/api/auth/users`, {
            credentials: "include",
            headers: getAuthHeaders()
          });

          if (staffResponse.ok) {
            const staffData = await staffResponse.json();
            const staff = staffData.users || [];

            console.log("Staff data sample:", staff.slice(0, 2));

            setStaffList(staff.map((s: any) => ({
              id: s.uuid,
              email: s.email || 'Unknown User'
            })));

            console.log("Processed staffList sample:", staff.slice(0, 2).map((s: any) => ({
              id: s.uuid,
              email: s.email
            })));
          }
        } catch (error) {
          console.error("Error fetching staff:", error);
        }

        // Fetch departments
        try {
          const staffResponse = await fetch(`${API_BASE_URL}/api/auth/users`, {
            credentials: "include",
            headers: getAuthHeaders()
          });

          if (staffResponse.ok) {
            const staffData = await staffResponse.json();
            const staff = staffData.users || [];

            const departmentSet = new Set<string>();
            staff.forEach((user: any) => {
              const userDepts = user.departments || [];
              userDepts.forEach((dept: string) => {
                if (dept && dept.trim()) {
                  departmentSet.add(dept.trim());
                }
              });
            });

            const departments = Array.from(departmentSet).map(dept => ({
              id: dept,
              name: dept
            }));

            setDepartmentList(departments);
          }
        } catch (error) {
          console.error("Error fetching departments:", error);
        }
      } catch (error) {
        console.error("Error fetching lists:", error);
      } finally {
        setIsLoadingLists(false);
      }
    }
    fetchLists();
  }, []);

  const handleChange = (field: keyof FilterState) => (
    e: ChangeEvent<HTMLSelectElement | HTMLInputElement>
  ) => {
    setFilters((prev) => ({ ...prev, [field]: e.target.value }));
    if (field === "scope_type") {
      setFilters((prev) => ({ ...prev, scope_id: "" }));
    }
  };

  const getScopeLabelAndOptions = () => {
    if (!selectedReport) return { label: "", options: [] as { id: string; name: string }[] };

    switch (selectedReport) {
      case "Task Completion Report":
        if (filters.scope_type === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        if (filters.scope_type === "staff") return { label: "Select Staff:", options: staffList.map(s => ({ id: s.id, name: s.email })) };
        break;
      case "Weekly/Monthly Team Summary":
        if (filters.scope_type === "department") return { label: "Select Department:", options: departmentList.map(d => ({ id: d.id, name: d.name })) };
        if (filters.scope_type === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        break;
      case "Logged Time per Project/Department":
        if (filters.scope_type === "department") return { label: "Select Department:", options: departmentList.map(d => ({ id: d.id, name: d.name })) };
        if (filters.scope_type === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        break;
      default:
        break;
    }
    return { label: "Select:", options: [] };
  };

  const { label: scopeLabel, options: scopeOptions } = getScopeLabelAndOptions();

  const validateFilters = (): boolean => {
    if (!selectedReport) {
      alert("Please select a report type.");
      return false;
    }

    if (!filters.scope_type) {
      alert("Please select a scope type.");
      return false;
    }

    if (!filters.scope_id) {
      alert("Please select a scope option.");
      return false;
    }

    if (!filters.start_date || !filters.end_date) {
      if (selectedReport === "Weekly/Monthly Team Summary") {
        alert(filters.time_frame === "weekly"
          ? "Please select a week."
          : filters.time_frame === "monthly"
          ? "Please select a month."
          : "Please select both start and end dates.");
      } else {
        alert("Please select both start and end dates.");
      }
      return false;
    }

    if (filters.end_date < filters.start_date) {
      alert("End date must be after start date.");
      return false;
    }

    if (selectedReport === "Weekly/Monthly Team Summary" && !filters.time_frame) {
      alert("Please select a time frame (weekly or monthly).");
      return false;
    }

    return true;
  };

  const handleViewReport = async () => {
    if (!validateFilters()) return;

    const endpointMap: Record<string, string> = {
      "Task Completion Report": "/api/reports/taskCompletion",
      "Weekly/Monthly Team Summary": "/api/reports/teamSummary",
      "Logged Time per Project/Department": "/api/reports/loggedTime",
    };

    const endpoint = endpointMap[selectedReport];
    if (!endpoint) {
      alert("Invalid report type.");
      return;
    }

    setIsLoading(true);
    try {
      console.log("Filters sent:", {
        scope_type: filters.scope_type,
        scope_id: filters.scope_id,
        start_date: filters.start_date,
        end_date: filters.end_date,
        time_frame: filters.time_frame
      });

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          scope_type: filters.scope_type,
          scope_id: filters.scope_id,
          start_date: filters.start_date,
          end_date: filters.end_date,
          time_frame: filters.time_frame,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Report data received:", data);
      console.log("Report type:", selectedReport);

      if (selectedReport === "Task Completion Report") {
        console.log("Tasks array:", data.tasks);
        console.log("Total tasks:", data.total_tasks);
        console.log("Scope name:", data.scope_name);
        if (data.tasks && data.tasks.length > 0) {
          console.log("First task structure:", data.tasks[0]);
        } else {
          console.log("WARNING: No tasks returned! Check backend logs for DEBUG output.");
        }
      } else if (selectedReport === "Weekly/Monthly Team Summary") {
        console.log("Staff summaries:", data.staff_summaries);
        if (data.staff_summaries && data.staff_summaries.length > 0) {
          console.log("First staff summary structure:", data.staff_summaries[0]);
        }
      } else if (selectedReport === "Logged Time per Project/Department") {
        console.log("Time entries:", data.time_entries);
        console.log("Total hours:", data.total_hours);
        if (data.time_entries && data.time_entries.length > 0) {
          console.log("First time entry structure:", data.time_entries[0]);
        }
      }

      setReportData(data);
    } catch (error) {
      console.error("Error generating report:", error);
      alert(`Failed to generate report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (!validateFilters()) return;

    const exportEndpointMap: Record<string, string> = {
      "Task Completion Report": "/api/reports/taskCompletion/export",
      "Weekly/Monthly Team Summary": "/api/reports/teamSummary/export",
      "Logged Time per Project/Department": "/api/reports/loggedTime/export",
    };

    const endpoint = exportEndpointMap[selectedReport];
    if (!endpoint) {
      alert("Invalid report type for export.");
      return;
    }

    setIsExporting(true);
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          scope_type: filters.scope_type,
          scope_id: filters.scope_id,
          start_date: filters.start_date,
          end_date: filters.end_date,
          time_frame: filters.time_frame,
          export_format: exportFormat,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      const reportType = selectedReport.toLowerCase().replace(/ /g, "_");
      const extension = exportFormat === "xlsx" ? ".xlsx" : ".pdf";
      link.download = `${reportType}_${filters.scope_type}_${filters.start_date}${extension}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert("Report exported successfully!");
    } catch (error) {
      console.error("Error exporting file:", error);
      alert(`Failed to export file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const renderDynamicFields = () => {
    if (!selectedReport) return null;

    switch (selectedReport) {
      case "Task Completion Report":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex flex-col flex-1 min-w-[200px]">
                <label className="font-medium mb-1">Scope Type <span className="text-red-500">*</span></label>
                <select
                  value={filters.scope_type ?? ""}
                  onChange={handleChange("scope_type")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  <option value="project">Project</option>
                  <option value="staff">Staff</option>
                </select>
              </div>
              {filters.scope_type && (
                <div className="flex flex-col flex-1 min-w-[200px]">
                  <label className="font-medium mb-1">{scopeLabel} <span className="text-red-500">*</span></label>
                  <select
                    value={filters.scope_id ?? ""}
                    onChange={handleChange("scope_id")}
                    className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="" key="empty-option">Select {scopeLabel}</option>
                    {scopeOptions.length === 0 && (
                      <option value="" disabled key="no-options">No options available</option>
                    )}
                    {scopeOptions.map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {opt.name}
                      </option>
                    ))}
                  </select>
                  {scopeOptions.length === 0 && (
                    <p className="text-xs text-red-500 mt-1">
                      No {scopeLabel.toLowerCase()} found. Check console for errors.
                    </p>
                  )}
                </div>
              )}
            </div>
            <div className="flex gap-4 mb-4">
              <div className="flex flex-col flex-1">
                <label className="font-medium mb-1">Start Date <span className="text-red-500">*</span></label>
                <input
                  type="date"
                  value={filters.start_date ?? ""}
                  onChange={handleChange("start_date")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col flex-1">
                <label className="font-medium mb-1">End Date <span className="text-red-500">*</span></label>
                <input
                  type="date"
                  value={filters.end_date ?? ""}
                  onChange={handleChange("end_date")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </>
        );

      case "Weekly/Monthly Team Summary":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex flex-col flex-1 min-w-[200px]">
                <label className="font-medium mb-1">Scope Type <span className="text-red-500">*</span></label>
                <select
                  value={filters.scope_type ?? ""}
                  onChange={handleChange("scope_type")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  <option value="department">Department</option>
                  <option value="project">Project</option>
                </select>
              </div>
              {filters.scope_type && (
                <div className="flex flex-col flex-1 min-w-[200px]">
                  <label className="font-medium mb-1">{scopeLabel} <span className="text-red-500">*</span></label>
                  <select
                    value={filters.scope_id ?? ""}
                    onChange={handleChange("scope_id")}
                    className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="" key="empty">Select</option>
                    {scopeOptions.map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {opt.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className="flex gap-4 mb-4">
              <div className="flex flex-col flex-1">
                <label className="font-medium mb-1">Time Frame <span className="text-red-500">*</span></label>
                <select
                  value={filters.time_frame ?? ""}
                  onChange={(e) => {
                    setFilters((prev) => ({
                      ...prev,
                      time_frame: e.target.value,
                      start_date: "",
                      end_date: ""
                    }));
                  }}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>

            {filters.time_frame === "weekly" && (
              <div className="flex gap-4 mb-4">
                <div className="flex flex-col flex-1">
                  <label className="font-medium mb-1">Select Week <span className="text-red-500">*</span></label>
                  <input
                    type="week"
                    onChange={(e) => {
                      const weekValue = e.target.value; // Format: "2025-W43"
                      if (weekValue) {
                        const [year, week] = weekValue.split('-W');
                        const firstDayOfYear = new Date(parseInt(year), 0, 1);
                        const daysOffset = (parseInt(week) - 1) * 7;
                        const firstDayOfWeek = new Date(firstDayOfYear.getTime() + daysOffset * 24 * 60 * 60 * 1000);

                        // Adjust to Monday (ISO week starts on Monday)
                        const dayOfWeek = firstDayOfWeek.getDay();
                        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
                        const monday = new Date(firstDayOfWeek.getTime() + mondayOffset * 24 * 60 * 60 * 1000);

                        // Calculate Sunday (6 days after Monday)
                        const sunday = new Date(monday.getTime() + 6 * 24 * 60 * 60 * 1000);

                        const startDate = monday.toISOString().split('T')[0];
                        const endDate = sunday.toISOString().split('T')[0];

                        setFilters((prev) => ({
                          ...prev,
                          start_date: startDate,
                          end_date: endDate
                        }));
                      }
                    }}
                    className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {filters.start_date && filters.end_date && (
                    <p className="text-xs text-gray-600 mt-1">
                      Selected: {filters.start_date} to {filters.end_date}
                    </p>
                  )}
                </div>
              </div>
            )}

            {filters.time_frame === "monthly" && (
              <div className="flex gap-4 mb-4">
                <div className="flex flex-col flex-1">
                  <label className="font-medium mb-1">Select Month <span className="text-red-500">*</span></label>
                  <input
                    type="month"
                    onChange={(e) => {
                      const monthValue = e.target.value; // Format: "2025-10"
                      if (monthValue) {
                        const [year, month] = monthValue.split('-');
                        const firstDay = new Date(parseInt(year), parseInt(month) - 1, 1);
                        const lastDay = new Date(parseInt(year), parseInt(month), 0);

                        const startDate = firstDay.toISOString().split('T')[0];
                        const endDate = lastDay.toISOString().split('T')[0];

                        setFilters((prev) => ({
                          ...prev,
                          start_date: startDate,
                          end_date: endDate
                        }));
                      }
                    }}
                    className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {filters.start_date && filters.end_date && (
                    <p className="text-xs text-gray-600 mt-1">
                      Selected: {filters.start_date} to {filters.end_date}
                    </p>
                  )}
                </div>
              </div>
            )}
          </>
        );

      case "Logged Time per Project/Department":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex flex-col flex-1 min-w-[200px]">
                <label className="font-medium mb-1">Scope Type <span className="text-red-500">*</span></label>
                <select
                  value={filters.scope_type ?? ""}
                  onChange={handleChange("scope_type")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  <option value="department">Department</option>
                  <option value="project">Project</option>
                </select>
              </div>
              {filters.scope_type && (
                <div className="flex flex-col flex-1 min-w-[200px]">
                  <label className="font-medium mb-1">{scopeLabel} <span className="text-red-500">*</span></label>
                  <select
                    value={filters.scope_id ?? ""}
                    onChange={handleChange("scope_id")}
                    className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="" key="empty">Select</option>
                    {scopeOptions.map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {opt.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className="flex gap-4 mb-4">
              <div className="flex flex-col flex-1">
                <label className="font-medium mb-1">Start Date <span className="text-red-500">*</span></label>
                <input
                  type="date"
                  value={filters.start_date ?? ""}
                  onChange={handleChange("start_date")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col flex-1">
                <label className="font-medium mb-1">End Date <span className="text-red-500">*</span></label>
                <input
                  type="date"
                  value={filters.end_date ?? ""}
                  onChange={handleChange("end_date")}
                  className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Generate Reports</h2>

      {isLoadingLists && (
        <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded">
          Loading projects, staff, and departments...
        </div>
      )}

      {!isLoadingLists && (
        <div className="mb-4 p-3 bg-gray-50 text-gray-600 rounded text-sm">
          <div>Loaded: {projectList.length} projects, {staffList.length} staff, {departmentList.length} departments</div>

          <details className="mt-2">
            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">Show Debug Data</summary>
            <div className="mt-2 p-2 bg-white rounded text-xs overflow-auto max-h-48">
              <div className="mb-2">
                <strong>Projects ({projectList.length}):</strong>
                <pre>{JSON.stringify(projectList.slice(0, 3), null, 2)}</pre>
              </div>
              <div className="mb-2">
                <strong>Staff ({staffList.length}):</strong>
                <pre>{JSON.stringify(staffList.slice(0, 3), null, 2)}</pre>
              </div>
              <div>
                <strong>Departments ({departmentList.length}):</strong>
                <pre>{JSON.stringify(departmentList, null, 2)}</pre>
              </div>
            </div>
          </details>
        </div>
      )}

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-3">Select Report Type</h3>
        <div className="space-y-2">
          {[
            "Task Completion Report",
            "Weekly/Monthly Team Summary",
            "Logged Time per Project/Department",
          ].map((report) => (
            <div key={report} className="flex items-center space-x-3 p-3 border rounded hover:bg-gray-50 transition-colors">
              <input
                type="radio"
                id={report}
                name="reportType"
                checked={selectedReport === report}
                onChange={() => {
                  setSelectedReport(report);
                  setFilters({});
                  setReportData(null);
                }}
                className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <label
                htmlFor={report}
                className={`cursor-pointer flex-1 ${
                  selectedReport === report ? "font-semibold text-blue-600" : "text-gray-700"
                }`}
              >
                {report}
              </label>
            </div>
          ))}
        </div>
      </div>

      {selectedReport && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Report Filters</h3>
          {renderDynamicFields()}
        </div>
      )}

      {selectedReport && (
        <div className="flex items-center gap-4 flex-wrap">
          <button
            type="button"
            className={`px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors ${
              isLoading ? "opacity-50 cursor-not-allowed" : ""
            }`}
            onClick={handleViewReport}
            disabled={isLoading}
          >
            {isLoading ? "Loading..." : "View Report"}
          </button>

          <div className="flex items-center gap-4 ml-auto">
            <label className="flex items-center space-x-2 font-medium">
              <span>Export as:</span>
              <select
                className="border rounded p-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as "xlsx" | "pdf")}
              >
                <option value="xlsx">Excel (.xlsx)</option>
                <option value="pdf">PDF (.pdf)</option>
              </select>
            </label>

            <button
              type="button"
              className={`px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors ${
                isExporting ? "opacity-50 cursor-not-allowed" : ""
              }`}
              onClick={handleExport}
              disabled={isExporting}
            >
              {isExporting ? "Exporting..." : "Export"}
            </button>
          </div>
        </div>
      )}

      {reportData && (
        <div className="mt-6 bg-white border rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-6 py-4 border-b">
            <h3 className="text-xl font-semibold text-gray-900">Report Preview</h3>
            <p className="text-sm text-gray-600 mt-1">
              {selectedReport} - {reportData.scope_type}: {reportData.scope_name}
            </p>
            {reportData.start_date && reportData.end_date && (
              <p className="text-sm text-gray-600">
                Period: {reportData.start_date} to {reportData.end_date}
              </p>
            )}

            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">Show Raw Data (Debug)</summary>
              <div className="mt-2 p-2 bg-white rounded text-xs overflow-auto max-h-48">
                <pre>{JSON.stringify(reportData, null, 2)}</pre>
              </div>
            </details>
          </div>

          <div className="p-6 overflow-auto">
            {selectedReport === "Task Completion Report" && reportData.tasks && (
              <div>
                <p className="text-sm text-gray-600 mb-4">Total Tasks: {reportData.tasks.length}</p>
                {reportData.tasks.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No tasks found for the selected criteria.</p>
                  </div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Overdue</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {reportData.tasks.map((task: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">{task.title || task.task_title || 'No Title'}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              task.priority === 'HIGH' ? 'bg-red-100 text-red-800' :
                              task.priority === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {task.priority || 'N/A'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              task.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                              task.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                              task.status === 'BLOCKED' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {task.status?.replace('_', ' ') || 'N/A'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">{task.due_date || 'N/A'}</td>
                          <td className="px-4 py-3 text-sm">
                            {task.overdue ? (
                              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">Yes</span>
                            ) : (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium">No</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {selectedReport === "Weekly/Monthly Team Summary" && reportData.staff_summaries && (
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Time Frame: {reportData.time_frame} | Total Staff: {reportData.staff_summaries.length}
                </p>
                {reportData.staff_summaries.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No staff summaries found for the selected criteria.</p>
                  </div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Staff Member</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Blocked</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">In Progress</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Completed</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Overdue</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Total Tasks</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {reportData.staff_summaries.map((staff: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{staff.staff_name || staff.name || 'Unknown'}</td>
                          <td className="px-4 py-3 text-sm text-center text-red-600 font-semibold">{staff.blocked_count ?? staff.blocked ?? 0}</td>
                          <td className="px-4 py-3 text-sm text-center text-blue-600 font-semibold">{staff.in_progress_count ?? staff.in_progress ?? 0}</td>
                          <td className="px-4 py-3 text-sm text-center text-green-600 font-semibold">{staff.completed_count ?? staff.completed ?? 0}</td>
                          <td className="px-4 py-3 text-sm text-center text-orange-600 font-semibold">{staff.overdue_count ?? staff.overdue ?? 0}</td>
                          <td className="px-4 py-3 text-sm text-center text-gray-900 font-semibold">{staff.total_tasks ?? staff.total ?? 0}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {selectedReport === "Logged Time per Project/Department" && reportData.time_entries && (
              <div>
                <div className="mb-4 flex justify-between items-center">
                  <p className="text-sm text-gray-600">Total Entries: {reportData.time_entries.length}</p>
                  <p className="text-lg font-semibold text-gray-900">
                    Total Hours: <span className="text-blue-600">{reportData.total_hours?.toFixed(2) || '0.00'}</span>
                  </p>
                </div>
                {reportData.time_entries.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No time entries found for the selected criteria.</p>
                  </div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Staff Member</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Time (hrs)</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Overdue</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {reportData.time_entries.map((entry: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">{entry.staff_name || entry.name || 'Unknown'}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{entry.task_title || entry.title || 'Unknown Task'}</td>
                          <td className="px-4 py-3 text-sm text-center font-semibold text-blue-600">{entry.time_log?.toFixed(2) || entry.time_logged?.toFixed(2) || '0.00'}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              entry.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                              entry.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                              entry.status === 'BLOCKED' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {entry.status?.replace('_', ' ') || 'N/A'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">{entry.due_date || 'N/A'}</td>
                          <td className="px-4 py-3 text-sm text-center">
                            {entry.overdue ? (
                              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">Yes</span>
                            ) : (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium">No</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {selectedReport === "Task Completion Report" && !reportData.tasks && (
              <div className="text-center py-8 text-red-500">
                <p>Error: Report data structure is invalid. Expected 'tasks' array.</p>
                <p className="text-sm mt-2">Check console for raw data.</p>
              </div>
            )}

            {selectedReport === "Weekly/Monthly Team Summary" && !reportData.staff_summaries && (
              <div className="text-center py-8 text-red-500">
                <p>Error: Report data structure is invalid. Expected 'staff_summaries' array.</p>
                <p className="text-sm mt-2">Check console for raw data.</p>
              </div>
            )}

            {selectedReport === "Logged Time per Project/Department" && !reportData.time_entries && (
              <div className="text-center py-8 text-red-500">
                <p>Error: Report data structure is invalid. Expected 'time_entries' array.</p>
                <p className="text-sm mt-2">Check console for raw data.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
