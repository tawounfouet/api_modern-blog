from celery import shared_task
from django_celery_results.models import TaskResult


@shared_task(bind=True, ignore_result=False)
def diagnostic_task(self):
    """A simple task to test Django-Celery-Results integration"""
    return {
        "status": "success",
        "message": "This result should be stored in the database",
        "task_id": self.request.id,
    }
