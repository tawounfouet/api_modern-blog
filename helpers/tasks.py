# helpers/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import connection
from datetime import timedelta
import os
import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)


@shared_task
def cleanup_temp_files():
    """
    Clean up temporary files and uploads
    """
    try:
        cleaned_files = 0
        cleaned_size = 0

        # Clean up temporary podcast uploads
        temp_podcast_dir = os.path.join(settings.MEDIA_ROOT, "temp_podcasts")
        if os.path.exists(temp_podcast_dir):
            for filename in os.listdir(temp_podcast_dir):
                file_path = os.path.join(temp_podcast_dir, filename)
                file_age = timezone.now().timestamp() - os.path.getctime(file_path)

                # Remove files older than 24 hours
                if file_age > 86400:  # 24 hours in seconds
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        cleaned_size += file_size
                    except OSError as e:
                        logger.warning(f"Could not remove temp file {file_path}: {e}")

        # Clean up Django sessions older than 7 days
        call_command("clearsessions")

        # Clean up old log files if they exist
        log_dir = getattr(settings, "LOG_DIR", None)
        if log_dir and os.path.exists(log_dir):
            cutoff_time = timezone.now().timestamp() - (7 * 86400)  # 7 days
            for log_file in os.listdir(log_dir):
                if log_file.endswith(".log"):
                    log_path = os.path.join(log_dir, log_file)
                    if os.path.getctime(log_path) < cutoff_time:
                        try:
                            file_size = os.path.getsize(log_path)
                            os.remove(log_path)
                            cleaned_files += 1
                            cleaned_size += file_size
                        except OSError as e:
                            logger.warning(f"Could not remove log file {log_path}: {e}")

        logger.info(
            f"Cleanup completed: {cleaned_files} files removed, {cleaned_size} bytes freed"
        )

        return {
            "status": "success",
            "files_cleaned": cleaned_files,
            "bytes_freed": cleaned_size,
        }

    except Exception as exc:
        logger.error(f"Error during file cleanup: {str(exc)}")
        raise


@shared_task
def backup_database():
    """
    Create a database backup
    """
    try:
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        # Check database backend
        db_engine = settings.DATABASES["default"]["ENGINE"]

        if "postgresql" in db_engine:
            # PostgreSQL backup
            backup_file = os.path.join(backup_dir, f"backup_postgres_{timestamp}.sql")
            db_config = settings.DATABASES["default"]

            pg_dump_cmd = [
                "pg_dump",
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', '5432')}",
                f"--username={db_config['USER']}",
                f"--dbname={db_config['NAME']}",
                "--no-password",
                "--verbose",
                "--file",
                backup_file,
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["PASSWORD"]

            result = subprocess.run(
                pg_dump_cmd, env=env, capture_output=True, text=True
            )

            if result.returncode == 0:
                backup_size = os.path.getsize(backup_file)
                logger.info(
                    f"PostgreSQL backup created: {backup_file} ({backup_size} bytes)"
                )
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                raise Exception(f"PostgreSQL backup failed: {result.stderr}")

        elif "sqlite" in db_engine:
            # SQLite backup
            db_path = settings.DATABASES["default"]["NAME"]
            backup_file = os.path.join(backup_dir, f"backup_sqlite_{timestamp}.db")

            shutil.copy2(db_path, backup_file)
            backup_size = os.path.getsize(backup_file)
            logger.info(f"SQLite backup created: {backup_file} ({backup_size} bytes)")

        else:
            raise ValueError(f"Unsupported database engine: {db_engine}")

        # Clean up old backups (keep only last 7)
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("backup_")]
        backup_files.sort(reverse=True)

        for old_backup in backup_files[7:]:  # Keep only 7 most recent
            old_backup_path = os.path.join(backup_dir, old_backup)
            try:
                os.remove(old_backup_path)
                logger.info(f"Removed old backup: {old_backup}")
            except OSError as e:
                logger.warning(f"Could not remove old backup {old_backup}: {e}")

        return {
            "status": "success",
            "backup_file": backup_file,
            "backup_size": backup_size,
        }

    except Exception as exc:
        logger.error(f"Error creating database backup: {str(exc)}")
        raise


@shared_task
def optimize_database():
    """
    Optimize database performance
    """
    try:
        with connection.cursor() as cursor:
            db_engine = settings.DATABASES["default"]["ENGINE"]

            if "postgresql" in db_engine:
                # PostgreSQL optimization
                cursor.execute("VACUUM ANALYZE;")
                cursor.execute(
                    "REINDEX DATABASE %s;" % settings.DATABASES["default"]["NAME"]
                )
                logger.info("PostgreSQL database optimized (VACUUM ANALYZE + REINDEX)")

            elif "sqlite" in db_engine:
                # SQLite optimization
                cursor.execute("VACUUM;")
                cursor.execute("PRAGMA optimize;")
                logger.info("SQLite database optimized (VACUUM + PRAGMA optimize)")

        return {"status": "success", "database_optimized": True}

    except Exception as exc:
        logger.error(f"Error optimizing database: {str(exc)}")
        raise


@shared_task
def generate_analytics_report():
    """
    Generate weekly analytics report
    """
    try:
        from content.models import Post, Podcast, Video, Comment
        from authentication.models import User

        # Get date range (last week)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        # Collect analytics data
        analytics = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "content": {
                "new_posts": Post.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                "new_podcasts": Podcast.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                "new_videos": Video.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                "new_comments": Comment.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
            },
            "users": {
                "new_registrations": User.objects.filter(
                    date_joined__range=[start_date, end_date]
                ).count(),
                "total_users": User.objects.count(),
            },
            "engagement": {
                "total_posts": Post.objects.filter(is_published=True).count(),
                "total_podcasts": Podcast.objects.filter(is_published=True).count(),
                "total_videos": Video.objects.filter(is_published=True).count(),
                "total_comments": Comment.objects.count(),
            },
        }

        # Log analytics summary
        logger.info(
            f"Weekly analytics: {analytics['content']['new_posts']} new posts, "
            f"{analytics['content']['new_podcasts']} new podcasts, "
            f"{analytics['users']['new_registrations']} new users"
        )

        # In production, you'd save this to a file or send it via email
        return {"status": "success", "analytics": analytics}

    except Exception as exc:
        logger.error(f"Error generating analytics report: {str(exc)}")
        raise


@shared_task
def check_system_health():
    """
    Perform system health checks
    """
    try:
        health_status = {"timestamp": timezone.now().isoformat(), "checks": {}}

        # Database connectivity check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "response_time": "fast",
                }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Redis connectivity check (Celery broker)
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", 10)
            redis_test = cache.get("health_check")
            if redis_test == "ok":
                health_status["checks"]["redis"] = {"status": "healthy"}
            else:
                health_status["checks"]["redis"] = {
                    "status": "unhealthy",
                    "error": "Cache test failed",
                }
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

        # Disk space check
        try:
            disk_usage = shutil.disk_usage(settings.BASE_DIR)
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            health_status["checks"]["disk_space"] = {
                "status": "healthy" if usage_percent < 90 else "warning",
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "usage_percent": round(usage_percent, 2),
            }
        except Exception as e:
            health_status["checks"]["disk_space"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Media directory check
        try:
            media_dir = settings.MEDIA_ROOT
            if os.path.exists(media_dir) and os.access(media_dir, os.W_OK):
                health_status["checks"]["media_storage"] = {
                    "status": "healthy",
                    "writable": True,
                }
            else:
                health_status["checks"]["media_storage"] = {
                    "status": "unhealthy",
                    "writable": False,
                }
        except Exception as e:
            health_status["checks"]["media_storage"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Overall health assessment
        unhealthy_checks = [
            name
            for name, check in health_status["checks"].items()
            if check["status"] == "unhealthy"
        ]

        overall_status = "unhealthy" if unhealthy_checks else "healthy"
        health_status["overall_status"] = overall_status

        if unhealthy_checks:
            logger.warning(f"System health check failed: {unhealthy_checks}")
        else:
            logger.info("System health check passed")

        return {"status": "success", "health": health_status}

    except Exception as exc:
        logger.error(f"Error during system health check: {str(exc)}")
        raise


@shared_task
def process_scheduled_content():
    """
    Publish scheduled content that should now be live
    """
    try:
        from content.models import Post, Podcast, Video

        now = timezone.now()
        published_count = 0

        # Check for posts scheduled to be published
        scheduled_posts = Post.objects.filter(published_at__lte=now, is_published=False)

        for post in scheduled_posts:
            post.is_published = True
            post.save(update_fields=["is_published"])
            published_count += 1

            # Trigger content notification
            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="post", content_id=post.id, notification_type="published"
            )

        # Check for podcasts scheduled to be published
        scheduled_podcasts = Podcast.objects.filter(
            published_at__lte=now,
            is_published=False,
            is_processed=True,  # Only publish if audio is processed
        )

        for podcast in scheduled_podcasts:
            podcast.is_published = True
            podcast.save(update_fields=["is_published"])
            published_count += 1

            # Trigger content notification
            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="podcast",
                content_id=podcast.id,
                notification_type="published",
            )

        # Check for videos scheduled to be published
        scheduled_videos = Video.objects.filter(
            published_at__lte=now, is_published=False
        )

        for video in scheduled_videos:
            video.is_published = True
            video.save(update_fields=["is_published"])
            published_count += 1

            # Trigger content notification
            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="video", content_id=video.id, notification_type="published"
            )

        logger.info(f"Published {published_count} scheduled content items")

        return {"status": "success", "published_count": published_count}

    except Exception as exc:
        logger.error(f"Error processing scheduled content: {str(exc)}")
        raise


@shared_task
def monitor_system_health():
    """
    Monitor system health metrics and alert if issues detected
    """
    try:
        import psutil
        import os
        from django.db import connection

        health_status = {
            "timestamp": timezone.now().isoformat(),
            "status": "healthy",
            "metrics": {},
            "alerts": [],
        }

        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status["metrics"]["cpu_percent"] = cpu_percent
        if cpu_percent > 80:
            health_status["alerts"].append(f"High CPU usage: {cpu_percent}%")
            health_status["status"] = "warning"

        # Check memory usage
        memory = psutil.virtual_memory()
        health_status["metrics"]["memory_percent"] = memory.percent
        if memory.percent > 85:
            health_status["alerts"].append(f"High memory usage: {memory.percent}%")
            health_status["status"] = "warning"

        # Check disk usage
        disk = psutil.disk_usage("/")
        health_status["metrics"]["disk_percent"] = (disk.used / disk.total) * 100
        if (disk.used / disk.total) * 100 > 90:
            health_status["alerts"].append("Low disk space")
            health_status["status"] = "critical"

        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["metrics"]["database"] = "connected"
        except Exception as db_exc:
            health_status["alerts"].append(f"Database connection error: {str(db_exc)}")
            health_status["status"] = "critical"

        # Check Redis connection
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", timeout=10)
            health_status["metrics"]["redis"] = "connected"
        except Exception as redis_exc:
            health_status["alerts"].append(f"Redis connection error: {str(redis_exc)}")
            health_status["status"] = "warning"

        logger.info(f"System health check completed: {health_status['status']}")

        # In production, you'd send alerts to monitoring systems
        if health_status["alerts"]:
            logger.warning(f"Health alerts: {health_status['alerts']}")

        return health_status

    except ImportError:
        logger.warning("psutil not installed, skipping system metrics")
        return {"status": "partial", "message": "System metrics unavailable"}
    except Exception as exc:
        logger.error(f"Error checking system health: {str(exc)}")
        raise


@shared_task
def publish_scheduled_content():
    """
    Publish content that is scheduled for release
    """
    try:
        from content.models import Post, Podcast, Video

        current_time = timezone.now()
        published_count = 0

        # Publish scheduled posts
        scheduled_posts = Post.objects.filter(
            status="scheduled", scheduled_publish_date__lte=current_time
        )

        for post in scheduled_posts:
            post.status = "published"
            post.published_date = current_time
            post.save(update_fields=["status", "published_date"])
            published_count += 1

            # Trigger content notification
            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="post", content_id=post.id, notification_type="published"
            )

        # Publish scheduled podcasts
        scheduled_podcasts = Podcast.objects.filter(
            status="scheduled", scheduled_publish_date__lte=current_time
        )

        for podcast in scheduled_podcasts:
            podcast.status = "published"
            podcast.published_date = current_time
            podcast.save(update_fields=["status", "published_date"])
            published_count += 1

            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="podcast",
                content_id=podcast.id,
                notification_type="published",
            )

        # Publish scheduled videos
        scheduled_videos = Video.objects.filter(
            status="scheduled", scheduled_publish_date__lte=current_time
        )

        for video in scheduled_videos:
            video.status = "published"
            video.published_date = current_time
            video.save(update_fields=["status", "published_date"])
            published_count += 1

            from content.tasks import send_content_notification

            send_content_notification.delay(
                content_type="video", content_id=video.id, notification_type="published"
            )

        logger.info(f"Published {published_count} scheduled content items")

        return {
            "status": "success",
            "published_count": published_count,
            "timestamp": current_time.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error publishing scheduled content: {str(exc)}")
        raise
