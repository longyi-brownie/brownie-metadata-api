#!/usr/bin/env python3
"""Test enum conversion issue."""

import os
os.environ['METADATA_POSTGRES_DSN'] = "postgresql://brownie-fastapi-server@localhost:5432/brownie_metadata?sslmode=require&sslcert=../brownie-metadata-database/dev-certs/client.crt&sslkey=../brownie-metadata-database/dev-certs/client.key&sslrootcert=../brownie-metadata-database/dev-certs/ca.crt"

from app.db import get_db
from app.models import User
from app.schemas import UserResponse
from sqlalchemy.orm import Session

def test_enum_conversion():
    """Test enum conversion."""
    print("=== Testing Enum Conversion ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get user from database
        user = db.query(User).filter(User.email == 'test@example.com').first()
        if not user:
            print("❌ User not found in database")
            return
        
        print(f"✅ User found: {user.email}")
        print(f"   role: {user.role}")
        print(f"   role type: {type(user.role)}")
        print(f"   role value: {repr(user.role)}")
        
        # Try to convert to UserResponse
        print("\n--- Converting to UserResponse ---")
        try:
            user_response = UserResponse.model_validate(user)
            print("✅ UserResponse conversion successful!")
            print(f"   Response role: {user_response.role}")
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
    test_enum_conversion()
