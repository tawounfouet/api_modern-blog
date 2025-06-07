# helpers/tests/test_tasks.py
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from celery import current_app
from celery.exceptions import Retry
from datetime import datetime, timedelta

from ..tasks import (
    cleanup_temp_files,
    backup_database,
    optimize_database,
    generate_analytics_report,
    monitor_system_health,
    send_admin_notification,
    publish_scheduled_content,
    sync_media_files,
    update_search_index,
    cleanup_old_logs,
)

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class HelpersTasksTestCase(TestCase):
    """Test cases for helper utility tasks"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("helpers.tasks.os.listdir")
    @patch("helpers.tasks.os.path.isfile")
    @patch("helpers.tasks.os.path.getmtime")
    @patch("helpers.tasks.os.remove")
    def test_cleanup_temp_files_success(
        self, mock_remove, mock_getmtime, mock_isfile, mock_listdir
    ):
        """Test temporary files cleanup task success"""
        # Mock file system
        mock_listdir.return_value = ["temp1.tmp", "temp2.tmp", "keep.txt"]
        mock_isfile.side_effect = lambda x: x.endswith(".tmp")
        # Mock old files (older than 24 hours)
        mock_getmtime.return_value = (datetime.now() - timedelta(hours=25)).timestamp()

        result = cleanup_temp_files()

        self.assertTrue(result)
        # Should try to remove temp files
        self.assertEqual(mock_remove.call_count, 2)

    @patch("helpers.tasks.os.listdir")
    @patch("helpers.tasks.logger")
    def test_cleanup_temp_files_directory_not_exist(self, mock_logger, mock_listdir):
        """Test cleanup when temp directory doesn't exist"""
        mock_listdir.side_effect = FileNotFoundError("Directory not found")

        result = cleanup_temp_files()

        self.assertTrue(result)  # Should handle gracefully
        mock_logger.info.assert_called()

    @patch("helpers.tasks.os.listdir")
    @patch("helpers.tasks.os.remove")
    @patch("helpers.tasks.logger")
    def test_cleanup_temp_files_permission_error(
        self, mock_logger, mock_remove, mock_listdir
    ):
        """Test cleanup with permission errors"""
        mock_listdir.return_value = ["temp1.tmp"]
        mock_remove.side_effect = PermissionError("Permission denied")

        result = cleanup_temp_files()

        self.assertTrue(result)  # Should handle gracefully
        mock_logger.warning.assert_called()

    @patch("helpers.tasks.subprocess.run")
    @patch("helpers.tasks.settings")
    def test_backup_database_sqlite_success(self, mock_settings, mock_subprocess):
        """Test database backup for SQLite success"""
        mock_settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "/path/to/db.sqlite3",
            }
        }
        mock_subprocess.return_value.returncode = 0

        result = backup_database()

        self.assertTrue(result)
        mock_subprocess.assert_called_once()

    @patch("helpers.tasks.subprocess.run")
    @patch("helpers.tasks.settings")
    def test_backup_database_postgres_success(self, mock_settings, mock_subprocess):
        """Test database backup for PostgreSQL success"""
        mock_settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "testdb",
                "USER": "testuser",
                "HOST": "localhost",
                "PORT": "5432",
            }
        }
        mock_subprocess.return_value.returncode = 0

        result = backup_database()

        self.assertTrue(result)
        mock_subprocess.assert_called_once()

    @patch("helpers.tasks.subprocess.run")
    @patch("helpers.tasks.settings")
    def test_backup_database_failure(self, mock_settings, mock_subprocess):
        """Test database backup failure"""
        mock_settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "/path/to/db.sqlite3",
            }
        }
        mock_subprocess.return_value.returncode = 1

        result = backup_database()

        self.assertFalse(result)

    @patch("helpers.tasks.connection")
    def test_optimize_database_success(self, mock_connection):
        """Test database optimization success"""
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        result = optimize_database()

        self.assertTrue(result)
        mock_cursor.execute.assert_called()

    @patch("helpers.tasks.connection")
    def test_optimize_database_failure(self, mock_connection):
        """Test database optimization failure"""
        mock_connection.cursor.side_effect = Exception("Database error")

        result = optimize_database()

        self.assertFalse(result)

    def test_generate_analytics_report_success(self):
        """Test analytics report generation success"""
        with patch("helpers.tasks.Post") as mock_post, patch(
            "helpers.tasks.Podcast"
        ) as mock_podcast, patch("helpers.tasks.Video") as mock_video, patch(
            "helpers.tasks.User"
        ) as mock_user:

            # Mock querysets
            mock_post.objects.filter.return_value.count.return_value = 10
            mock_podcast.objects.filter.return_value.count.return_value = 5
            mock_video.objects.filter.return_value.count.return_value = 3
            mock_user.objects.filter.return_value.count.return_value = 2

            mock_post.objects.filter.return_value.aggregate.return_value = {
                "total_views": 1000
            }

            result = generate_analytics_report()

            self.assertTrue(result)

    @patch("helpers.tasks.psutil")
    def test_monitor_system_health_success(self, mock_psutil):
        """Test system health monitoring success"""
        # Mock system metrics
        mock_psutil.cpu_percent.return_value = 45.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.disk_usage.return_value.percent = 70.0

        result = monitor_system_health()

        self.assertTrue(result)

    @patch("helpers.tasks.psutil")
    @patch("helpers.tasks.send_admin_notification")
    def test_monitor_system_health_high_usage(
        self, mock_send_notification, mock_psutil
    ):
        """Test system health monitoring with high resource usage"""
        # Mock high system usage
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.virtual_memory.return_value.percent = 95.0
        mock_psutil.disk_usage.return_value.percent = 95.0

        result = monitor_system_health()

        self.assertTrue(result)
        # Should send alert notification
        mock_send_notification.delay.assert_called()

    @patch("helpers.tasks.psutil")
    def test_monitor_system_health_failure(self, mock_psutil):
        """Test system health monitoring failure"""
        mock_psutil.cpu_percent.side_effect = Exception("System error")

        result = monitor_system_health()

        self.assertFalse(result)

    @patch("helpers.tasks.send_mail")
    def test_send_admin_notification_success(self, mock_send_mail):
        """Test admin notification sending success"""
        mock_send_mail.return_value = True

        result = send_admin_notification("Test Subject", "Test message")

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch("helpers.tasks.send_mail")
    def test_send_admin_notification_failure(self, mock_send_mail):
        """Test admin notification sending failure"""
        mock_send_mail.side_effect = Exception("Email error")

        result = send_admin_notification("Test Subject", "Test message")

        self.assertFalse(result)

    def test_publish_scheduled_content_success(self):
        """Test scheduled content publishing success"""
        with patch("helpers.tasks.Post") as mock_post, patch(
            "helpers.tasks.Podcast"
        ) as mock_podcast, patch("helpers.tasks.Video") as mock_video:

            # Mock scheduled content
            mock_scheduled_post = MagicMock()
            mock_scheduled_post.title = "Test Post"
            mock_post.objects.filter.return_value = [mock_scheduled_post]
            mock_podcast.objects.filter.return_value = []
            mock_video.objects.filter.return_value = []

            result = publish_scheduled_content()

            self.assertTrue(result)
            # Should mark content as published
            self.assertTrue(mock_scheduled_post.is_published)

    @patch("helpers.tasks.os.walk")
    @patch("helpers.tasks.CloudinaryService")
    def test_sync_media_files_success(self, mock_cloudinary, mock_walk):
        """Test media files synchronization success"""
        # Mock file system
        mock_walk.return_value = [("/media", [], ["image1.jpg", "image2.png"])]

        # Mock Cloudinary service
        mock_service = MagicMock()
        mock_cloudinary.return_value = mock_service
        mock_service.sync_file.return_value = True

        result = sync_media_files()

        self.assertTrue(result)

    @patch("helpers.tasks.call_command")
    def test_update_search_index_success(self, mock_call_command):
        """Test search index update success"""
        result = update_search_index()

        self.assertTrue(result)
        mock_call_command.assert_called_with("rebuild_index", "--noinput")

    @patch("helpers.tasks.call_command")
    def test_update_search_index_failure(self, mock_call_command):
        """Test search index update failure"""
        mock_call_command.side_effect = Exception("Index error")

        result = update_search_index()

        self.assertFalse(result)

    @patch("helpers.tasks.os.listdir")
    @patch("helpers.tasks.os.path.getmtime")
    @patch("helpers.tasks.os.remove")
    def test_cleanup_old_logs_success(self, mock_remove, mock_getmtime, mock_listdir):
        """Test old logs cleanup success"""
        # Mock log files
        mock_listdir.return_value = ["app.log", "celery.log", "old.log"]
        # Mock old files (older than 30 days)
        mock_getmtime.return_value = (datetime.now() - timedelta(days=31)).timestamp()

        result = cleanup_old_logs()

        self.assertTrue(result)
        # Should remove old log files
        self.assertEqual(mock_remove.call_count, 3)


class TaskPerformanceTestCase(TestCase):
    """Test task performance and optimization"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_task_execution_time(self):
        """Test that tasks execute within reasonable time limits"""
        import time

        # Test cleanup task performance
        start_time = time.time()
        result = cleanup_temp_files()
        execution_time = time.time() - start_time

        self.assertTrue(result)
        self.assertLess(execution_time, 30)  # Should complete within 30 seconds

    def test_task_memory_usage(self):
        """Test that tasks don't consume excessive memory"""
        import tracemalloc

        tracemalloc.start()

        # Run a task
        cleanup_temp_files()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory usage should be reasonable (less than 100MB)
        self.assertLess(peak / 1024 / 1024, 100)


class TaskRetryTestCase(TestCase):
    """Test task retry mechanisms"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("helpers.tasks.subprocess.run")
    def test_backup_database_retry_on_failure(self, mock_subprocess):
        """Test database backup retry on failure"""
        # First call fails, second succeeds
        mock_subprocess.side_effect = [
            MagicMock(returncode=1),  # Failure
            MagicMock(returncode=0),  # Success
        ]

        with patch.object(backup_database, "retry") as mock_retry:
            mock_retry.side_effect = Retry()

            with self.assertRaises(Retry):
                backup_database.apply()

    @patch("helpers.tasks.connection")
    def test_optimize_database_retry_on_exception(self, mock_connection):
        """Test database optimization retry on exception"""
        mock_connection.cursor.side_effect = Exception("Temporary database error")

        with patch.object(optimize_database, "retry") as mock_retry:
            mock_retry.side_effect = Retry()

            with self.assertRaises(Retry):
                optimize_database.apply()


class TaskSchedulingTestCase(TestCase):
    """Test task scheduling and beat configuration"""

    def test_beat_schedule_configuration(self):
        """Test that beat schedule is properly configured"""
        from django.conf import settings

        self.assertIsNotNone(settings.CELERY_BEAT_SCHEDULE)

        # Check that key tasks are scheduled
        schedule = settings.CELERY_BEAT_SCHEDULE
        self.assertIn("cleanup-temp-files", schedule)

    def test_periodic_task_intervals(self):
        """Test that periodic tasks have reasonable intervals"""
        from django.conf import settings

        schedule = settings.CELERY_BEAT_SCHEDULE

        # Daily cleanup should run every 24 hours
        cleanup_schedule = schedule.get("cleanup-temp-files", {}).get("schedule", 0)
        expected_daily = 60 * 60 * 24  # 24 hours in seconds
        self.assertEqual(cleanup_schedule, expected_daily)


class CeleryIntegrationTestCase(TestCase):
    """Integration tests for Celery task system"""

    def test_task_discovery_helpers(self):
        """Test that helper tasks are discovered"""
        registered_tasks = list(current_app.tasks.keys())

        helper_tasks = [
            "helpers.tasks.cleanup_temp_files",
            "helpers.tasks.backup_database",
            "helpers.tasks.optimize_database",
            "helpers.tasks.generate_analytics_report",
            "helpers.tasks.monitor_system_health",
        ]

        for task_name in helper_tasks:
            self.assertIn(task_name, registered_tasks)

    def test_task_routing_helpers(self):
        """Test that helper tasks are routed to correct queue"""
        routes = current_app.conf.task_routes
        self.assertIn("helpers.tasks.*", routes)
        self.assertEqual(routes["helpers.tasks.*"]["queue"], "helpers")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_task_chain_execution(self):
        """Test chaining multiple helper tasks"""
        # Chain: cleanup -> backup -> analytics
        with patch("helpers.tasks.os.listdir"), patch(
            "helpers.tasks.subprocess.run"
        ) as mock_subprocess, patch("helpers.tasks.Post") as mock_post:

            mock_subprocess.return_value.returncode = 0
            mock_post.objects.filter.return_value.count.return_value = 5
            mock_post.objects.filter.return_value.aggregate.return_value = {
                "total_views": 100
            }

            # Execute task chain
            cleanup_result = cleanup_temp_files()
            backup_result = backup_database()
            analytics_result = generate_analytics_report()

            self.assertTrue(cleanup_result)
            self.assertTrue(backup_result)
            self.assertTrue(analytics_result)
