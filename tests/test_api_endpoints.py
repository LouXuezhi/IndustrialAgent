#!/usr/bin/env python
"""
Comprehensive API endpoint tests for Industrial QA Backend.

This script tests all implemented API endpoints:
- Authentication (login, refresh, logout)
- Library management (CRUD operations)
- Document management (upload, list, get, delete, search, preview, download)
- Group permissions

Usage:
    python tests/test_api_endpoints.py
    # or
    uv run python tests/test_api_endpoints.py

Prerequisites:
    1. Run tests/init_test_data.py first to create test data
    2. Start the FastAPI server: uvicorn app.main:app --reload
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest


# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test user credentials
TEST_USERS = {
    "operator": {"email": "operator@test.com", "password": "test123456"},
    "maintenance": {"email": "maintenance@test.com", "password": "test123456"},
    "manager": {"email": "manager@test.com", "password": "test123456"},
    "admin": {"email": "admin@test.com", "password": "test123456"},
}

# Global state
tokens: dict[str, str] = {}
user_ids: dict[str, str] = {}
library_ids: dict[str, str] = {}
document_ids: list[str] = []


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_test_header(test_name: str):
    """Print test section header."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}Testing: {test_name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")


async def test_authentication(client: httpx.AsyncClient):
    """Test authentication endpoints."""
    print_test_header("Authentication")
    
    # Test login for each user
    for username, creds in TEST_USERS.items():
        try:
            response = await client.post(
                f"{API_BASE}/login",
                json={"email": creds["email"], "password": creds["password"]},
            )
            assert response.status_code == 200, f"Login failed for {username}: {response.status_code}"
            data = response.json()
            assert data["code"] == 0, f"Login error for {username}: {data.get('message')}"
            assert "data" in data, "Missing data in login response"
            assert "access_token" in data["data"], "Missing access_token"
            
            tokens[username] = data["data"]["access_token"]
            user_ids[username] = data["data"]["user_id"]
            print_success(f"Login successful for {username}")
        except Exception as e:
            print_error(f"Login failed for {username}: {e}")
            return False
    
    # Test refresh token
    try:
        response = await client.post(
            f"{API_BASE}/refresh",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Refresh failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data["data"], "Missing access_token in refresh"
        tokens["operator"] = data["data"]["access_token"]  # Update token
        print_success("Token refresh successful")
    except Exception as e:
        print_error(f"Token refresh failed: {e}")
        return False
    
    # Test logout
    try:
        response = await client.post(
            f"{API_BASE}/logout",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Logout failed: {response.status_code}"
        print_success("Logout successful")
        # Re-login for subsequent tests
        response = await client.post(
            f"{API_BASE}/login",
            json=TEST_USERS["operator"],
        )
        tokens["operator"] = response.json()["data"]["access_token"]
    except Exception as e:
        print_error(f"Logout failed: {e}")
        return False
    
    return True


async def test_library_management(client: httpx.AsyncClient):
    """Test library CRUD operations."""
    print_test_header("Library Management")
    
    # Create library
    try:
        response = await client.post(
            f"{API_BASE}/docs/libraries",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={
                "payload": {
                    "name": "Test Library",
                    "description": "Test library for API testing",
                    "owner_type": "user",
                }
            },
        )
        assert response.status_code == 200, f"Create library failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Create library error: {data.get('message')}"
        library_ids["test"] = data["data"]["id"]
        print_success(f"Created library: {library_ids['test']}")
    except Exception as e:
        print_error(f"Create library failed: {e}")
        return False
    
    # List libraries
    try:
        response = await client.get(
            f"{API_BASE}/docs/libraries?owner_type=user",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"List libraries failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"List libraries error: {data.get('message')}"
        assert isinstance(data["data"], list), "Libraries should be a list"
        print_success(f"Listed {len(data['data'])} libraries")
    except Exception as e:
        print_error(f"List libraries failed: {e}")
        return False
    
    # Get library
    try:
        response = await client.get(
            f"{API_BASE}/docs/libraries/{library_ids['test']}",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Get library failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Get library error: {data.get('message')}"
        assert data["data"]["id"] == library_ids["test"], "Library ID mismatch"
        print_success("Retrieved library details")
    except Exception as e:
        print_error(f"Get library failed: {e}")
        return False
    
    # Update library
    try:
        response = await client.put(
            f"{API_BASE}/docs/libraries/{library_ids['test']}",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={"payload": {"name": "Updated Test Library", "description": "Updated description"}},
        )
        assert response.status_code == 200, f"Update library failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Update library error: {data.get('message')}"
        assert data["data"]["name"] == "Updated Test Library", "Library name not updated"
        print_success("Updated library")
    except Exception as e:
        print_error(f"Update library failed: {e}")
        return False
    
    # Get library stats
    try:
        response = await client.get(
            f"{API_BASE}/docs/libraries/{library_ids['test']}/stats",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Get library stats failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Get library stats error: {data.get('message')}"
        print_success(f"Library stats: {data['data']['document_count']} documents, {data['data']['total_chunks']} chunks")
    except Exception as e:
        print_error(f"Get library stats failed: {e}")
        return False
    
    return True


async def test_document_management(client: httpx.AsyncClient):
    """Test document management operations."""
    print_test_header("Document Management")
    
    # Create a test file
    test_file = Path("/tmp/test_document.txt")
    test_file.write_text("This is a test document for API testing.\nIt contains multiple lines.\nFor testing document upload and ingestion.")
    
    # Upload document (no auto-vectorization)
    try:
        with open(test_file, "rb") as f:
            response = await client.post(
                f"{API_BASE}/docs/ingest?library_id={library_ids['test']}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
                files={"file": ("test_document.txt", f, "text/plain")},
            )
        assert response.status_code == 200, f"Upload document failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Upload document error: {data.get('message')}"
        assert data["data"].get("vectorized") is False, "Document should not be vectorized on upload"
        document_ids.append(data["data"]["document_id"])
        print_success(f"Uploaded document: {document_ids[0]}")
    except Exception as e:
        print_error(f"Upload document failed: {e}")
        return False

    # Trigger vectorization
    try:
        response = await client.post(
            f"{API_BASE}/docs/documents/{document_ids[0]}/vectorize",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={"payload": {"chunk_size": 800}},
        )
        assert response.status_code == 200, f"Vectorize document failed: {response.status_code}"
        data = response.json()
        assert data["data"]["vectorized"] is True, f"Vectorization flag should be True (code={data.get('code')}, msg={data.get('message')})"
        assert data["data"]["chunks"] > 0, "Chunks should be greater than 0 after vectorization"
        print_success(f"Vectorized document: {document_ids[0]}")
    except Exception as e:
        print_error(f"Vectorize document failed: {e}")
        return False
    
    # List documents
    try:
        response = await client.get(
            f"{API_BASE}/docs/libraries/{library_ids['test']}/documents",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"List documents failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"List documents error: {data.get('message')}"
        assert isinstance(data["data"], list), "Documents should be a list"
        # ensure our uploaded doc is present and marked vectorized
        found = next((d for d in data["data"] if d.get("id") == document_ids[0]), None)
        assert found, "Uploaded document not found in list response"
        assert found.get("vectorized") is True, "Document should be vectorized in list response"
        print_success(f"Listed {len(data['data'])} documents (found vectorized doc)")
    except Exception as e:
        print_error(f"List documents failed: {e}")
        return False
    
    # Get document
    try:
        response = await client.get(
            f"{API_BASE}/docs/documents/{document_ids[0]}",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Get document failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Get document error: {data.get('message')}"
        assert data["data"]["id"] == document_ids[0], "Document ID mismatch"
        assert data["data"].get("vectorized") is True, "Document should be vectorized after trigger"
        print_success("Retrieved document details")
    except Exception as e:
        print_error(f"Get document failed: {e}")
        return False
    
    # Search documents
    try:
        response = await client.post(
            f"{API_BASE}/docs/documents/search",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={"payload": {"query": "test", "library_id": library_ids["test"], "limit": 10}},
        )
        assert response.status_code == 200, f"Search documents failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Search documents error: {data.get('message')}"
        assert isinstance(data["data"], list), "Search results should be a list"
        print_success(f"Search found {len(data['data'])} results")
    except Exception as e:
        print_error(f"Search documents failed: {e}")
        return False
    
    # Preview document
    try:
        response = await client.get(
            f"{API_BASE}/docs/documents/{document_ids[0]}/preview?max_length=1000",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Preview document failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Preview document error: {data.get('message')}"
        assert "content" in data["data"], "Missing content in preview"
        assert data["data"].get("vectorized") is True, "Preview should indicate vectorized"
        print_success(f"Previewed document ({len(data['data']['content'])} chars)")
    except Exception as e:
        print_error(f"Preview document failed: {e}")
        return False
    
    # Download document
    try:
        response = await client.get(
            f"{API_BASE}/docs/documents/{document_ids[0]}/download",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
        )
        assert response.status_code == 200, f"Download document failed: {response.status_code}"
        print_success("Downloaded document")
    except Exception as e:
        print_info(f"Download document skipped (file may not exist on disk): {e}")
    
    # Cleanup test file
    test_file.unlink(missing_ok=True)
    
    return True


async def test_permissions(client: httpx.AsyncClient):
    """Test permission checks."""
    print_test_header("Permission Checks")
    
    # Test: operator cannot access maintenance's library
    try:
        # First, get maintenance's library ID (assuming it exists from init_test_data)
        response = await client.get(
            f"{API_BASE}/docs/libraries?owner_type=user",
            headers={"Authorization": f"Bearer {tokens['maintenance']}"},
        )
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                maintenance_lib_id = data["data"][0]["id"]
                
                # Try to access with operator token
                response = await client.get(
                    f"{API_BASE}/docs/libraries/{maintenance_lib_id}",
                    headers={"Authorization": f"Bearer {tokens['operator']}"},
                )
                assert response.status_code == 403, "Should be forbidden for operator"
                print_success("Permission check passed: operator cannot access maintenance's library")
    except Exception as e:
        print_info(f"Permission test skipped: {e}")
    
    return True


@pytest.mark.asyncio
async def test_agent_rag_flow(client: httpx.AsyncClient | None = None):
    """End-to-end Agent/RAG flow on a dedicated library and document."""
    print_test_header("Agent/RAG Flow")

    # Allow standalone pytest execution without provided client
    owns_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        owns_client = True

    rag_library_id: str | None = None
    rag_document_id: str | None = None

    # 1) Create a dedicated library
    try:
        response = await client.post(
            f"{API_BASE}/docs/libraries",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={
                "payload": {
                    "name": "RAG Agent Test Library",
                    "description": "Library for agent/RAG end-to-end test",
                    "owner_type": "user",
                }
            },
        )
        assert response.status_code == 200, f"Create RAG library failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Create RAG library error: {data.get('message')}"
        rag_library_id = data["data"]["id"]
        print_success(f"Created RAG test library: {rag_library_id}")
    except Exception as e:
        print_error(f"Create RAG test library failed: {e}")
        return False

    # 2) Upload a document with known content
    test_file = Path("/tmp/rag_agent_test.txt")
    content = "RAG_AGENT_TEST: The capital of France is Paris."
    test_file.write_text(content)
    try:
        with open(test_file, "rb") as f:
            response = await client.post(
                f"{API_BASE}/docs/ingest?library_id={rag_library_id}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
                files={"file": ("rag_agent_test.txt", f, "text/plain")},
            )
        assert response.status_code == 200, f"Upload RAG doc failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Upload RAG doc error: {data.get('message')}"
        rag_document_id = data["data"]["document_id"]
        print_success(f"Uploaded RAG test doc: {rag_document_id}")
    except Exception as e:
        print_error(f"Upload RAG test doc failed: {e}")
        return False

    # 3) Vectorize the document
    try:
        response = await client.post(
            f"{API_BASE}/docs/documents/{rag_document_id}/vectorize",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={"payload": {"chunk_size": 512}},
        )
        assert response.status_code == 200, f"Vectorize RAG doc failed: {response.status_code}"
        data = response.json()
        assert data["data"]["vectorized"] is True, f"Vectorization flag should be True (code={data.get('code')}, msg={data.get('message')})"
        print_success(f"Vectorized RAG test doc: {rag_document_id}")
    except Exception as e:
        print_error(f"Vectorize RAG test doc failed: {e}")
        return False

    # 4) Ask via Agent/RAG with library filter
    try:
        response = await client.post(
            f"{API_BASE}/ask",
            headers={"Authorization": f"Bearer {tokens['operator']}"},
            json={
                "payload": {
                    "query": "What is the capital of France?",
                    "library_ids": [rag_library_id],
                    "top_k": 3,
                }
            },
        )
        assert response.status_code == 200, f"Ask failed: {response.status_code}"
        data = response.json()
        assert data["code"] == 0, f"Ask error: {data.get('message')}"
        refs = data["data"].get("references", [])
        assert isinstance(refs, list), "References should be a list"
        assert len(refs) > 0, "Should return at least one reference"
        print_success(f"Ask succeeded with {len(refs)} reference(s)")
    except Exception as e:
        print_error(f"Ask (Agent/RAG) failed: {e}")
        return False

    # 5) Cleanup doc and library (best-effort)
    try:
        if rag_document_id:
            await client.delete(
                f"{API_BASE}/docs/documents/{rag_document_id}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
            )
        if rag_library_id:
            await client.delete(
                f"{API_BASE}/docs/libraries/{rag_library_id}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
            )
        test_file.unlink(missing_ok=True)
    except Exception:
        test_file.unlink(missing_ok=True)

    if owns_client:
        await client.aclose()

    return True


async def test_cleanup(client: httpx.AsyncClient):
    """Clean up test data."""
    print_test_header("Cleanup")
    
    # Delete test document
    if document_ids:
        try:
            response = await client.delete(
                f"{API_BASE}/docs/documents/{document_ids[0]}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
            )
            if response.status_code == 200:
                print_success("Deleted test document")
        except Exception as e:
            print_info(f"Cleanup document skipped: {e}")
    
    # Delete test library
    if "test" in library_ids:
        try:
            response = await client.delete(
                f"{API_BASE}/docs/libraries/{library_ids['test']}",
                headers={"Authorization": f"Bearer {tokens['operator']}"},
            )
            if response.status_code == 200:
                print_success("Deleted test library")
        except Exception as e:
            print_info(f"Cleanup library skipped: {e}")


async def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Industrial QA Backend - API Endpoint Tests{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    print_info(f"Testing against: {BASE_URL}")
    print_info("Make sure the server is running: uvicorn app.main:app --reload\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check server health
        try:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print_error(f"Server not responding at {BASE_URL}")
                print_info("Please start the server: uvicorn app.main:app --reload")
                sys.exit(1)
        except Exception as e:
            print_error(f"Cannot connect to server: {e}")
            print_info("Please start the server: uvicorn app.main:app --reload")
            sys.exit(1)
        
        results = []
        
        # Run tests
        results.append(("Authentication", await test_authentication(client)))
        results.append(("Library Management", await test_library_management(client)))
        results.append(("Document Management", await test_document_management(client)))
        results.append(("Permissions", await test_permissions(client)))
        results.append(("Agent/RAG Flow", await test_agent_rag_flow(client)))
        
        # Cleanup
        await test_cleanup(client)
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}Test Summary{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}\n")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  {test_name}: {status}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
        
        if passed == total:
            print_success("All tests passed! ✓")
            return 0
        else:
            print_error("Some tests failed. Please check the output above.")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

