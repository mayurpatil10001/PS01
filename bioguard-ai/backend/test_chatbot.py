"""
AI Chatbot Test Script
Tests the chatbot API endpoints to ensure everything is working correctly.
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8001"
USERNAME = "analyzer"  # Default analyzer user
PASSWORD = "analyzer123"  # Default password

def login() -> str:
    """Login and get JWT token."""
    print("🔐 Logging in...")
    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_chat(token: str, message: str) -> Dict[str, Any]:
    """Send a message to the chatbot."""
    print(f"\n💬 User: {message}")
    
    response = requests.post(
        f"{API_URL}/api/chatbot/chat",
        json={
            "message": message,
            "conversation_history": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🤖 AI Assistant:\n{data['response']}")
        
        if data.get('suggestions'):
            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(data['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        
        return data
    else:
        print(f"❌ Chat failed: {response.text}")
        return None

def test_suggestions(token: str):
    """Get suggested questions."""
    print("\n📋 Getting suggested questions...")
    
    response = requests.get(
        f"{API_URL}/api/chatbot/suggestions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        suggestions = response.json()["suggestions"]
        print("✅ Suggested questions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        return suggestions
    else:
        print(f"❌ Failed to get suggestions: {response.text}")
        return None

def main():
    """Run chatbot tests."""
    print("=" * 60)
    print("🧪 AI Chatbot Test Suite")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    print("\n" + "=" * 60)
    print("Test 1: Get Suggested Questions")
    print("=" * 60)
    test_suggestions(token)
    
    print("\n" + "=" * 60)
    print("Test 2: Critical Alerts Query")
    print("=" * 60)
    test_chat(token, "Show me critical alerts")
    
    print("\n" + "=" * 60)
    print("Test 3: Disease Information Query")
    print("=" * 60)
    test_chat(token, "Tell me about cholera prevention")
    
    print("\n" + "=" * 60)
    print("Test 4: Water Quality Query")
    print("=" * 60)
    test_chat(token, "What water parameters do you monitor?")
    
    print("\n" + "=" * 60)
    print("Test 5: Village Status Query")
    print("=" * 60)
    test_chat(token, "Which villages need attention?")
    
    print("\n" + "=" * 60)
    print("Test 6: Action/Intervention Query")
    print("=" * 60)
    test_chat(token, "What actions should I take?")
    
    print("\n" + "=" * 60)
    print("Test 7: System Status Query")
    print("=" * 60)
    test_chat(token, "What's the overall system status?")
    
    print("\n" + "=" * 60)
    print("Test 8: General Help Query")
    print("=" * 60)
    test_chat(token, "Hello, how can you help me?")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend server")
        print("   Make sure the backend is running on http://localhost:8001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
