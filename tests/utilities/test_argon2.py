#!/usr/bin/env python3
"""Test argon2 implementation."""

print("=== Argon2 Test ===")

try:
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    # Test password hashing
    password = "testpassword123"
    print(f"Testing password: {password}")

    # Hash password
    hashed = pwd_context.hash(password)
    print(f"✅ Hash created: {hashed[:50]}...")

    # Verify password
    is_valid = pwd_context.verify(password, hashed)
    print(f"✅ Verification: {is_valid}")

    # Test with different password
    wrong_password = "wrongpassword"
    is_invalid = pwd_context.verify(wrong_password, hashed)
    print(f"✅ Wrong password rejected: {not is_invalid}")

    print("\n✅ Argon2 is working perfectly!")

except Exception as e:
    print(f"❌ Argon2 failed: {e}")
    import traceback

    traceback.print_exc()
