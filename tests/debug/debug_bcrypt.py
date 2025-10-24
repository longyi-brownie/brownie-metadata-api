#!/usr/bin/env python3
"""Minimal script to debug bcrypt issues."""

print("=== BCrypt Debug Script ===")
print()

# Test 1: Check bcrypt installation
print("1. Testing bcrypt installation...")
try:
    import bcrypt
    print("   ✅ bcrypt imported successfully")
    print(f"   Version: {bcrypt.__version__}")
    print(f"   About: {getattr(bcrypt, '__about__', 'Not available')}")
except ImportError as e:
    print(f"   ❌ bcrypt import failed: {e}")
    exit(1)
except Exception as e:
    print(f"   ❌ bcrypt error: {e}")

# Test 2: Check passlib installation
print("\n2. Testing passlib installation...")
try:
    from passlib.context import CryptContext
    print("   ✅ passlib imported successfully")
except ImportError as e:
    print(f"   ❌ passlib import failed: {e}")
    exit(1)
except Exception as e:
    print(f"   ❌ passlib error: {e}")

# Test 3: Test basic bcrypt functionality
print("\n3. Testing basic bcrypt functionality...")
try:
    password = "test123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    print(f"   ✅ Basic bcrypt hash created: {hashed[:20]}...")

    # Test verification
    is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed)
    print(f"   ✅ Password verification: {is_valid}")
except Exception as e:
    print(f"   ❌ Basic bcrypt failed: {e}")

# Test 4: Test passlib with bcrypt
print("\n4. Testing passlib with bcrypt...")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password = "test123"
    hashed = pwd_context.hash(password)
    print(f"   ✅ Passlib hash created: {hashed[:20]}...")

    # Test verification
    is_valid = pwd_context.verify(password, hashed)
    print(f"   ✅ Passlib verification: {is_valid}")
except Exception as e:
    print(f"   ❌ Passlib bcrypt failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error details: {str(e)}")

# Test 5: Test with different password lengths
print("\n5. Testing different password lengths...")
test_passwords = [
    "test123",  # Short
    "testpassword123",  # Medium
    "a" * 50,  # 50 chars
    "a" * 72,  # 72 chars (bcrypt limit)
    "a" * 100,  # 100 chars (over limit)
]

for pwd in test_passwords:
    try:
        hashed = pwd_context.hash(pwd)
        verified = pwd_context.verify(pwd, hashed)
        print(f"   ✅ Password length {len(pwd)}: {verified}")
    except Exception as e:
        print(f"   ❌ Password length {len(pwd)}: {e}")

print("\n=== Debug Complete ===")
