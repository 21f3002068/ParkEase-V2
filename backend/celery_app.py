"""
Shared Celery app instance
"""
from celery import Celery, Task
from celery.schedules import crontab
import os

def create_celery_app():
    """
    Factory to create and configure a Celery app.
    This ensures that the app context is available for tasks.
    """
    # Create Celery instance
    celery = Celery('parkease')

    # Configure Celery
    celery.conf.update(
        broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        timezone='Asia/Kolkata',
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_always_eager=True,
        result_expires=3600,
        task_routes={
            'export_admin_users_csv': {'queue': 'default'},
            'daily_update': {'queue': 'default'},
            'monthly_report': {'queue': 'default'},
            'cleanup_old_csv_files': {'queue': 'default'},
            'send_daily_reminders': {'queue': 'default'},
            'system_health_check': {'queue': 'default'},
            'auto_release_expired_reservations': {'queue': 'default'},
        },
        beat_schedule={
            'daily-reminders': {
                'task': 'send_daily_reminders',
                # 'schedule': crontab(hour=18, minute=0),
                'schedule': 120.0,
            },
            'monthly-reports': {
                'task': 'send_monthly_reports',
                # 'schedule': crontab(day_of_month=1, hour=0, minute=0), 
                'schedule': 600.0,
            },
            'cleanup-csv': {
                'task': 'cleanup_old_csv_files',
                'schedule': crontab(hour=2, minute=0),
            },
            'auto-release-expired': {
                'task': 'auto_release_expired_reservations',
                'schedule': crontab(minute=0),
            },
            'payment-reminders': {
                'task': 'send_payment_reminders',
                # 'schedule': crontab(hour=10, minute=0), 
                'schedule': 120.0, 
            },
        }
    )

    # Create a custom Task class that sets up the Flask app context
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            from backend.app import create_app
            app = create_app()
            with app.app_context():
                return self.run(*args, **kwargs)

    # Set the custom task class as the default
    celery.Task = FlaskTask

    # Autodiscover tasks
    celery.autodiscover_tasks(['backend.app.tasks'])
    
    return celery

# Create the Celery app instance
celery_app = create_celery_app()