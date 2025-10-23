import { useState, useEffect, type ChangeEvent, type JSX } from 'react';

// Types for lists
type Project = { id: string; name: string };
type Staff = { id: string; email: string };
type Department = { id: string; name: string };

type FilterState = {
  scopeType?: string;
  scopeId?: string;
  startDate?: string;
  endDate?: string;
  timeframe?: string;
};

type ReportData = Record<string, unknown> | null;

const Reports = () => {
    const [selectedReport, setSelectedReport] = useState<string>("");
    const [filters, setFilters] = useState<FilterState>({});
    const [exportFormat, setExportFormat] = useState<"excel" | "pdf">("excel");
    const [reportData, setReportData] = useState<ReportData>(null);

    // Lists from database (to be fetched)
    const [projectList, setProjectList] = useState<Project[]>([]);
    const [staffList, setStaffList] = useState<Staff[]>([]);
    const [departmentList, setDepartmentList] = useState<Department[]>([]);

    useEffect(() => {
    async function fetchLists() {
      // Replace URLs with your real endpoints or functions imported from CalendarView
      const projectsResponse = await fetch("/api/projects");
      const projects = (await projectsResponse.json()) as Project[];
      setProjectList(projects);

      const staffResponse = await fetch("/api/staff");
      const staff = (await staffResponse.json()) as Staff[];
      setStaffList(staff);

      const departmentResponse = await fetch("/api/departments");
      const departments = (await departmentResponse.json()) as Department[];
      setDepartmentList(departments);
    }
    fetchLists();
    }, []);

    const handleChange = (field: keyof FilterState) => (
    e: ChangeEvent<HTMLSelectElement | HTMLInputElement>
  ) => {
    setFilters((prev) => ({ ...prev, [field]: e.target.value }));
    // Clear scopeId if scopeType changes
    if (field === "scopeType") {
      setFilters((prev) => ({ ...prev, scopeId: "" }));
    }
  };

  const getScopeLabelAndOptions = () => {
    if (!selectedReport) return { label: "", options: [] as { id: string; name: string }[] };

    switch (selectedReport) {
      case "Task Completion Report":
        if (filters.scopeType === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        if (filters.scopeType === "staff") return { label: "Select Staff:", options: staffList.map(s => ({ id: s.id, name: s.email })) };
        break;
      case "Weekly/Monthly Team Summary":
        if (filters.scopeType === "department") return { label: "Select Department:", options: departmentList.map(d => ({ id: d.id, name: d.name })) };
        if (filters.scopeType === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        break;
      case "Logged Time per Project/Department":
        if (filters.scopeType === "department") return { label: "Select Department:", options: departmentList.map(d => ({ id: d.id, name: d.name })) };
        if (filters.scopeType === "project") return { label: "Select Project:", options: projectList.map(p => ({ id: p.id, name: p.name })) };
        break;
      default:
        break;
    }
    return { label: "Select:", options: [] };
  };

  const { label: scopeLabel, options: scopeOptions } = getScopeLabelAndOptions();

  const validateDates = (): boolean => {
    if (filters.startDate && filters.endDate) {
      if (filters.endDate < filters.startDate) {
        alert("End date must be after start date.");
        return false;
      }
    }
    return true;
  };

  const handleViewReport = async () => {
    if (!selectedReport) {
      alert("Please select a report type.");
      return;
    }
    if (!validateDates()) return;

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

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...filters, exportFormat: "json" }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setReportData(data);
    } catch (error) {
      console.error("Error generating report:", error);
      alert("Failed to generate report.");
    }
    };

    const handleExport = async () => {
    if (!selectedReport) {
      alert("Please select a report type.");
      return;
    }
    if (!validateDates()) return;

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

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...filters, exportFormat }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download =
        selectedReport.toLowerCase().replace(/ /g, "_") +
        (exportFormat === "excel" ? ".xlsx" : ".pdf");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error exporting file:", error);
      alert("Failed to export file.");
    }
  };


  // Conditional Filters based on selected report
  const renderDynamicFields = () => {
    if (!selectedReport) return null;

    switch (selectedReport) {
      case "Task Completion Report":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">Select Project or Staff:</label>
                <select value={filters.scopeType ?? ""} onChange={handleChange("scopeType")} className="border rounded p-2">
                  <option value="">Select</option>
                  <option value="project">Project</option>
                  <option value="staff">Staff</option>
                </select>
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">{scopeLabel}</label>
                <select value={filters.scopeId ?? ""} onChange={handleChange("scopeId")} className="border rounded p-2">
                  <option value="">Select</option>
                  {scopeOptions.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">Start Date</label>
                <input type="date" value={filters.startDate ?? ""} onChange={handleChange("startDate")} className="border rounded p-2 w-full" />
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">End Date</label>
                <input type="date" value={filters.endDate ?? ""} onChange={handleChange("endDate")} className="border rounded p-2 w-full" />
              </div>
            </div>
          </>
        );

      case "Weekly/Monthly Team Summary":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">Select Department or Project:</label>
                <select value={filters.scopeType ?? ""} onChange={handleChange("scopeType")} className="border rounded p-2">
                  <option value="">Select</option>
                  <option value="department">Department</option>
                  <option value="project">Project</option>
                </select>
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">{scopeLabel}</label>
                <select value={filters.scopeId ?? ""} onChange={handleChange("scopeId")} className="border rounded p-2">
                  <option value="">Select</option>
                  {scopeOptions.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">Start Date</label>
                <input type="date" value={filters.startDate ?? ""} onChange={handleChange("startDate")} className="border rounded p-2 w-full" />
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">End Date</label>
                <input type="date" value={filters.endDate ?? ""} onChange={handleChange("endDate")} className="border rounded p-2 w-full" />
              </div>
            </div>
          </>
        );

      case "Logged Time per Project/Department":
        return (
          <>
            <div className="flex flex-wrap gap-4 mb-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">Select Department or Project:</label>
                <select value={filters.scopeType ?? ""} onChange={handleChange("scopeType")} className="border rounded p-2">
                  <option value="">Select</option>
                  <option value="department">Department</option>
                  <option value="project">Project</option>
                </select>
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1">{scopeLabel}</label>
                <select value={filters.scopeId ?? ""} onChange={handleChange("scopeId")} className="border rounded p-2">
                  <option value="">Select</option>
                  {scopeOptions.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">Start Date</label>
                <input type="date" value={filters.startDate ?? ""} onChange={handleChange("startDate")} className="border rounded p-2 w-full" />
              </div>
              <div className="flex flex-col flex-1 min-w-[150px]">
                <label className="font-small mb-1 block">End Date</label>
                <input type="date" value={filters.endDate ?? ""} onChange={handleChange("endDate")} className="border rounded p-2 w-full" />
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
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Filters</h2>
      <ul className="list-disc pl-6 mb-4 space-y-2">
        {[
          "Task Completion Report",
          "Weekly/Monthly Team Summary",
          "Logged Time per Project/Department",
        ].map((report) => (
          <li key={report} className="flex items-center space-x-2">
            <input
              type="checkbox"
              id={report}
              checked={selectedReport === report}
              onChange={() => {
                if (selectedReport === report) {
                  setSelectedReport("");
                  setFilters({});
                  setReportData(null);
                } else {
                  setSelectedReport(report);
                  setFilters({});
                  setReportData(null);
                }
              }}
            />
            <label
              htmlFor={report}
              className={`cursor-pointer ${
                selectedReport === report ? "font-bold text-blue-600" : ""
              }`}
            >
              {report}
            </label>
          </li>
        ))}
      </ul>

      {/* Render dynamic fields */}
      <div>{renderDynamicFields()}</div>

      {/* View and Export Buttons */}
      <div className="flex items-center gap-4 mt-4 justify-between">
  <button
    type="button"
    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    onClick={handleViewReport}
  >
    View Report
  </button>

  <div className="flex items-center gap-4 ml-auto">
    <label className="flex items-center space-x-2 font-medium">
      <span>Export as</span>
      <select
        className="border rounded p-2"
        value={exportFormat}
        onChange={(e) => setExportFormat(e.target.value as "excel" | "pdf")}
      >
        <option value="excel">Excel</option>
        <option value="pdf">PDF</option>
      </select>
    </label>

    <button
      type="button"
      className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
      onClick={handleExport}
    >
      Export
    </button>
    </div>
  </div>


      {/* Report Preview */}
      {reportData && (
        <div className="mt-6 bg-gray-50 p-4 rounded border">
          <h3 className="font-semibold mb-2">Report Preview</h3>
          <pre className="overflow-auto text-sm">{JSON.stringify(reportData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Reports;
