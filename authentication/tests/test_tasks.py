# authentication/tests/test_tasks.py
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from celery import current_app

from ..tasks import (
    send_welcome_email,
    send_password_reset_email,
    cleanup_expired_tokens,
    send_login_notification,
    update_user_activity,
    sync_user_profile,
)

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AuthenticationTasksTestCase(TestCase):
    """Test cases for authentication-related Celery tasks"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_send_welcome_email_success(self):
        """Test welcome email sending success"""
        result = send_welcome_email(self.user.id)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn("Welcome", email.subject)
        self.assertIn(self.user.first_name, email.body)
        self.assertEqual(email.to, [self.user.email])

    def test_send_welcome_email_nonexistent_user(self):
        """Test welcome email with non-existent user"""
        result = send_welcome_email(99999)

        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    @patch("authentication.tasks.send_mail")
    def test_send_welcome_email_failure(self, mock_send_mail):
        """Test welcome email sending failure"""
        mock_send_mail.side_effect = Exception("Email service error")

        result = send_welcome_email(self.user.id)

        self.assertFalse(result)

    def test_send_password_reset_email_success(self):
        """Test password reset email sending success"""
        reset_token = "test-reset-token-123"

        result = send_password_reset_email(self.user.id, reset_token)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn("Password Reset", email.subject)
        self.assertIn(reset_token, email.body)
        self.assertEqual(email.to, [self.user.email])

    def test_send_password_reset_email_nonexistent_user(self):
        """Test password reset email with non-existent user"""
        result = send_password_reset_email(99999, "token")

        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_cleanup_expired_tokens_success(self):
        """Test expired tokens cleanup success"""
        # This would typically clean up JWT tokens or session tokens
        # Mock the cleanup process
        with patch("authentication.tasks.OutstandingToken") as mock_token:
            mock_queryset = MagicMock()
            mock_token.objects.filter.return_value = mock_queryset
            mock_queryset.delete.return_value = (5, {})  # 5 tokens deleted

            result = cleanup_expired_tokens()

            self.assertTrue(result)
            mock_token.objects.filter.assert_called_once()
            mock_queryset.delete.assert_called_once()

    def test_cleanup_expired_tokens_no_tokens(self):
        """Test expired tokens cleanup with no expired tokens"""
        with patch("authentication.tasks.OutstandingToken") as mock_token:
            mock_queryset = MagicMock()
            mock_token.objects.filter.return_value = mock_queryset
            mock_queryset.delete.return_value = (0, {})  # No tokens deleted

            result = cleanup_expired_tokens()

            self.assertTrue(result)

    def test_send_login_notification_success(self):
        """Test login notification sending success"""
        login_info = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 Test Browser",
            "location": "Test City, Test Country",
        }

        result = send_login_notification(self.user.id, login_info)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn("Login Alert", email.subject)
        self.assertIn(login_info["ip_address"], email.body)
        self.assertEqual(email.to, [self.user.email])

    def test_send_login_notification_disabled_user(self):
        """Test login notification for disabled user"""
        self.user.is_active = False
        self.user.save()

        result = send_login_notification(self.user.id, {})

        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_update_user_activity_success(self):
        """Test user activity update success"""
        activity_data = {
            "last_login_ip": "192.168.1.1",
            "login_count": 5,
            "last_activity": timezone.now().isoformat(),
        }

        result = update_user_activity(self.user.id, activity_data)

        self.assertTrue(result)

        # Refresh user from database
        self.user.refresh_from_db()

        # Check if profile was updated (assuming UserProfile model exists)
        # This would depend on your specific implementation

    def test_update_user_activity_nonexistent_user(self):
        """Test user activity update with non-existent user"""
        result = update_user_activity(99999, {})

        self.assertFalse(result)

    def test_sync_user_profile_success(self):
        """Test user profile synchronization success"""
        profile_data = {
            "bio": "Updated bio",
            "website": "https://example.com",
            "social_links": {
                "twitter": "https://twitter.com/testuser",
                "github": "https://github.com/testuser",
            },
        }

        with patch("authentication.tasks.UserProfile") as mock_profile:
            mock_profile_instance = MagicMock()
            mock_profile.objects.get_or_create.return_value = (
                mock_profile_instance,
                True,
            )

            result = sync_user_profile(self.user.id, profile_data)

            self.assertTrue(result)
            mock_profile.objects.get_or_create.assert_called_once()

    @patch("authentication.tasks.requests")
    def test_sync_user_profile_with_external_service(self, mock_requests):
        """Test user profile sync with external service"""
        # Mock external API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "External bio",
        }
        mock_requests.get.return_value = mock_response

        result = sync_user_profile(self.user.id, {"external_sync": True})

        self.assertTrue(result)
        mock_requests.get.assert_called_once()

    @patch("authentication.tasks.requests")
    def test_sync_user_profile_external_failure(self, mock_requests):
        """Test user profile sync with external service failure"""
        mock_requests.get.side_effect = Exception("API Error")

        result = sync_user_profile(self.user.id, {"external_sync": True})

        self.assertFalse(result)


class AuthenticationTaskIntegrationTestCase(TestCase):
    """Integration tests for authentication task workflows"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_user_registration_workflow(self):
        """Test complete user registration workflow"""
        # Simulate user registration workflow

        # 1. Send welcome email
        welcome_result = send_welcome_email(self.user.id)
        self.assertTrue(welcome_result)

        # 2. Update user activity
        activity_data = {
            "registration_ip": "192.168.1.1",
            "registration_date": timezone.now().isoformat(),
        }
        activity_result = update_user_activity(self.user.id, activity_data)
        self.assertTrue(activity_result)

        # 3. Sync user profile
        profile_data = {"bio": "New user bio", "onboarding_completed": False}
        sync_result = sync_user_profile(self.user.id, profile_data)
        self.assertTrue(sync_result)

        # Check that welcome email was sent
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_password_reset_workflow(self):
        """Test password reset workflow"""
        reset_token = "secure-reset-token-123"

        # Send password reset email
        result = send_password_reset_email(self.user.id, reset_token)
        self.assertTrue(result)

        # Update activity to track reset request
        activity_data = {
            "password_reset_requested": timezone.now().isoformat(),
            "reset_token": reset_token,
        }
        activity_result = update_user_activity(self.user.id, activity_data)
        self.assertTrue(activity_result)

        # Check that reset email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password Reset", mail.outbox[0].subject)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_login_monitoring_workflow(self):
        """Test login monitoring workflow"""
        login_info = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test Browser",
            "location": "New York, USA",
            "suspicious": False,
        }

        # Send login notification
        notification_result = send_login_notification(self.user.id, login_info)
        self.assertTrue(notification_result)

        # Update user activity
        activity_data = {
            "last_login_ip": login_info["ip_address"],
            "last_login_time": timezone.now().isoformat(),
            "login_count": 1,
        }
        activity_result = update_user_activity(self.user.id, activity_data)
        self.assertTrue(activity_result)

        # Check that login notification was sent
        self.assertEqual(len(mail.outbox), 1)


class AuthenticationTaskErrorHandlingTestCase(TestCase):
    """Test error handling in authentication tasks"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("authentication.tasks.logger")
    def test_task_error_logging(self, mock_logger):
        """Test that tasks log errors appropriately"""
        # Test with non-existent user
        send_welcome_email(99999)

        # Verify error was logged
        mock_logger.error.assert_called()

    def test_task_resilience_to_database_errors(self):
        """Test task resilience to database errors"""
        with patch("authentication.tasks.User.objects.get") as mock_get:
            mock_get.side_effect = Exception("Database connection error")

            result = send_welcome_email(self.user.id)
            self.assertFalse(result)

    def test_task_resilience_to_email_errors(self):
        """Test task resilience to email service errors"""
        with patch("authentication.tasks.send_mail") as mock_send:
            mock_send.side_effect = Exception("SMTP server error")

            result = send_welcome_email(self.user.id)
            self.assertFalse(result)


class AuthenticationCeleryConfigurationTestCase(TestCase):
    """Test Celery configuration for authentication tasks"""

    def test_authentication_tasks_discovery(self):
        """Test that authentication tasks are discovered"""
        registered_tasks = list(current_app.tasks.keys())

        auth_tasks = [
            "authentication.tasks.send_welcome_email",
            "authentication.tasks.send_password_reset_email",
            "authentication.tasks.cleanup_expired_tokens",
            "authentication.tasks.send_login_notification",
        ]

        for task_name in auth_tasks:
            self.assertIn(task_name, registered_tasks)

    def test_authentication_task_routing(self):
        """Test that authentication tasks are routed to auth queue"""
        routes = current_app.conf.task_routes
        self.assertIn("authentication.tasks.*", routes)
        self.assertEqual(routes["authentication.tasks.*"]["queue"], "auth")

    def test_task_retry_configuration(self):
        """Test that tasks have proper retry configuration"""
        # Test that tasks inherit global retry settings
        self.assertEqual(current_app.conf.task_default_retry_delay, 60)
        self.assertEqual(current_app.conf.task_max_retries, 3)


class AuthenticationTaskPerformanceTestCase(TestCase):
    """Test performance of authentication tasks"""

    def setUp(self):
        """Set up test data"""
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                password="testpass123",
            )
            self.users.append(user)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_bulk_email_sending_performance(self):
        """Test performance of sending emails to multiple users"""
        import time

        start_time = time.time()

        # Send welcome emails to all users
        for user in self.users:
            send_welcome_email(user.id)

        execution_time = time.time() - start_time

        # Should complete within reasonable time (5 seconds for 10 emails)
        self.assertLess(execution_time, 5)

        # Check that all emails were sent
        self.assertEqual(len(mail.outbox), len(self.users))

    def test_token_cleanup_performance(self):
        """Test performance of token cleanup task"""
        import time

        start_time = time.time()

        with patch("authentication.tasks.OutstandingToken") as mock_token:
            mock_queryset = MagicMock()
            mock_token.objects.filter.return_value = mock_queryset
            mock_queryset.delete.return_value = (100, {})  # Simulate 100 tokens

            cleanup_expired_tokens()

        execution_time = time.time() - start_time

        # Should complete quickly even with many tokens
        self.assertLess(execution_time, 1)
