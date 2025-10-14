from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta  # handles monthly recurrences cleanly
from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskCreate, MAIN_TASK_PARENT_ID
from backend.utils.notif_util.notification_service import NotificationService
from backend.utils.task_crud.constants import (
   TASKS_TABLE_NAME,
   TITLE_FIELD,
   DESCRIPTION_FIELD,
   DUE_DATE_FIELD,
   STATUS_FIELD,
   PRIORITY_FIELD,
   OWNER_USER_ID_FIELD,
   ASSIGNEE_IDS_FIELD,
   PARENT_ID_FIELD,
   COMMENTS_FIELD,
   ATTACHMENTS_FIELD,
   IS_ARCHIVED_FIELD,
   FILE_URL_FIELD,
   MAIN_TASK_KEY,
   SUBTASKS_RESPONSE_KEY,
   TASK_ID_FIELD,
   DEFAULT_COMMENTS,
   DEFAULT_ATTACHMENTS,
   DEFAULT_IS_ARCHIVED,
)


class TaskCreator:
   """
   Task creation utilities
   """


   def __init__(self):
       self.crud = SupabaseCRUD()
       self.table_name = TASKS_TABLE_NAME


   def _generate_recurrence_dates(self, start_date: datetime, rule: str, interval: int, end_date: Optional[datetime]) -> List[datetime]:
       """Generate due dates based on recurrence rule."""
       if not rule:
           return [start_date]
       if not interval or interval <= 0:
           interval = 1


       dates = []
       current = start_date
       limit = end_date or start_date


       while current <= limit:
           dates.append(current)
           if rule == "DAILY":
               current += timedelta(days=interval)
           elif rule == "WEEKLY":
               current += timedelta(weeks=interval)
           elif rule == "MONTHLY":
               current += relativedelta(months=interval)
           else:
               break  # Unsupported rule
       return dates


   def create_task_with_subtasks(self, user_id: str, main_task: TaskCreate, subtasks: Optional[List[TaskCreate]] = None) -> Dict[str, Any]:
       assignee_ids = list(main_task.assignee_ids) if main_task.assignee_ids else []
       if user_id not in assignee_ids:
           assignee_ids.append(user_id)


       main_task_dict = {
           TITLE_FIELD: main_task.title,
           DESCRIPTION_FIELD: main_task.description,
           DUE_DATE_FIELD: main_task.due_date.isoformat(),
           STATUS_FIELD: main_task.status.value,
           PRIORITY_FIELD: main_task.priority,
           OWNER_USER_ID_FIELD: user_id,
           ASSIGNEE_IDS_FIELD: assignee_ids,
           PARENT_ID_FIELD: MAIN_TASK_PARENT_ID,
           COMMENTS_FIELD: DEFAULT_COMMENTS,
           ATTACHMENTS_FIELD: DEFAULT_ATTACHMENTS,
           IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED,
           "recurrence_rule": main_task.recurrence_rule.value if main_task.recurrence_rule else None,
           "recurrence_interval": main_task.recurrence_interval,
           "recurrence_end_date": main_task.recurrence_end_date.isoformat() if main_task.recurrence_end_date else None,
       }


       if main_task.project_id is not None:
           main_task_dict["project_id"] = main_task.project_id


       if hasattr(main_task, 'file_url') and main_task.file_url:
           main_task_dict[FILE_URL_FIELD] = main_task.file_url


       created_main_task = self.crud.insert(self.table_name, main_task_dict)
       result = {MAIN_TASK_KEY: created_main_task, SUBTASKS_RESPONSE_KEY: []}


       if main_task.recurrence_rule:
           recurrence_dates = self._generate_recurrence_dates(
               start_date=main_task.due_date,
               rule=main_task.recurrence_rule.value,
               interval=main_task.recurrence_interval or 1,
               end_date=main_task.recurrence_end_date,
           )


           for due_date in recurrence_dates[1:]:
               instance_dict = {**main_task_dict}
               instance_dict[DUE_DATE_FIELD] = due_date.isoformat()
               instance_dict[PARENT_ID_FIELD] = created_main_task[TASK_ID_FIELD]
               self.crud.insert(self.table_name, instance_dict)


       if subtasks:
           for subtask_data in subtasks:
               subtask_assignee_ids = list(subtask_data.assignee_ids) if subtask_data.assignee_ids else []
               if user_id not in subtask_assignee_ids:
                   subtask_assignee_ids.append(user_id)


               subtask_dict = {
                   TITLE_FIELD: subtask_data.title,
                   DESCRIPTION_FIELD: subtask_data.description,
                   DUE_DATE_FIELD: subtask_data.due_date.isoformat(),
                   STATUS_FIELD: subtask_data.status.value,
                   PRIORITY_FIELD: subtask_data.priority,
                   OWNER_USER_ID_FIELD: user_id,
                   ASSIGNEE_IDS_FIELD: subtask_assignee_ids,
                   PARENT_ID_FIELD: created_main_task[TASK_ID_FIELD],
                   COMMENTS_FIELD: DEFAULT_COMMENTS,
                   ATTACHMENTS_FIELD: DEFAULT_ATTACHMENTS,
                   IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED,
                   "recurrence_rule": subtask_data.recurrence_rule.value if subtask_data.recurrence_rule else None,
                   "recurrence_interval": subtask_data.recurrence_interval,
                   "recurrence_end_date": subtask_data.recurrence_end_date.isoformat() if subtask_data.recurrence_end_date else None,
               }


               if subtask_data.project_id is not None:
                   subtask_dict["project_id"] = subtask_data.project_id


               if hasattr(subtask_data, 'file_url') and subtask_data.file_url:
                   subtask_dict[FILE_URL_FIELD] = subtask_data.file_url


               created_subtask = self.crud.insert(self.table_name, subtask_dict)
               result[SUBTASKS_RESPONSE_KEY].append(created_subtask)
              
       notification_service = NotificationService()


       # Collect all unique assignees (main + subtasks)
       receivers = set(main_task.assignee_ids or [])
       if subtasks:
           for sub in subtasks:
               if sub.assignee_ids:
                   receivers.update(sub.assignee_ids)


       # prevent self-notify (optional)
       receivers.discard(user_id)


       hardcoded_email = "reneefongsh@gmail.com"  # change this to your address


       notification_service.notify_task_event(
           sender_id=user_id,
           action="created",
           task=created_main_task,
           receivers=list(receivers),
           email_receivers=[hardcoded_email]
       )


       return result


