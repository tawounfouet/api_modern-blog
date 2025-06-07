from celery import shared_task

@shared_task(
    name="content.tasks.test_celery_task",
    ignore_result=False,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    track_started=True
)
def test_celery_task(self, name="Celery"):
    """
    A simple task to test if Celery is working correctly.
    This task logs a message and returns a success message with timestamp.
    """
    import logging
    from django.utils import timezone
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"Test Celery task started at {timezone.now()}")
    
    try:
        # Simulate some work
        time.sleep(2)
        
        current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        result_msg = f"Hello {name}! Task executed successfully at {current_time}"
        
        logger.info(f"Test Celery task completed with result: {result_msg}")
        
        return result_msg
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(exc=exc)