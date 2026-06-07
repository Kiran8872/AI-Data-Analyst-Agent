import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_all():
    print("--- 1. Checking API Health ---")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        print("Health Check:", r.json())
    except Exception as e:
        print("Server is offline:", e)
        return

    print("\n--- 2. Authentication (Login/Register) ---")
    email = "test_e2e@example.com"
    password = "password123"
    
    # Try register first
    r = requests.post(f"{BASE_URL}/users/", json={"email": email, "password": password})
    if r.status_code == 200:
        print("Successfully registered test user.")
    
    # Login
    r = requests.post(f"{BASE_URL}/token", data={"username": email, "password": password})
    if r.status_code != 200:
        print("Login failed:", r.text)
        return
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Successfully obtained JWT access token.")

    print("\n--- 3. Data Ingestion & Pre-computation ---")
    csv_content = "month,product,revenue\nJan,Widget A,5000\nFeb,Widget A,5500\nMar,Widget A,6000\nJan,Widget B,200\nFeb,Widget B,300\nMar,Widget B,90000\n"
    with open("test_e2e_data.csv", "w") as f:
        f.write(csv_content)
    
    with open("test_e2e_data.csv", "rb") as f:
        r = requests.post(f"{BASE_URL}/datasets/upload", headers=headers, files={"file": ("test_e2e_data.csv", f, "text/csv")})
    
    if r.status_code != 200:
        print("Upload failed:", r.text)
        return
    dataset_id = r.json().get("id")
    print(f"Successfully uploaded and parsed dataset (ID: {dataset_id}). ChromaDB metadata generated.")

    print("\n--- 4. Testing DuckDB Fast Track (Simple Query) ---")
    start = time.time()
    r = requests.post(f"{BASE_URL}/chat", headers=headers, json={"dataset_ids": [dataset_id], "question": "What is the total revenue for Widget A?"})
    dur = time.time() - start
    print(f"Response ({dur:.2f}s):", r.json())

    print("\n--- 5. Testing LangChain Track (Complex Query) ---")
    start = time.time()
    r = requests.post(f"{BASE_URL}/chat", headers=headers, json={"dataset_ids": [dataset_id], "question": "Are there any outliers in Widget B's revenue? Use z-scores."})
    dur = time.time() - start
    print(f"Response ({dur:.2f}s):", r.json())
    
    print("\n--- All Tests Completed Successfully! ---")

if __name__ == "__main__":
    run_all()
