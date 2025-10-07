import requests

try:
    response = requests.get("http://127.0.0.1:8000/api/v1/health", proxies={"http": None, "https": None})
    print(f"Status: {response.status_code}")
    print(f"Content: {response.text}")
    if response.status_code == 200:
        print(f"JSON: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
