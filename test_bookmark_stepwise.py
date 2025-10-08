"""
Step-by-step Bookmark API Testing
Tests each endpoint individually to isolate issues
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None
DOCUMENT_ID = None
BOOKMARK_ID = None


def print_step(step_num, title):
    """Print formatted step header"""
    print("\n" + "="*60)
    print(f"STEP {step_num}: {title}")
    print("="*60)


def print_result(success, message, data=None):
    """Print test result"""
    icon = "✓" if success else "✗"
    color = "32" if success else "31"  # Green or Red
    print(f"\033[{color}m{icon} {message}\033[0m")
    if data:
        print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")


# Step 1: Health Check
print_step(1, "Health Check")
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    if r.status_code == 200:
        print_result(True, "Server is healthy", r.json())
    else:
        print_result(False, f"Unexpected status: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Server not accessible: {e}")
    sys.exit(1)

# Step 2: User Login
print_step(2, "User Authentication")
try:
    # Try login first
    r = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "test@intellipdf.com",
            "password": "testpass123"
        }
    )

    if r.status_code == 200:
        TOKEN = r.json()["access_token"]
        print_result(True, f"Login successful, token: {TOKEN[:30]}...")
    else:
        # Try register
        print("  Login failed, trying registration...")
        r = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "test@intellipdf.com",
                "password": "testpass123",
                "username": "testuser"
            }
        )
        if r.status_code in [200, 201]:  # Accept both 200 and 201
            TOKEN = r.json()["access_token"]
            print_result(
                True, f"Registration successful, token: {TOKEN[:30]}...")
        else:
            print_result(False, f"Auth failed: {r.status_code} - {r.text}")
            sys.exit(1)
except Exception as e:
    print_result(False, f"Auth error: {e}")
    sys.exit(1)

# Step 3: Get Documents
print_step(3, "Get Existing Documents")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(f"{BASE_URL}/documents",
                     headers=headers, params={"limit": 10})

    if r.status_code == 200:
        data = r.json()
        docs = data.get("documents", [])
        print_result(True, f"Found {len(docs)} documents")

        if docs:
            DOCUMENT_ID = docs[0]["id"]
            print(
                f"  Using document: {docs[0]['filename']} (ID: {DOCUMENT_ID})")
        else:
            print_result(
                False, "No documents found. Please upload a PDF first.")
            print("  You can upload via web interface or use upload endpoint.")
            sys.exit(1)
    else:
        print_result(False, f"Failed to get documents: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Step 4: Create Bookmark
print_step(4, "Create Bookmark")
try:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    bookmark_data = {
        "document_id": DOCUMENT_ID,
        "selected_text": "这是测试书签的内容。深度学习是机器学习的重要分支，通过多层神经网络实现复杂的模式识别。",
        "page_number": 1,
        "position": {
            "x": 100.0,
            "y": 200.0,
            "width": 300.0,
            "height": 50.0
        },
        "conversation_history": [
            {"role": "user", "content": "什么是深度学习？"},
            {"role": "assistant", "content": "深度学习是机器学习的一个分支，使用多层神经网络。"}
        ],
        "title": "深度学习基础",
        "tags": ["AI", "机器学习", "测试"],
        "color": "#FCD34D"
    }

    print("  Sending bookmark creation request...")
    print(f"  Document ID: {DOCUMENT_ID}")
    print(f"  Title: {bookmark_data['title']}")

    r = requests.post(
        f"{BASE_URL}/bookmarks",
        headers=headers,
        json=bookmark_data,
        timeout=30
    )

    if r.status_code == 201:
        bookmark = r.json()
        BOOKMARK_ID = bookmark["id"]
        print_result(True, "Bookmark created successfully!")
        print(f"  ID: {BOOKMARK_ID}")
        print(f"  Title: {bookmark['title']}")
        print(f"  AI Summary: {bookmark['ai_summary'][:80]}...")
    else:
        print_result(False, f"Failed: {r.status_code}")
        print(f"  Response: {r.text}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Get Bookmarks
print_step(5, "Get Bookmarks List")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(
        f"{BASE_URL}/bookmarks",
        headers=headers,
        params={"document_id": DOCUMENT_ID}
    )

    if r.status_code == 200:
        data = r.json()
        bookmarks = data.get("bookmarks", [])
        print_result(True, f"Retrieved {data['total']} bookmarks")
        for bm in bookmarks:
            print(f"  - {bm['title']} (Page {bm['page_number']})")
    else:
        print_result(False, f"Failed: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Step 6: Update Bookmark
print_step(6, "Update Bookmark")
try:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    update_data = {
        "title": "深度学习基础（已更新）",
        "user_notes": "这是一个重要的知识点，需要深入学习和实践。",
        "tags": ["AI", "机器学习", "深度学习", "神经网络"],
        "color": "#60A5FA"
    }

    r = requests.put(
        f"{BASE_URL}/bookmarks/{BOOKMARK_ID}",
        headers=headers,
        json=update_data
    )

    if r.status_code == 200:
        bookmark = r.json()
        print_result(True, "Bookmark updated successfully!")
        print(f"  New title: {bookmark['title']}")
        print(f"  Notes: {bookmark.get('user_notes', 'N/A')[:50]}...")
        print(f"  Tags: {', '.join(bookmark.get('tags', []))}")
    else:
        print_result(False, f"Failed: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Step 7: Search Bookmarks
print_step(7, "Search Bookmarks")
try:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    search_data = {
        "query": "深度学习",
        "document_id": DOCUMENT_ID
    }

    r = requests.post(
        f"{BASE_URL}/bookmarks/search",
        headers=headers,
        json=search_data
    )

    if r.status_code == 200:
        data = r.json()
        print_result(True, f"Found {data['total']} results for '深度学习'")
        for bm in data['bookmarks']:
            print(f"  - {bm['title']}")
    else:
        print_result(False, f"Failed: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Step 8: Get Single Bookmark
print_step(8, "Get Single Bookmark")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(
        f"{BASE_URL}/bookmarks/{BOOKMARK_ID}",
        headers=headers
    )

    if r.status_code == 200:
        bookmark = r.json()
        print_result(True, "Retrieved bookmark details")
        print(f"  Title: {bookmark['title']}")
        print(f"  Page: {bookmark['page_number']}")
        print(f"  Summary: {bookmark['ai_summary'][:60]}...")
    else:
        print_result(False, f"Failed: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Step 9: Delete Bookmark
print_step(9, "Delete Bookmark")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}

    confirm = input(
        "\nAre you sure you want to delete the test bookmark? (y/n): ")
    if confirm.lower() == 'y':
        r = requests.delete(
            f"{BASE_URL}/bookmarks/{BOOKMARK_ID}",
            headers=headers
        )

        if r.status_code == 204:
            print_result(True, "Bookmark deleted successfully")
        else:
            print_result(False, f"Failed: {r.status_code}")
            sys.exit(1)
    else:
        print("  Skipped deletion")
except Exception as e:
    print_result(False, f"Error: {e}")
    sys.exit(1)

# Final Summary
print("\n" + "="*60)
print("🎉 ALL TESTS PASSED!")
print("="*60)
print("\nBookmark API is working correctly!")
print(f"- Token: {TOKEN[:30]}...")
print(f"- Document ID: {DOCUMENT_ID}")
print(f"- Test completed successfully")
