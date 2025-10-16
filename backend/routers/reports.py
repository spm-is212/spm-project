from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.utils.security import get_current_user
from backend.schemas.report_schemas import (
    TaskCompletionRequest,
    TaskCompletionResponse,
    TeamSummaryRequest,
    TeamSummaryResponse,
    LoggedTimeRequest,
    LoggedTimeResponse
)
from backend.utils.report_util.task_completion_util import TaskCompletionReportGenerator
from backend.utils.report_util.team_summary_util import TeamSummaryReportGenerator
from backend.utils.report_util.logged_time_util import LoggedTimeReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/taskCompletion", response_model=TaskCompletionResponse)
def generate_task_completion_report(
    request: TaskCompletionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate task completion report filtered by project or staff member.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "project" or "staff"
    - scope_id: Project ID or Staff user UUID
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    - export_format: "json", "xlsx", or "csv" (currently only json is supported)

    **Returns**:
    - List of tasks with: title, priority, status, due_date, overdue flag
    - Overdue flag is true if due_date < today AND status != "COMPLETED"
    """
    # Check if user is in HR & admin department
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    try:
        generator = TaskCompletionReportGenerator()
        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating task completion report: {str(e)}"
        )


@router.post("/taskCompletion/export")
def export_task_completion_report(
    request: TaskCompletionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Export task completion report as Excel or PDF file.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "project" or "staff"
    - scope_id: Project ID or Staff user UUID
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    - export_format: "xlsx" or "pdf"

    **Returns**:
    - File download (Excel or PDF) with proper headers
    """
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    if request.export_format not in ["xlsx", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="export_format must be 'xlsx' or 'pdf'"
        )

    try:
        generator = TaskCompletionReportGenerator()

        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            start_date=request.start_date,
            end_date=request.end_date
        )

        if request.export_format == "xlsx":
            file_bytes = generator.generate_excel_bytes(
                scope_type=report.scope_type,
                scope_id=report.scope_id,
                scope_name=report.scope_name,
                start_date=request.start_date,
                end_date=request.end_date,
                tasks=report.tasks
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"task_completion_report_{request.scope_type}_{request.start_date}.xlsx"
        else:  # pdf
            file_bytes = generator.generate_pdf_bytes(
                scope_type=report.scope_type,
                scope_id=report.scope_id,
                scope_name=report.scope_name,
                start_date=request.start_date,
                end_date=request.end_date,
                tasks=report.tasks
            )
            media_type = "application/pdf"
            filename = f"task_completion_report_{request.scope_type}_{request.start_date}.pdf"

        # Return file as streaming response
        return StreamingResponse(
            file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting task completion report: {str(e)}"
        )


@router.post("/teamSummary", response_model=TeamSummaryResponse)
def generate_team_summary_report(
    request: TeamSummaryRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate team summary report showing task counts by status per staff member.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "department" or "project"
    - scope_id: Department name or Project ID
    - time_frame: "weekly" or "monthly"
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)

    **Returns**:
    - Staff summaries with task counts: Blocked, In Progress, Completed, Overdue
    """
    # Check if user is in HR & admin department
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    try:
        generator = TeamSummaryReportGenerator()
        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            time_frame=request.time_frame,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating team summary report: {str(e)}"
        )


@router.post("/teamSummary/export")
def export_team_summary_report(
    request: TeamSummaryRequest,
    user: dict = Depends(get_current_user)
):
    """
    Export team summary report as Excel or PDF file.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "department" or "project"
    - scope_id: Department name or Project ID
    - time_frame: "weekly" or "monthly"
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    - export_format: "xlsx" or "pdf"

    **Returns**:
    - File download (Excel or PDF) with proper headers
    """
    # Check if user is in HR & admin department
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    # Validate export format
    if request.export_format not in ["xlsx", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="export_format must be 'xlsx' or 'pdf'"
        )

    try:
        generator = TeamSummaryReportGenerator()

        # Get report data
        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            time_frame=request.time_frame,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Generate file based on format
        if request.export_format == "xlsx":
            file_bytes = generator.generate_excel_bytes(
                scope_type=report.scope_type,
                scope_name=report.scope_name,
                time_frame=report.time_frame,
                start_date=request.start_date,
                end_date=request.end_date,
                staff_summaries=report.staff_summaries
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"team_summary_report_{request.scope_type}_{request.start_date}.xlsx"
        else:  # pdf
            file_bytes = generator.generate_pdf_bytes(
                scope_type=report.scope_type,
                scope_name=report.scope_name,
                time_frame=report.time_frame,
                start_date=request.start_date,
                end_date=request.end_date,
                staff_summaries=report.staff_summaries
            )
            media_type = "application/pdf"
            filename = f"team_summary_report_{request.scope_type}_{request.start_date}.pdf"

        # Return file as streaming response
        return StreamingResponse(
            file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting team summary report: {str(e)}"
        )


@router.post("/loggedTime", response_model=LoggedTimeResponse)
def generate_logged_time_report(
    request: LoggedTimeRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate logged time report showing time logged per user and task.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "department" or "project"
    - scope_id: Department name or Project ID
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)

    **Returns**:
    - Time entries with: staff_name, task_title, time_log (hrs), status, due_date, overdue
    """
    # Check if user is in HR & admin department
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    try:
        generator = LoggedTimeReportGenerator()
        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating logged time report: {str(e)}"
        )


@router.post("/loggedTime/export")
def export_logged_time_report(
    request: LoggedTimeRequest,
    user: dict = Depends(get_current_user)
):
    """
    Export logged time report as Excel or PDF file.

    **Access**: HR & admin department only

    **Filters**:
    - scope_type: "department" or "project"
    - scope_id: Department name or Project ID
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    - export_format: "xlsx" or "pdf"

    **Returns**:
    - File download (Excel or PDF) with proper headers
    """
    # Check if user is in HR & admin department
    user_departments = user.get("departments", [])
    has_access = any(dept.lower() == "hr & admin" for dept in user_departments)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only HR & admin department users can access reports."
        )

    # Validate export format
    if request.export_format not in ["xlsx", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="export_format must be 'xlsx' or 'pdf'"
        )

    try:
        generator = LoggedTimeReportGenerator()

        # Get report data
        report = generator.generate_report(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Generate file based on format
        if request.export_format == "xlsx":
            file_bytes = generator.generate_excel_bytes(
                scope_type=report.scope_type,
                scope_name=report.scope_name,
                start_date=request.start_date,
                end_date=request.end_date,
                time_entries=report.time_entries,
                total_hours=report.total_hours
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"logged_time_report_{request.scope_type}_{request.start_date}.xlsx"
        else:  # pdf
            file_bytes = generator.generate_pdf_bytes(
                scope_type=report.scope_type,
                scope_name=report.scope_name,
                start_date=request.start_date,
                end_date=request.end_date,
                time_entries=report.time_entries,
                total_hours=report.total_hours
            )
            media_type = "application/pdf"
            filename = f"logged_time_report_{request.scope_type}_{request.start_date}.pdf"

        # Return file as streaming response
        return StreamingResponse(
            file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting logged time report: {str(e)}"
        )
