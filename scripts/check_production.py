#!/usr/bin/env python3
"""
Production Deployment Checker
Validates environment configuration for production deployment
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))


def check_production_environment():
    """Check production environment configuration"""

    print("🚀 Production Environment Checker")
    print("=" * 50)

    # Load production environment variables
    env_path = backend_dir / ".env.production"
    if not env_path.exists():
        print(f"❌ Production .env file not found at: {env_path}")
        print("💡 Create one from .env.example:")
        print(f"   cp {backend_dir}/.env.example {env_path}")
        return False

    # Load the production environment
    from dotenv import load_dotenv

    load_dotenv(env_path)

    print(f"✅ Production .env file found at: {env_path}")

    # Critical production checks
    critical_checks = []
    warning_checks = []

    # Security checks
    debug_mode = os.getenv("DEBUG", "True").lower() == "true"
    if debug_mode:
        critical_checks.append("❌ DEBUG is still True - must be False in production")
    else:
        print("✅ DEBUG is properly set to False")

    # Secret key check
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or secret_key == "your-production-secret-key-here":
        critical_checks.append("❌ SECRET_KEY not properly configured")
    elif "django-insecure" in secret_key:
        critical_checks.append(
            "❌ SECRET_KEY contains 'django-insecure' - use a production key"
        )
    else:
        print("✅ SECRET_KEY is properly configured")

    # HTTPS/Security settings checks
    security_settings = [
        ("SECURE_HSTS_SECONDS", "HTTPS Strict Transport Security"),
        ("SECURE_SSL_REDIRECT", "SSL redirect"),
        ("SESSION_COOKIE_SECURE", "Secure session cookies"),
        ("CSRF_COOKIE_SECURE", "Secure CSRF cookies"),
    ]

    for setting, description in security_settings:
        value = os.getenv(setting)
        if not value:
            warning_checks.append(f"⚠️  {setting} not set - {description} disabled")
        else:
            print(f"✅ {setting} configured for {description}")

    # Database check
    database_url = os.getenv("DATABASE_URL")
    if not database_url or "sqlite" in database_url:
        warning_checks.append(
            "⚠️  Using SQLite database - consider PostgreSQL for production"
        )
    else:
        print("✅ Production database configured")

    # Email backend check
    email_backend = os.getenv("EMAIL_BACKEND", "")
    if "console" in email_backend:
        warning_checks.append(
            "⚠️  Using console email backend - configure SMTP for production"
        )
    else:
        print("✅ Production email backend configured")

    # Cloudinary checks
    cloudinary_vars = [
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_PUBLIC_API_KEY",
        "CLOUDINARY_SECRET_API_KEY",
    ]
    missing_cloudinary = []
    for var in cloudinary_vars:
        if not os.getenv(var):
            missing_cloudinary.append(var)

    if missing_cloudinary:
        critical_checks.append(
            f"❌ Missing Cloudinary variables: {', '.join(missing_cloudinary)}"
        )
    else:
        print("✅ Cloudinary configuration complete")

    # CORS check
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if not cors_origins:
        warning_checks.append(
            "⚠️  CORS_ALLOWED_ORIGINS not set - configure for production domains"
        )
    else:
        print("✅ CORS origins configured")

    # Allowed hosts check
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
    if not allowed_hosts or "localhost" in allowed_hosts:
        warning_checks.append(
            "⚠️  ALLOWED_HOSTS contains localhost - update for production domains"
        )
    else:
        print("✅ ALLOWED_HOSTS configured for production")

    # Display results
    print("\n" + "=" * 50)

    if critical_checks:
        print("❌ CRITICAL ISSUES (Must fix before deployment):")
        for check in critical_checks:
            print(f"   {check}")

    if warning_checks:
        print("\n⚠️  WARNINGS (Recommended for production):")
        for check in warning_checks:
            print(f"   {check}")

    if not critical_checks and not warning_checks:
        print("✅ All production checks passed!")
        print("🚀 Ready for deployment!")
    elif not critical_checks:
        print("✅ No critical issues found")
        print("💡 Consider addressing warnings for optimal security")
    else:
        print("❌ Critical issues must be resolved before deployment")

    return len(critical_checks) == 0


def generate_production_secret_key():
    """Generate a new secret key for production"""
    try:
        from django.core.management.utils import get_random_secret_key

        return get_random_secret_key()
    except ImportError:
        import secrets
        import string

        chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
        return "".join(secrets.choice(chars) for _ in range(50))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate-key":
        key = generate_production_secret_key()
        print("🔑 Generated production SECRET_KEY:")
        print(key)
        print("\n💡 Add this to your .env.production file:")
        print(f"SECRET_KEY={key}")
    else:
        success = check_production_environment()
        if not success:
            print("\n💡 Usage:")
            print(
                "  python check_production.py                # Check production config"
            )
            print(
                "  python check_production.py --generate-key # Generate new secret key"
            )
        sys.exit(0 if success else 1)
