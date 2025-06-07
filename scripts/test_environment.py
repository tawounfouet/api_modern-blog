#!/usr/bin/env python3
"""
Environment Variables Test Script
Verifies that all environment variables are properly loaded from .env file
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.conf import settings
from dotenv import load_dotenv


def test_environment_variables():
    """Test that environment variables are properly loaded"""

    print("🔍 Environment Variables Test")
    print("=" * 50)

    # Load .env file
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env file found at: {env_path}")
    else:
        print(f"❌ .env file not found at: {env_path}")
        return False

    # Test basic Django settings
    tests = [
        ("DEBUG", settings.DEBUG, os.getenv("DEBUG", "True").lower() == "true"),
        (
            "SECRET_KEY",
            settings.SECRET_KEY[:20] + "...",
            (
                "Loaded from environment"
                if settings.SECRET_KEY
                != "django-insecure-6dyg600)3^65dn&3ohn$ls&kzis-(^s*5%swdcgnxy90gy=+1h"
                else "Using default"
            ),
        ),
        ("ALLOWED_HOSTS", settings.ALLOWED_HOSTS, "From environment"),
    ]

    # Test Cloudinary settings
    cloudinary_tests = [
        ("CLOUDINARY_CLOUD_NAME", settings.CLOUDINARY_CLOUD_NAME, "From environment"),
        (
            "CLOUDINARY_PUBLIC_API_KEY",
            settings.CLOUDINARY_PUBLIC_API_KEY,
            "From environment",
        ),
        (
            "CLOUDINARY_SECRET_API_KEY",
            "***"
            + (
                settings.CLOUDINARY_SECRET_API_KEY[-4:]
                if settings.CLOUDINARY_SECRET_API_KEY
                else "None"
            ),
            "From environment",
        ),
    ]

    # Test JWT settings
    jwt_tests = [
        (
            "JWT_ACCESS_TOKEN_LIFETIME",
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            "From environment",
        ),
        (
            "JWT_REFRESH_TOKEN_LIFETIME",
            settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            "From environment",
        ),
    ]

    print("\n📋 Django Configuration:")
    print("-" * 30)
    for name, value, source in tests:
        print(f"{name}: {value} ({source})")

    print("\n☁️ Cloudinary Configuration:")
    print("-" * 30)
    for name, value, source in cloudinary_tests:
        if value:
            print(f"✅ {name}: {value} ({source})")
        else:
            print(f"❌ {name}: Not set")

    print("\n🔐 JWT Configuration:")
    print("-" * 30)
    for name, value, source in jwt_tests:
        print(f"{name}: {value} ({source})")

    print("\n🌐 CORS Configuration:")
    print("-" * 30)
    print(f"CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
    if hasattr(settings, "CORS_ALLOWED_ORIGINS"):
        print(f"CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")

    print("\n📧 Email Configuration:")
    print("-" * 30)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")

    # Check for missing critical environment variables
    missing_vars = []
    critical_vars = [
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_PUBLIC_API_KEY",
        "CLOUDINARY_SECRET_API_KEY",
    ]

    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"\n⚠️ Missing critical environment variables:")
        for var in missing_vars:
            print(f"  • {var}")
        return False

    print(f"\n✅ All critical environment variables are set!")
    return True


if __name__ == "__main__":
    success = test_environment_variables()
    sys.exit(0 if success else 1)
