"""
Test script to verify the register endpoint works correctly.
Run this after starting the Django server.
"""
import requests
import json

BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/api/v1/auth/register/"

def test_register():
    """Test the register endpoint."""
    print("Testing register endpoint...")
    print(f"URL: {REGISTER_URL}")
    
    # Test data for registration
    data = {
        "email": "testadmin@example.com",
        "password": "secure-password-123",
        "first_name": "Test",
        "last_name": "Admin",
        "role": "admin"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            REGISTER_URL,
            data=json.dumps(data),
            headers=headers
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✅ SUCCESS: User registered successfully!")
        elif response.status_code == 403:
            print("\n⚠️  Registration disabled - admin users already exist")
        elif response.status_code == 401:
            print("\n❌ ERROR: Authentication required (this should not happen for register)")
        else:
            print(f"\n❌ ERROR: Unexpected status code {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("Make sure the Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_register()
