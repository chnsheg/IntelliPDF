"""
Test bookmark API endpoints.

Tests bookmark creation, retrieval, update, and deletion.
"""

import requests
import json
from typing import Dict, Optional

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
TEST_USER = {
    "email": "test@example.com",
    "password": "testpass123",
    "username": "testuser"
}


def register_user() -> Optional[str]:
    """Register a test user."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER
        )
        if response.status_code == 200:
            print(f"✓ User registered: {TEST_USER['email']}")
            return response.json()["access_token"]
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"ℹ User already exists: {TEST_USER['email']}")
            return None
        else:
            print(f"✗ Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Registration error: {str(e)}")
        return None


def login_user() -> Optional[str]:
    """Login and get access token."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✓ Login successful")
            return token
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {str(e)}")
        return None


def upload_test_document(token: str) -> Optional[str]:
    """Upload a test PDF document."""
    try:
        # Check if we have test PDF
        import os
        pdf_path = "论文.pdf"
        if not os.path.exists(pdf_path):
            pdf_path = "Linux教程.pdf"
        if not os.path.exists(pdf_path):
            print("✗ No test PDF found")
            return None

        headers = {"Authorization": f"Bearer {token}"}
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path, f, "application/pdf")}
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                headers=headers,
                files=files
            )

        if response.status_code == 200:
            doc_id = response.json()["id"]
            print(f"✓ Document uploaded: {doc_id}")
            return doc_id
        else:
            print(f"✗ Upload failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Upload error: {str(e)}")
        return None


def create_bookmark(token: str, document_id: str) -> Optional[str]:
    """Create a test bookmark."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        bookmark_data = {
            "document_id": document_id,
            "selected_text": "这是一段测试文本内容。深度学习是机器学习的一个分支，它模仿人脑的神经网络结构来处理数据。",
            "page_number": 1,
            "position": {
                "x": 100.5,
                "y": 200.3,
                "width": 300.0,
                "height": 50.0
            },
            "conversation_history": [
                {"role": "user", "content": "什么是深度学习？"},
                {"role": "assistant", "content": "深度学习是机器学习的一个重要分支..."}
            ],
            "title": "深度学习简介",
            "tags": ["AI", "机器学习"],
            "color": "#FCD34D"
        }

        response = requests.post(
            f"{BASE_URL}/bookmarks",
            headers=headers,
            json=bookmark_data
        )

        if response.status_code == 201:
            bookmark = response.json()
            bookmark_id = bookmark["id"]
            print(f"✓ Bookmark created: {bookmark_id}")
            print(f"  AI Summary: {bookmark['ai_summary'][:100]}...")
            return bookmark_id
        else:
            print(f"✗ Bookmark creation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Bookmark creation error: {str(e)}")
        return None


def get_bookmarks(token: str, document_id: Optional[str] = None):
    """Get bookmarks."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if document_id:
            params["document_id"] = document_id

        response = requests.get(
            f"{BASE_URL}/bookmarks",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {data['total']} bookmarks")
            for bookmark in data["bookmarks"]:
                print(
                    f"  - {bookmark['title'] or 'Untitled'} (page {bookmark['page_number']})")
            return data["bookmarks"]
        else:
            print(f"✗ Get bookmarks failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Get bookmarks error: {str(e)}")
        return None


def update_bookmark(token: str, bookmark_id: str):
    """Update a bookmark."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        update_data = {
            "title": "深度学习基础知识",
            "user_notes": "这是一个很重要的知识点，需要深入学习。",
            "tags": ["AI", "机器学习", "神经网络"],
            "color": "#60A5FA"
        }

        response = requests.put(
            f"{BASE_URL}/bookmarks/{bookmark_id}",
            headers=headers,
            json=update_data
        )

        if response.status_code == 200:
            bookmark = response.json()
            print(f"✓ Bookmark updated")
            print(f"  New title: {bookmark['title']}")
            print(f"  New notes: {bookmark['user_notes'][:50]}...")
            return True
        else:
            print(f"✗ Update failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Update error: {str(e)}")
        return False


def search_bookmarks(token: str, query: str, document_id: Optional[str] = None):
    """Search bookmarks."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        search_data = {
            "query": query,
            "document_id": document_id
        }

        response = requests.post(
            f"{BASE_URL}/bookmarks/search",
            headers=headers,
            json=search_data
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Search found {data['total']} results for '{query}'")
            for bookmark in data["bookmarks"]:
                print(f"  - {bookmark['title'] or 'Untitled'}")
            return data["bookmarks"]
        else:
            print(f"✗ Search failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Search error: {str(e)}")
        return None


def delete_bookmark(token: str, bookmark_id: str):
    """Delete a bookmark."""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.delete(
            f"{BASE_URL}/bookmarks/{bookmark_id}",
            headers=headers
        )

        if response.status_code == 204:
            print(f"✓ Bookmark deleted")
            return True
        else:
            print(f"✗ Delete failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Delete error: {str(e)}")
        return False


def main():
    """Run all bookmark tests."""
    print("=" * 60)
    print("Bookmark API Test Suite")
    print("=" * 60)

    # Step 1: Register or login
    print("\n[1] User Authentication")
    print("-" * 60)
    token = register_user()
    if not token:
        token = login_user()

    if not token:
        print("\n✗ Authentication failed. Exiting.")
        return

    # Step 2: Upload document
    print("\n[2] Document Upload")
    print("-" * 60)
    document_id = upload_test_document(token)

    if not document_id:
        print("\n✗ Document upload failed. Using mock document.")
        # Try to use existing document
        return

    # Step 3: Create bookmark
    print("\n[3] Create Bookmark")
    print("-" * 60)
    bookmark_id = create_bookmark(token, document_id)

    if not bookmark_id:
        print("\n✗ Bookmark creation failed. Exiting.")
        return

    # Step 4: Get bookmarks
    print("\n[4] Get Bookmarks")
    print("-" * 60)
    get_bookmarks(token, document_id)

    # Step 5: Update bookmark
    print("\n[5] Update Bookmark")
    print("-" * 60)
    update_bookmark(token, bookmark_id)

    # Step 6: Search bookmarks
    print("\n[6] Search Bookmarks")
    print("-" * 60)
    search_bookmarks(token, "深度学习", document_id)

    # Step 7: Delete bookmark
    print("\n[7] Delete Bookmark")
    print("-" * 60)
    delete_bookmark(token, bookmark_id)

    # Final verification
    print("\n[8] Final Verification")
    print("-" * 60)
    get_bookmarks(token, document_id)

    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
