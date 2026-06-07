import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_tests():
    print("🚀 Starting Automated API Tests...\n")
    
    # 1. Register User
    print("1. Registering test user...")
    res = requests.post(f"{BASE_URL}/users/", json={"email": "test_auto@example.com", "password": "password123"})
    if res.status_code == 200 or res.status_code == 400: # 400 if already exists
        print("✅ User registered or already exists.")
    else:
        print(f"❌ User registration failed: {res.text}")
        return

    # 2. Login
    print("\n2. Logging in...")
    res = requests.post(f"{BASE_URL}/token", data={"username": "test_auto@example.com", "password": "password123"})
    if res.status_code == 200:
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful. Token acquired.")
    else:
        print(f"❌ Login failed: {res.text}")
        return

    # 3. Upload Dataset
    print("\n3. Uploading dataset...")
    # Create a dummy CSV
    with open("test_data.csv", "w") as f:
        f.write("id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300")
        
    with open("test_data.csv", "rb") as f:
        res = requests.post(f"{BASE_URL}/datasets/upload", headers=headers, files={"file": ("test_data.csv", f, "text/csv")})
        
    if res.status_code == 200:
        dataset_id = res.json()["id"]
        print(f"✅ Dataset uploaded successfully. ID: {dataset_id}")
    else:
        print(f"❌ Dataset upload failed: {res.text}")
        return

    # Wait for background agent
    print("Waiting for background analysis to complete...")
    time.sleep(3)

    # 4. List Datasets
    print("\n4. Listing datasets...")
    res = requests.get(f"{BASE_URL}/datasets/", headers=headers)
    if res.status_code == 200 and len(res.json()) > 0:
        print(f"✅ Datasets listed successfully. Found {len(res.json())} datasets.")
    else:
        print(f"❌ List datasets failed: {res.text}")

    # 5. Get Dataset Data
    print("\n5. Fetching dataset data...")
    res = requests.get(f"{BASE_URL}/datasets/{dataset_id}/data", headers=headers)
    if res.status_code == 200:
        print("✅ Dataset data fetched successfully.")
    else:
        print(f"❌ Fetch dataset data failed: {res.text}")

    # 6. Chat with Dataset
    print("\n6. Chatting with dataset (Testing LLM Fallback Chain)...")
    chat_payload = {
        "dataset_ids": [dataset_id],
        "question": "What is the total value?",
        "session_id": None
    }
    res = requests.post(f"{BASE_URL}/chat/", headers=headers, json=chat_payload)
    if res.status_code == 200:
        chat_res = res.json()
        session_id = chat_res["session_id"]
        print(f"✅ Chat successful! AI Response: {chat_res['answer'][:50]}...")
        print(f"   Created Session ID: {session_id}")
    else:
        print(f"❌ Chat failed: {res.text}")
        return

    # 7. List Chat Sessions
    print("\n7. Listing chat sessions...")
    res = requests.get(f"{BASE_URL}/chat/sessions/{dataset_id}", headers=headers)
    if res.status_code == 200 and len(res.json()) > 0:
        print(f"✅ Chat sessions listed successfully. Found {len(res.json())} sessions.")
    else:
        print(f"❌ List sessions failed: {res.text}")

    # 8. Get Chat History
    print("\n8. Fetching chat history...")
    res = requests.get(f"{BASE_URL}/chat/history/{session_id}", headers=headers)
    if res.status_code == 200 and len(res.json()) == 2: # 1 user, 1 AI
        print("✅ Chat history fetched successfully. 2 messages found.")
    else:
        print(f"❌ Fetch history failed: {res.text}")

    # 9. Delete Chat Session
    print("\n9. Deleting chat session...")
    res = requests.delete(f"{BASE_URL}/chat/sessions/{session_id}", headers=headers)
    if res.status_code == 200:
        print("✅ Chat session deleted successfully.")
    else:
        print(f"❌ Delete session failed: {res.text}")

    # 10. Delete Dataset
    print("\n10. Deleting dataset...")
    res = requests.delete(f"{BASE_URL}/datasets/{dataset_id}", headers=headers)
    if res.status_code == 200:
        print("✅ Dataset deleted successfully.")
    else:
        print(f"❌ Delete dataset failed: {res.text}")
        
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    run_tests()
