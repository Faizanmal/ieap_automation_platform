#!/usr/bin/env python3
"""
IEAP - Generate Secret Keys Script

This script generates secure random keys for use in the application.
"""

import secrets


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "ieap") -> str:
    """Generate a secure API key with a prefix."""
    key = secrets.token_urlsafe(32)
    return f"{prefix}_{key}"


def generate_encryption_key() -> str:
    """Generate a Fernet encryption key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


def generate_password(length: int = 24) -> str:
    """Generate a strong random password."""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    """Generate all necessary secrets."""
    print("=" * 60)
    print("IEAP - Secret Key Generator")
    print("=" * 60)
    print("")

    print("# JWT Configuration")
    print(f"JWT_SECRET_KEY={generate_secret_key(64)}")
    print(f"JWT_REFRESH_SECRET_KEY={generate_secret_key(64)}")
    print("")

    print("# Encryption")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print("")

    print("# API Keys")
    print(f"INTERNAL_API_KEY={generate_api_key('ieap_internal')}")
    print(f"SERVICE_API_KEY={generate_api_key('ieap_service')}")
    print("")

    print("# Database")
    print(f"POSTGRES_PASSWORD={generate_password(24)}")
    print("")

    print("# Redis")
    print(f"REDIS_PASSWORD={generate_password(24)}")
    print("")

    print("# Admin User")
    print(f"ADMIN_PASSWORD={generate_password(16)}")
    print("")

    print("# Session")
    print(f"SESSION_SECRET={generate_secret_key(32)}")
    print("")

    print("=" * 60)
    print("Copy the values above to your .env file")
    print("NEVER commit these values to version control!")
    print("=" * 60)


if __name__ == "__main__":
    main()
