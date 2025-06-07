#!/usr/bin/env python3
"""
Test script to validate Celery setup and Redis connection
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings
from celery import Celery
import redis


def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis Connection...")
    print("=" * 50)

    try:
        # Get Redis URL from settings
        redis_url = settings.CELERY_BROKER_URL
        print(f"Redis URL: {redis_url}")

        # For local testing, try localhost connection
        if "redis:6379" in redis_url:
            # Try local Redis first
            local_redis_url = redis_url.replace("redis:6379", "localhost:6380")
            print(f"Trying local Redis: {local_redis_url}")

            try:
                r = redis.from_url(local_redis_url)
                r.ping()
                print("✅ Local Redis connection successful!")
                return True
            except:
                print("❌ Local Redis not available, will use Docker Redis")

        # Try original URL
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful!")
        return True

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_celery_configuration():
    """Test Celery configuration"""
    print("\n🔍 Testing Celery Configuration...")
    print("=" * 50)

    try:
        from core.celery import app

        # Test basic configuration
        print(f"✅ Celery app created: {app.main}")
        print(f"✅ Broker URL: {app.conf.broker_url}")
        print(f"✅ Result backend: {app.conf.result_backend}")
        print(f"✅ Task serializer: {app.conf.task_serializer}")
        print(f"✅ Accept content: {app.conf.accept_content}")

        # Test task routing
        if hasattr(app.conf, "task_routes"):
            print("✅ Task routing configured:")
            for pattern, route in app.conf.task_routes.items():
                print(f"   {pattern} -> {route}")

        # Test beat schedule
        if hasattr(app.conf, "beat_schedule"):
            print("✅ Beat schedule configured:")
            for task_name, config in app.conf.beat_schedule.items():
                print(f"   {task_name}: {config['task']}")

        return True

    except Exception as e:
        print(f"❌ Celery configuration failed: {e}")
        return False


def test_task_imports():
    """Test that all tasks can be imported"""
    print("\n🔍 Testing Task Imports...")
    print("=" * 50)

    tasks_to_test = [
        # Authentication tasks
        ("authentication.tasks", "send_verification_email"),
        ("authentication.tasks", "send_password_reset_email"),
        ("authentication.tasks", "cleanup_expired_tokens"),
        # Content tasks
        ("content.tasks", "process_article_content"),
        ("content.tasks", "optimize_image"),
        ("content.tasks", "process_podcast_audio"),
        ("content.tasks", "send_content_notification"),
        ("content.tasks", "update_view_count"),
        ("content.tasks", "cleanup_old_comments"),
        ("content.tasks", "generate_sitemap"),
        ("content.tasks", "sync_social_metrics"),
        # Helper tasks
        ("helpers.tasks", "cleanup_temp_files"),
        ("helpers.tasks", "backup_database"),
        ("helpers.tasks", "optimize_database"),
        ("helpers.tasks", "generate_analytics_report"),
        ("helpers.tasks", "monitor_system_health"),
        ("helpers.tasks", "publish_scheduled_content"),
    ]

    success_count = 0
    total_count = len(tasks_to_test)

    for module_name, task_name in tasks_to_test:
        try:
            module = __import__(module_name, fromlist=[task_name])
            task = getattr(module, task_name)
            print(f"✅ {module_name}.{task_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}.{task_name}: {e}")

    print(f"\n📊 Task Import Results: {success_count}/{total_count} successful")
    return success_count == total_count


def test_simple_task():
    """Test a simple task execution"""
    print("\n🔍 Testing Simple Task Execution...")
    print("=" * 50)

    try:
        from helpers.tasks import cleanup_temp_files

        # Try to call the task
        print("Testing cleanup_temp_files task...")
        result = cleanup_temp_files.delay()
        print(f"✅ Task queued successfully! Task ID: {result.id}")
        print("⚠️  Note: Task execution requires Redis and Celery worker to be running")
        return True

    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        return False


def test_django_integration():
    """Test Django-Celery integration"""
    print("\n🔍 Testing Django-Celery Integration...")
    print("=" * 50)

    try:
        # Test that Celery is properly initialized in Django
        from django.apps import apps

        print("✅ Django apps loaded successfully")

        # Test that we can import Django models in tasks
        from django.contrib.auth.models import User

        print("✅ Django models accessible")

        # Test settings integration
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Time zone: {settings.TIME_ZONE}")
        print(f"✅ Celery timezone: {settings.CELERY_TIMEZONE}")

        return True

    except Exception as e:
        print(f"❌ Django integration failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Celery Setup Validation")
    print("=" * 60)

    tests = [
        ("Redis Connection", test_redis_connection),
        ("Celery Configuration", test_celery_configuration),
        ("Task Imports", test_task_imports),
        ("Django Integration", test_django_integration),
        ("Simple Task", test_simple_task),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! Celery setup is ready for production.")
        print("\n📝 Next steps:")
        print("   1. Start Redis: docker-compose up redis -d")
        print("   2. Start Celery worker: python manage.py celery_worker")
        print("   3. Start Celery beat: python manage.py celery_beat")
        print("   4. Start Flower: flower --broker=redis://localhost:6380/0")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure Redis is running")
        print("   - Check .env file configuration")
        print("   - Verify all dependencies are installed")


if __name__ == "__main__":
    main()
