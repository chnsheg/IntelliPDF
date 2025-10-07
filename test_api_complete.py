"""
Comprehensive API test script for IntelliPDF.

Tests all API endpoints end-to-end:
- Document upload
- Document listing
- Document details
- Document chunks
- Document chat (RAG)
- Document deletion
"""

import asyncio
import time
from pathlib import Path

import httpx

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_PDF = Path("Linux教程.pdf")  # Use existing test PDF

# Colors for output


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    END = "\033[0m"


def print_test(name: str):
    """Print test name."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{Colors.END}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")


async def test_health_check(client: httpx.AsyncClient):
    """Test health check endpoint."""
    print_test("Health Check")

    try:
        response = await client.get(f"{API_PREFIX}/health")

        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_upload_document(client: httpx.AsyncClient, pdf_path: Path):
    """Test document upload."""
    print_test("Document Upload")

    if not pdf_path.exists():
        print_error(f"Test PDF not found: {pdf_path}")
        return None

    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            print_info(
                f"Uploading {pdf_path.name} ({pdf_path.stat().st_size / 1024:.2f} KB)...")

            start_time = time.time()
            response = await client.post(
                f"{API_PREFIX}/documents/upload",
                files=files,
                timeout=300.0  # 5 minutes timeout for large files
            )
            elapsed = time.time() - start_time

        if response.status_code == 201:
            data = response.json()
            doc_id = data["id"]
            print_success(f"Document uploaded successfully!")
            print_info(f"Document ID: {doc_id}")
            print_info(f"Filename: {data['filename']}")
            print_info(f"Status: {data['status']}")
            print_info(f"Chunks: {data.get('chunk_count', 0)}")
            print_info(f"Upload time: {elapsed:.2f} seconds")
            return doc_id
        else:
            print_error(f"Upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Upload error: {e}")
        return None


async def test_list_documents(client: httpx.AsyncClient):
    """Test document listing."""
    print_test("List Documents")

    try:
        response = await client.get(f"{API_PREFIX}/documents")

        if response.status_code == 200:
            data = response.json()
            total = data["total"]
            docs = data["documents"]

            print_success(f"Found {total} documents")
            for doc in docs:
                print_info(f"  - {doc['filename']} ({doc['status']})")
            return True
        else:
            print_error(f"List failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"List error: {e}")
        return False


async def test_get_document(client: httpx.AsyncClient, doc_id: str):
    """Test getting document details."""
    print_test("Get Document Details")

    try:
        response = await client.get(f"{API_PREFIX}/documents/{doc_id}")

        if response.status_code == 200:
            data = response.json()
            print_success("Document details retrieved")
            print_info(f"ID: {data['id']}")
            print_info(f"Filename: {data['filename']}")
            print_info(f"Status: {data['status']}")
            print_info(f"File size: {data['file_size'] / 1024:.2f} KB")
            print_info(f"Chunks: {data['chunk_count']}")
            if data.get('doc_metadata'):
                print_info(f"Metadata: {data['doc_metadata']}")
            return True
        else:
            print_error(f"Get document failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get document error: {e}")
        return False


async def test_get_statistics(client: httpx.AsyncClient):
    """Test getting statistics."""
    print_test("Get Statistics")

    try:
        response = await client.get(f"{API_PREFIX}/documents/statistics")

        if response.status_code == 200:
            data = response.json()
            print_success("Statistics retrieved")
            print_info(f"Total documents: {data['total']}")
            print_info(f"Total size: {data['total_size'] / 1024:.2f} KB")
            print_info(f"By status: {data['by_status']}")
            return True
        else:
            print_error(f"Get statistics failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get statistics error: {e}")
        return False


async def test_get_chunks(client: httpx.AsyncClient, doc_id: str):
    """Test getting document chunks."""
    print_test("Get Document Chunks")

    try:
        response = await client.get(f"{API_PREFIX}/documents/{doc_id}/chunks")

        if response.status_code == 200:
            data = response.json()
            total = data["total"]
            chunks = data["chunks"]

            print_success(f"Retrieved {total} chunks")
            if chunks:
                first_chunk = chunks[0]
                print_info(f"First chunk:")
                print_info(f"  - Index: {first_chunk['chunk_index']}")
                print_info(
                    f"  - Pages: {first_chunk['start_page']}-{first_chunk['end_page']}")
                print_info(f"  - Type: {first_chunk['chunk_type']}")
                print_info(
                    f"  - Content length: {len(first_chunk['content'])} chars")
                print_info(
                    f"  - Content preview: {first_chunk['content'][:100]}...")
            return True
        else:
            print_error(f"Get chunks failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get chunks error: {e}")
        return False


async def test_chat(client: httpx.AsyncClient, doc_id: str):
    """Test document chat (RAG)."""
    print_test("Document Chat (RAG)")

    questions = [
        "这个文档主要讲什么内容？",
        "Linux中如何查看文件列表？",
        "什么是Shell？"
    ]

    for question in questions:
        print_info(f"Question: {question}")

        try:
            start_time = time.time()
            response = await client.post(
                f"{API_PREFIX}/documents/{doc_id}/chat",
                json={
                    "question": question,
                    "top_k": 3,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                print_success("Answer generated")
                print_info(f"Answer: {data['answer'][:200]}...")
                print_info(f"Sources: {len(data['sources'])} chunks")
                print_info(f"Processing time: {elapsed:.2f}s")
            else:
                print_error(f"Chat failed: {response.status_code}")
                print_error(f"Response: {response.text}")

        except Exception as e:
            print_error(f"Chat error: {e}")

        print()  # Blank line between questions


async def test_delete_document(client: httpx.AsyncClient, doc_id: str):
    """Test document deletion."""
    print_test("Delete Document")

    try:
        response = await client.delete(f"{API_PREFIX}/documents/{doc_id}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Document deleted: {data['message']}")
            return True
        else:
            print_error(f"Delete failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Delete error: {e}")
        return False


async def run_all_tests():
    """Run all API tests."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("IntelliPDF API Test Suite")
    print(f"{'='*60}{Colors.END}\n")

    print_info(f"API URL: {BASE_URL}{API_PREFIX}")
    print_info(f"Test PDF: {TEST_PDF}")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Health check
        if not await test_health_check(client):
            print_error("Health check failed, stopping tests")
            return

        # 2. Upload document
        doc_id = await test_upload_document(client, TEST_PDF)
        if not doc_id:
            print_error("Upload failed, stopping tests")
            return

        # 3. List documents
        await test_list_documents(client)

        # 4. Get document details
        await test_get_document(client, doc_id)

        # 5. Get statistics
        await test_get_statistics(client)

        # 6. Get chunks
        await test_get_chunks(client, doc_id)

        # 7. Chat with document
        await test_chat(client, doc_id)

        # 8. Delete document (optional - comment out to keep test data)
        # await test_delete_document(client, doc_id)

    print(f"\n{Colors.GREEN}{'='*60}")
    print("All tests completed!")
    print(f"{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
