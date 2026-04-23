#!/usr/bin/env python3
"""
IEAP - Database Initialization Script

This script initializes the database with required data:
- Default admin user
- Default API key
- Initial system configuration
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    """Initialize the database with required data."""
    from sqlalchemy import text

    from config.settings import get_settings
    from database.connection import get_database_manager
    from database.models import APIKey, User
    from security.password import PasswordManager

    settings = get_settings()
    db = get_database_manager()
    password_manager = PasswordManager()

    print("=" * 60)
    print("IEAP Database Initialization")
    print("=" * 60)

    async with db.get_session() as session:
        # Check if admin user exists
        result = await session.execute(
            text("SELECT id FROM users WHERE username = 'admin'")
        )
        admin_exists = result.scalar_one_or_none()

        if not admin_exists:
            # Create admin user
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123!")
            hashed_password = password_manager.hash_password(admin_password)

            admin_user = User(
                username="admin",
                email="admin@ieap.local",
                hashed_password=hashed_password,
                full_name="System Administrator",
                role="admin",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(admin_user)
            await session.flush()

            # Create default API key for admin
            from security.tokens import TokenManager
            token_manager = TokenManager()

            api_key_value = token_manager.generate_api_key()
            api_key_hash = password_manager.hash_password(api_key_value)

            api_key = APIKey(
                user_id=admin_user.id,
                key_hash=api_key_hash,
                name="Default Admin Key",
                scopes=["read", "write", "admin"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(api_key)

            await session.commit()

            print("✓ Created admin user: admin")
            print(f"✓ Created API key: {api_key_value[:20]}...")
            print("")
            print("IMPORTANT: Save the API key securely. It won't be shown again!")
            print(f"Full API Key: {api_key_value}")
        else:
            print("✓ Admin user already exists, skipping creation")

        # Display database statistics
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar_one()

        result = await session.execute(text("SELECT COUNT(*) FROM ml_models"))
        model_count = result.scalar_one()

        print("")
        print("Database Statistics:")
        print(f"  - Users: {user_count}")
        print(f"  - ML Models: {model_count}")

    print("")
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
