"""Quick test script for auth endpoints."""
import requests

BASE = 'http://localhost:8000/api/auth'

# 1. Register
print("=== REGISTER ===")
r = requests.post(f'{BASE}/register/', json={
    'email': 'testuser@example.com',
    'username': 'testuser',
    'password': 'TestPass123!',
    'role': 'listener',
})
print(f"Status: {r.status_code}")
print(f"Body: {r.json()}")
print()

# 2. Login BEFORE verification (should fail)
print("=== LOGIN (before verify - should fail) ===")
r = requests.post(f'{BASE}/login/', json={
    'email': 'testuser@example.com',
    'password': 'TestPass123!',
})
print(f"Status: {r.status_code}")
print(f"Body: {r.json()}")
print()

# 3. Verify OTP - read code from DB
import os, sys, django
sys.path.insert(0, r'D:\Study\PeopleLink\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunora.settings')
django.setup()

from users.models import OTP, User
user = User.objects.get(email='testuser@example.com')
otp = OTP.objects.filter(user=user, is_used=False).first()
print(f"=== VERIFY OTP (code: {otp.code}) ===")

r = requests.post(f'{BASE}/verify-otp/', json={
    'email': 'testuser@example.com',
    'otp': otp.code,
})
print(f"Status: {r.status_code}")
print(f"Body: {r.json()}")
print()

# 4. Login AFTER verification (should succeed)
print("=== LOGIN (after verify - should succeed) ===")
r = requests.post(f'{BASE}/login/', json={
    'email': 'testuser@example.com',
    'password': 'TestPass123!',
})
print(f"Status: {r.status_code}")
data = r.json()
print(f"Body: {data}")
print()

# Check password is hashed in DB
user.refresh_from_db()
print(f"=== DB CHECK ===")
print(f"Password hash: {user.password[:50]}...")
print(f"Role: {user.role}")
print(f"Is verified: {user.is_verified}")
print()

# 5. Logout
if r.status_code == 200:
    access = data['tokens']['access']
    refresh = data['tokens']['refresh']
    
    print("=== LOGOUT ===")
    r = requests.post(f'{BASE}/logout/', json={'refresh': refresh},
                      headers={'Authorization': f'Bearer {access}'})
    print(f"Status: {r.status_code}")
    print(f"Body: {r.json()}")
    print()

# Cleanup
User.objects.filter(email='testuser@example.com').delete()
print("=== CLEANUP: test user deleted ===")
print("\nAll tests completed!")
