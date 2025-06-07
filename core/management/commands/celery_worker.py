"""
Django management command to start Celery worker with monitoring and graceful shutdown
"""

import os
import signal
import subprocess
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Start Celery worker with proper configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--concurrency",
            type=int,
            default=2,
            help="Number of concurrent worker processes (default: 2)",
        )
        parser.add_argument(
            "--loglevel",
            default="info",
            choices=["debug", "info", "warning", "error", "critical"],
            help="Logging level (default: info)",
        )
        parser.add_argument(
            "--queues",
            default="auth,content,helpers",
            help="Comma-separated list of queues to process (default: auth,content,helpers)",
        )
        parser.add_argument(
            "--max-tasks-per-child",
            type=int,
            default=1000,
            help="Maximum number of tasks a worker child process can execute (default: 1000)",
        )
        parser.add_argument(
            "--prefetch-multiplier",
            type=int,
            default=1,
            help="How many messages to prefetch at a time (default: 1)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Celery worker..."))

        # Build the celery command
        cmd = [
            "celery",
            "-A",
            "core",
            "worker",
            "--loglevel",
            options["loglevel"],
            "--concurrency",
            str(options["concurrency"]),
            "--queues",
            options["queues"],
            "--max-tasks-per-child",
            str(options["max_tasks_per_child"]),
            "--prefetch-multiplier",
            str(options["prefetch_multiplier"]),
        ]

        # Add development-specific options
        if settings.DEBUG:
            cmd.extend(["--pool", "solo"])  # Use solo pool for easier debugging

        self.stdout.write(f"Command: {' '.join(cmd)}")
        self.stdout.write(f"Processing queues: {options['queues']}")
        self.stdout.write(f"Concurrency: {options['concurrency']}")
        self.stdout.write(f"Log level: {options['loglevel']}")

        try:
            # Start the worker process
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
                        f"\nReceived signal {signum}, shutting down worker gracefully..."
                    )
                )
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    self.stdout.write(
                        self.style.ERROR(
                            "Worker did not shutdown gracefully, forcing termination..."
                        )
                    )
                    process.kill()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Stream output
            self.stdout.write(
                self.style.SUCCESS(
                    "Celery worker started successfully. Press Ctrl+C to stop."
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
                    elif "[INFO]" in line or "received task" in line:
                        self.stdout.write(self.style.SUCCESS(line.strip()))
                    else:
                        self.stdout.write(line.strip())

            # Wait for process to complete
            return_code = process.wait()
            if return_code != 0:
                raise CommandError(f"Celery worker exited with code {return_code}")

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nShutting down Celery worker..."))
            if process:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()

        except Exception as e:
            raise CommandError(f"Failed to start Celery worker: {e}")

        self.stdout.write(self.style.SUCCESS("Celery worker stopped."))
