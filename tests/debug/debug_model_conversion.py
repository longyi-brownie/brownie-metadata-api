#!/usr/bin/env python3
"""Debug model conversion issues."""

import sys

sys.path.append("/Users/apple/Desktop/brownie-metadata-api")


from app.db import get_db
from app.models import User
from app.schemas import UserResponse


def debug_model_conversion():
    """Debug the model to schema conversion."""
    print("=== Debugging Model Conversion ===")

    # Get database session
    db = next(get_db())

    try:
        # Get user from database
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ User not found in database")
            return

        print(f"✅ User found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   org_id: {user.org_id}")
        print(f"   organization_id: {user.organization_id}")
        print(f"   team_id: {user.team_id}")
        print(f"   role: {user.role}")
        print(f"   role type: {type(user.role)}")

        # Try to convert to UserResponse
        print("\n--- Converting to UserResponse ---")
        try:
            user_response = UserResponse.model_validate(user)
            print("✅ UserResponse conversion successful!")
            print(f"   Response: {user_response}")
        except Exception as e:
            print(f"❌ UserResponse conversion failed: {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    debug_model_conversion()
