"""
Task logging utility for tracking background task executions
"""
from .. import db
from ..models.TaskLog import TaskLog
from datetime import datetime

def log_task(task_name, status, message, details=None, triggered_by='system'):
    """
    Log a task execution to the database
    
    Args:
        task_name: Name of the task (e.g., 'send_daily_reminders')
        status: Status of the task ('success', 'error', 'running')
        message: Human-readable message about the task
        details: Optional dictionary with additional details
        triggered_by: Who or what triggered the task (e.g., 'system', 'admin')
    """
    try:
        task_log = TaskLog(
            task_name=task_name,
            status=status,
            message=message,
            details=details or {},
            triggered_by=triggered_by
        )
        db.session.add(task_log)
        db.session.commit()
        print(f"[TaskLog] {task_name}: {status} - {message}")
    except Exception as e:
        print(f"[TaskLog] Error logging task {task_name}: {str(e)}")
        db.session.rollback()

def get_recent_task_logs(limit=50):
    """
    Get recent task logs
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of task log dictionaries
    """
    try:
        logs = TaskLog.query.order_by(TaskLog.created_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
    except Exception as e:
        print(f"[TaskLog] Error fetching logs: {str(e)}")
        return []

def clear_all_task_logs():
    """
    Deletes all task logs from the database.
    
    Returns:
        The number of logs cleared.
    """
    try:
        num_rows_deleted = db.session.query(TaskLog).delete()
        db.session.commit()
        print(f"[TaskLog] Cleared {num_rows_deleted} task logs.")
        return num_rows_deleted
    except Exception as e:
        print(f"[TaskLog] Error clearing logs: {str(e)}")
        db.session.rollback()
        raise e
