"""
Quick API health check test.
"""

import requests

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_list_documents():
    """Test listing documents."""
    print("\nTesting list documents...")
    response = requests.get(f"{BASE_URL}/api/v1/documents")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total documents: {data['total']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


if __name__ == "__main__":
    print("="*60)
    print("IntelliPDF Quick API Test")
    print("="*60)

    if test_health():
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")

    if test_list_documents():
        print("✅ List documents passed")
    else:
        print("❌ List documents failed")

    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)
