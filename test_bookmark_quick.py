"""
Quick test for bookmark API - single test at a time
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test server health"""
    print("Testing server health...")
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✓ Server is healthy: {r.json()}")
        return True
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        return False


def test_register_login():
    """Test user registration and login"""
    print("\nTesting authentication...")

    # Try register
    try:
        r = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "bookmark_test@example.com",
                "password": "testpass123",
                "username": "bookmarktest"
            }
        )
        if r.status_code == 200:
            print("✓ User registered")
            token = r.json()["access_token"]
            return token
        elif "already exists" in r.text:
            print("ℹ User exists, trying login...")
        else:
            print(f"Registration response: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"✗ Registration error: {e}")

    # Try login
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": "bookmark_test@example.com",
                "password": "testpass123"
            }
        )
        if r.status_code == 200:
            token = r.json()["access_token"]
            print(f"✓ Login successful, token: {token[:20]}...")
            return token
        else:
            print(f"✗ Login failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None


def test_get_documents(token):
    """Get existing documents"""
    print("\nGetting documents...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/documents",
                         headers=headers, params={"limit": 10})
        if r.status_code == 200:
            data = r.json()
            docs = data.get("documents", [])
            print(f"✓ Found {len(docs)} documents")
            for doc in docs[:3]:
                print(f"  - {doc['id']}: {doc['filename']}")
            return docs[0]['id'] if docs else None
        else:
            print(f"✗ Failed to get documents: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_create_bookmark(token, document_id):
    """Create a bookmark"""
    print(f"\nCreating bookmark for document {document_id}...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        bookmark_data = {
            "document_id": document_id,
            "selected_text": "测试书签内容。这是一个关于深度学习的测试段落。",
            "page_number": 1,
            "position": {
                "x": 100.0,
                "y": 200.0,
                "width": 300.0,
                "height": 50.0
            },
            "conversation_history": [
                {"role": "user", "content": "什么是深度学习？"},
                {"role": "assistant", "content": "深度学习是机器学习的一个分支"}
            ],
            "title": "测试书签",
            "tags": ["测试", "AI"],
            "color": "#FCD34D"
        }

        r = requests.post(
            f"{BASE_URL}/bookmarks",
            headers=headers,
            json=bookmark_data,
            timeout=30
        )

        if r.status_code == 201:
            bookmark = r.json()
            print(f"✓ Bookmark created: {bookmark['id']}")
            print(f"  Title: {bookmark['title']}")
            print(f"  AI Summary: {bookmark['ai_summary'][:100]}...")
            return bookmark['id']
        else:
            print(f"✗ Failed: {r.status_code}")
            print(f"  Response: {r.text[:500]}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_bookmarks(token, document_id=None):
    """Get bookmarks"""
    print("\nGetting bookmarks...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"document_id": document_id} if document_id else {}

        r = requests.get(f"{BASE_URL}/bookmarks",
                         headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            print(f"✓ Found {data['total']} bookmarks")
            for bm in data['bookmarks']:
                print(f"  - {bm['title']} (page {bm['page_number']})")
            return data['bookmarks']
        else:
            print(f"✗ Failed: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def main():
    print("="*60)
    print("Bookmark API Quick Test")
    print("="*60)

    # 1. Health check
    if not test_health():
        print("\n✗ Server not running. Please start backend first.")
        return

    # 2. Authentication
    token = test_register_login()
    if not token:
        print("\n✗ Authentication failed")
        return

    # 3. Get documents
    document_id = test_get_documents(token)
    if not document_id:
        print("\n✗ No documents found. Please upload a document first.")
        return

    # 4. Create bookmark
    bookmark_id = test_create_bookmark(token, document_id)
    if not bookmark_id:
        print("\n✗ Failed to create bookmark")
        return

    # 5. Get bookmarks
    test_get_bookmarks(token, document_id)

    print("\n" + "="*60)
    print("✓ Basic tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
