"""
Configuration Celery pour Modern Blog Platform

Ce module configure Celery pour la gestion des tâches asynchrones.
Utilise Redis comme broker et backend de résultats.
"""

import os
from celery import Celery
from django.conf import settings

# Configuration du module Django pour Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Création de l'instance Celery
app = Celery("core")

# Configuration depuis les paramètres Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Configuration explicite
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 heure
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 heure
    task_ignore_result=False,
    result_extended=True,
)

# Découverte automatique des tâches
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    """Tâche de débogage"""
    print(f"Request: {self.request!r}")

# Configuration for development
if os.environ.get("DJANGO_DEBUG", "True").lower() == "true":
    app.conf.update(
        task_always_eager=False,  # To test async tasks even in dev
        eager_propagates_exceptions=True,
    )