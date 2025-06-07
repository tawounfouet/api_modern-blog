"""
Django management command to start Celery beat scheduler with monitoring
"""

import os
import signal
import subprocess
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Start Celery beat scheduler for periodic tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--loglevel",
            default="info",
            choices=["debug", "info", "warning", "error", "critical"],
            help="Logging level (default: info)",
        )
        parser.add_argument(
            "--pidfile",
            default="celerybeat.pid",
            help="Path to pidfile (default: celerybeat.pid)",
        )
        parser.add_argument(
            "--schedule",
            default="celerybeat-schedule",
            help="Path to schedule database (default: celerybeat-schedule)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Celery beat scheduler..."))

        # Build the celery beat command
        cmd = [
            "celery",
            "-A",
            "core",
            "beat",
            "--loglevel",
            options["loglevel"],
            "--pidfile",
            options["pidfile"],
            "--schedule",
            options["schedule"],
        ]

        self.stdout.write(f"Command: {' '.join(cmd)}")
        self.stdout.write(f"Log level: {options['loglevel']}")
        self.stdout.write(f"PID file: {options['pidfile']}")
        self.stdout.write(f"Schedule database: {options['schedule']}")

        try:
            # Clean up old pidfile if it exists
            if os.path.exists(options["pidfile"]):
                try:
                    os.remove(options["pidfile"])
                    self.stdout.write(f"Removed old pidfile: {options['pidfile']}")
                except OSError:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not remove old pidfile: {options['pidfile']}"
                        )
                    )

            # Start the beat process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            # Setup signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                self.stdout.write(
                    self.style.WARNING(
                        f"\nReceived signal {signum}, shutting down beat scheduler gracefully..."
                    )
                )
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    self.stdout.write(
                        self.style.ERROR(
                            "Beat scheduler did not shutdown gracefully, forcing termination..."
                        )
                    )
                    process.kill()

                # Clean up pidfile
                if os.path.exists(options["pidfile"]):
                    try:
                        os.remove(options["pidfile"])
                    except OSError:
                        pass

                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Stream output
            self.stdout.write(
                self.style.SUCCESS(
                    "Celery beat scheduler started successfully. Press Ctrl+C to stop."
                )
            )
            self.stdout.write("-" * 60)

            for line in iter(process.stdout.readline, ""):
                if line:
                    # Color-code log levels
                    if "[ERROR]" in line or "ERROR" in line:
                        self.stdout.write(self.style.ERROR(line.strip()))
                    elif "[WARNING]" in line or "WARNING" in line:
                        self.stdout.write(self.style.WARNING(line.strip()))
                    elif "Scheduler:" in line or "beat:" in line:
                        self.stdout.write(self.style.SUCCESS(line.strip()))
                    else:
                        self.stdout.write(line.strip())

            # Wait for process to complete
            return_code = process.wait()
            if return_code != 0:
                raise CommandError(
                    f"Celery beat scheduler exited with code {return_code}"
                )

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\nShutting down Celery beat scheduler...")
            )
            if process:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()

        except Exception as e:
            raise CommandError(f"Failed to start Celery beat scheduler: {e}")

        finally:
            # Clean up pidfile
            if os.path.exists(options["pidfile"]):
                try:
                    os.remove(options["pidfile"])
                    self.stdout.write(f"Cleaned up pidfile: {options['pidfile']}")
                except OSError:
                    pass

        self.stdout.write(self.style.SUCCESS("Celery beat scheduler stopped."))
