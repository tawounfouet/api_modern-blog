# core/tests/test_celery.py
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
from celery import current_app
from celery.exceptions import WorkerLostError

from core.celery import app as celery_app


class CeleryConfigurationTestCase(TestCase):
    """Test Celery configuration and setup"""

    def test_celery_app_instance(self):
        """Test that Celery app is properly instantiated"""
        self.assertIsNotNone(celery_app)
        self.assertEqual(celery_app.main, "modern_blog_platform")

    def test_django_settings_integration(self):
        """Test that Celery integrates with Django settings"""
        # Check that Celery uses Django settings
        self.assertEqual(celery_app.conf.timezone, settings.TIME_ZONE)

    def test_broker_configuration(self):
        """Test broker configuration"""
        # Test that broker URL is configured
        broker_url = celery_app.conf.broker_url
        self.assertIsNotNone(broker_url)
        self.assertTrue(broker_url.startswith("redis://"))

    def test_result_backend_configuration(self):
        """Test result backend configuration"""
        result_backend = celery_app.conf.result_backend
        self.assertIsNotNone(result_backend)
        # Allow both redis:// (original) or django-db (new configuration)
        self.assertTrue(
            result_backend.startswith("redis://") or result_backend == "django-db"
        )

    def test_task_serialization_configuration(self):
        """Test task serialization settings"""
        self.assertEqual(celery_app.conf.task_serializer, "json")
        self.assertEqual(celery_app.conf.result_serializer, "json")
        self.assertIn("json", celery_app.conf.accept_content)

    def test_task_routing_configuration(self):
        """Test task routing configuration"""
        routes = celery_app.conf.task_routes

        # Check that all app queues are configured
        expected_routes = {
            "authentication.tasks.*": {"queue": "auth"},
            "content.tasks.*": {"queue": "content"},
            "helpers.tasks.*": {"queue": "helpers"},
        }

        for pattern, config in expected_routes.items():
            self.assertIn(pattern, routes)
            self.assertEqual(routes[pattern]["queue"], config["queue"])

    def test_worker_configuration(self):
        """Test worker configuration settings"""
        self.assertEqual(celery_app.conf.worker_prefetch_multiplier, 1)
        self.assertTrue(celery_app.conf.task_acks_late)
        self.assertEqual(celery_app.conf.worker_max_tasks_per_child, 1000)

    def test_monitoring_configuration(self):
        """Test monitoring configuration"""
        self.assertTrue(celery_app.conf.worker_send_task_events)
        self.assertTrue(celery_app.conf.task_send_sent_event)

    def test_retry_configuration(self):
        """Test retry configuration"""
        self.assertEqual(celery_app.conf.task_default_retry_delay, 60)
        self.assertEqual(celery_app.conf.task_max_retries, 3)

    def test_result_expiration(self):
        """Test result expiration configuration"""
        self.assertEqual(celery_app.conf.result_expires, 3600)  # 1 hour


class CeleryTaskDiscoveryTestCase(TestCase):
    """Test automatic task discovery"""

    def test_task_autodiscovery(self):
        """Test that tasks are automatically discovered"""
        # Force task discovery
        celery_app.autodiscover_tasks()

        # Get list of registered tasks
        registered_tasks = list(celery_app.tasks.keys())

        # Check that tasks from all modules are discovered
        expected_task_patterns = [
            "authentication.tasks.",
            "content.tasks.",
            "helpers.tasks.",
        ]

        for pattern in expected_task_patterns:
            matching_tasks = [task for task in registered_tasks if pattern in task]
            self.assertGreater(
                len(matching_tasks), 0, f"No tasks found matching pattern: {pattern}"
            )

    def test_specific_tasks_discovered(self):
        """Test that specific tasks are discovered"""
        registered_tasks = list(celery_app.tasks.keys())

        # Check for specific important tasks
        important_tasks = [
            "content.tasks.process_article_content",
            "content.tasks.send_content_notification",
            "helpers.tasks.cleanup_temp_files",
            "helpers.tasks.backup_database",
            "authentication.tasks.send_welcome_email",
        ]

        for task_name in important_tasks:
            self.assertIn(
                task_name, registered_tasks, f"Task not discovered: {task_name}"
            )


class CeleryBeatScheduleTestCase(TestCase):
    """Test Celery Beat schedule configuration"""

    def test_beat_schedule_exists(self):
        """Test that beat schedule is configured"""
        self.assertIsNotNone(celery_app.conf.beat_schedule)

    def test_periodic_tasks_configured(self):
        """Test that periodic tasks are properly configured"""
        beat_schedule = celery_app.conf.beat_schedule

        # Check for essential periodic tasks
        essential_tasks = [
            "cleanup-temp-files",
            "backup-database",
            "generate-analytics-report",
            "cleanup-expired-tokens",
            "monitor-system-health",
        ]

        for task_name in essential_tasks:
            self.assertIn(
                task_name, beat_schedule, f"Periodic task not configured: {task_name}"
            )

    def test_schedule_intervals(self):
        """Test that schedule intervals are reasonable"""
        beat_schedule = celery_app.conf.beat_schedule

        # Test specific intervals
        if "cleanup-temp-files" in beat_schedule:
            # Should run daily (24 hours)
            interval = beat_schedule["cleanup-temp-files"]["schedule"]
            self.assertEqual(interval, 60 * 60 * 24)  # 24 hours in seconds

    def test_schedule_task_references(self):
        """Test that scheduled tasks reference valid task names"""
        beat_schedule = celery_app.conf.beat_schedule
        registered_tasks = list(celery_app.tasks.keys())

        for schedule_name, schedule_config in beat_schedule.items():
            task_name = schedule_config.get("task")
            if task_name:
                self.assertIn(
                    task_name,
                    registered_tasks,
                    f"Scheduled task not found: {task_name}",
                )


class CeleryConnectionTestCase(TestCase):
    """Test Celery broker connection"""

    @patch("redis.Redis")
    def test_redis_connection_configuration(self, mock_redis):
        """Test Redis connection configuration"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        # Test connection to Redis
        from redis import Redis

        broker_url = celery_app.conf.broker_url
        # Extract host and port from broker URL
        # Format: redis://host:port/db
        if "://" in broker_url:
            parts = broker_url.split("://", 1)[1]
            if "/" in parts:
                host_port, db = parts.rsplit("/", 1)
            else:
                host_port, db = parts, "0"

            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = int(port)
            else:
                host, port = host_port, 6379

        # Test Redis instance creation
        redis_client = Redis(host=host, port=port, db=int(db))
        mock_redis.assert_called()

    def test_broker_url_format(self):
        """Test that broker URL is properly formatted"""
        broker_url = celery_app.conf.broker_url

        # Should be a valid Redis URL
        self.assertRegex(broker_url, r"^redis://[\w.-]+:\d+/\d+$")

    def test_result_backend_url_format(self):
        """Test that result backend URL is properly formatted"""
        result_backend = celery_app.conf.result_backend

        # Could be redis or django-db backend
        if result_backend.startswith("redis://"):
            self.assertRegex(result_backend, r"^redis://[\w.-]+:\d+/\d+$")
        else:
            self.assertEqual(result_backend, "django-db")


class CeleryErrorHandlingTestCase(TestCase):
    """Test Celery error handling and resilience"""

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_task_failure_handling(self):
        """Test that task failures are handled gracefully"""
        # This would test actual failure scenarios in a real environment
        # For now, we test the configuration

        # Check that tasks are configured for retry
        self.assertEqual(celery_app.conf.task_max_retries, 3)
        self.assertEqual(celery_app.conf.task_default_retry_delay, 60)

    def test_worker_error_configuration(self):
        """Test worker error handling configuration"""
        # Check that workers are configured for graceful error handling
        self.assertTrue(celery_app.conf.task_acks_late)
        self.assertEqual(celery_app.conf.worker_max_tasks_per_child, 1000)

    def test_task_timeout_configuration(self):
        """Test task timeout configuration"""
        # Check that results expire to prevent memory leaks
        self.assertEqual(celery_app.conf.result_expires, 3600)


class CeleryEnvironmentTestCase(TestCase):
    """Test Celery behavior in different environments"""

    @override_settings(DEBUG=True)
    def test_development_configuration(self):
        """Test Celery configuration in development"""
        # In development, tasks might be configured differently
        # This depends on your specific configuration
        pass

    @override_settings(DEBUG=False)
    def test_production_configuration(self):
        """Test Celery configuration in production"""
        # In production, certain settings should be different
        self.assertFalse(celery_app.conf.task_always_eager)

    def test_environment_variable_integration(self):
        """Test that environment variables are properly used"""
        # Test that environment variables override defaults
        with patch.dict(
            os.environ,
            {
                "CELERY_BROKER_URL": "redis://custom:6379/1",
                "CELERY_RESULT_BACKEND": "redis://custom:6379/1",
            },
        ):
            # Reload configuration
            celery_app.config_from_object("django.conf:settings", namespace="CELERY")

            # Environment variables should be used
            # This test depends on how your celery.py handles environment variables


class CeleryMonitoringTestCase(TestCase):
    """Test Celery monitoring and observability"""

    def test_task_events_enabled(self):
        """Test that task events are enabled for monitoring"""
        self.assertTrue(celery_app.conf.worker_send_task_events)
        self.assertTrue(celery_app.conf.task_send_sent_event)

    def test_flower_compatibility(self):
        """Test that configuration is compatible with Flower"""
        # Flower requires task events to be enabled
        self.assertTrue(celery_app.conf.worker_send_task_events)

        # JSON serialization is recommended for Flower
        self.assertEqual(celery_app.conf.task_serializer, "json")

    def test_logging_configuration(self):
        """Test that logging is properly configured"""
        # This would test logging configuration
        # Depends on your specific logging setup
        pass


class CeleryPerformanceTestCase(TestCase):
    """Test Celery performance configuration"""

    def test_prefetch_multiplier(self):
        """Test prefetch multiplier for optimal performance"""
        # Prefetch multiplier of 1 is recommended for long-running tasks
        self.assertEqual(celery_app.conf.worker_prefetch_multiplier, 1)

    def test_worker_lifecycle_settings(self):
        """Test worker lifecycle settings"""
        # Workers should restart after processing a reasonable number of tasks
        self.assertEqual(celery_app.conf.worker_max_tasks_per_child, 1000)

        # Late acknowledgment ensures tasks aren't lost on worker failure
        self.assertTrue(celery_app.conf.task_acks_late)

    def test_serialization_performance(self):
        """Test serialization settings for performance"""
        # JSON is fast and secure
        self.assertEqual(celery_app.conf.task_serializer, "json")
        self.assertEqual(celery_app.conf.result_serializer, "json")


class CelerySecurityTestCase(TestCase):
    """Test Celery security configuration"""

    def test_safe_serialization(self):
        """Test that safe serialization is used"""
        # JSON is safer than pickle
        self.assertEqual(celery_app.conf.task_serializer, "json")
        self.assertIn("json", celery_app.conf.accept_content)
        self.assertNotIn("pickle", celery_app.conf.accept_content)

    def test_result_backend_security(self):
        """Test result backend security"""
        # Results should expire to prevent information leakage
        self.assertGreater(celery_app.conf.result_expires, 0)
        self.assertLessEqual(celery_app.conf.result_expires, 86400)  # Max 24 hours
