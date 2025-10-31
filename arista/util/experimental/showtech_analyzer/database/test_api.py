#!/usr/bin/env python3
"""
Comprehensive test suite for the Showtech Database API
"""

import sys
import time
from db_api import ShowtechDatabaseAPI


def test_session_operations(api):
    """Test session CRUD operations"""
    print("\n🧪 Testing Session Operations")
    print("-" * 30)
    
    # Create session
    session = api.create_session(
        name="Test Session 1",
        description="First test session"
    )
    session_id = session["session_id"]
    print(f"✅ Created session: {session['name']}")
    
    # Get session
    retrieved = api.get_session(session_id)
    assert retrieved is not None, "Failed to retrieve session"
    assert retrieved["name"] == "Test Session 1", "Session name mismatch"
    print(f"✅ Retrieved session: {retrieved['name']}")
    
    # Update session
    success = api.update_session(session_id, name="Updated Session", description="Updated description")
    assert success, "Failed to update session"
    
    updated = api.get_session(session_id)
    assert updated["name"] == "Updated Session", "Session name not updated"
    print(f"✅ Updated session: {updated['name']}")
    
    # List sessions
    sessions = api.list_sessions()
    assert len(sessions) >= 1, "No sessions found"
    print(f"✅ Listed {len(sessions)} sessions")
    
    return session_id


def test_file_operations(api, session_id):
    """Test file CRUD operations"""
    print("\n🧪 Testing File Operations")
    print("-" * 30)
    
    # Add files
    file1_content = {
        "hostname": "switch1.test.com",
        "sections": ["System", "Interfaces", "BGP"],
        "interface_count": 24,
        "bgp_peers": 5
    }
    
    file1_id = api.add_file(
        session_id=session_id,
        filename="switch1-showtech.txt",
        file_content=file1_content,
        size_bytes=1024
    )
    assert file1_id is not None, "Failed to add file 1"
    print(f"✅ Added file 1: switch1-showtech.txt")
    
    file2_content = {
        "hostname": "switch2.test.com",
        "sections": ["System", "OSPF", "VLAN"],
        "vlan_count": 100,
        "ospf_areas": 3
    }
    
    file2_id = api.add_file(
        session_id=session_id,
        filename="switch2-showtech.txt",
        file_content=file2_content,
        size_bytes=2048
    )
    assert file2_id is not None, "Failed to add file 2"
    print(f"✅ Added file 2: switch2-showtech.txt")
    
    # List files
    files = api.list_files(session_id)
    assert len(files) == 2, f"Expected 2 files, got {len(files)}"
    print(f"✅ Listed {len(files)} files")
    
    # Get specific file
    file1_data = api.get_file(session_id, file1_id)
    assert file1_data is not None, "Failed to get file 1"
    assert file1_data["filename"] == "switch1-showtech.txt", "File 1 name mismatch"
    print(f"✅ Retrieved file: {file1_data['filename']}")
    
    # Note: Showtech files are immutable after upload, so no update test needed

    # Delete file
    success = api.delete_file(session_id, file2_id)
    assert success, "Failed to delete file"
    
    remaining_files = api.list_files(session_id)
    assert len(remaining_files) == 1, f"Expected 1 file after deletion, got {len(remaining_files)}"
    print(f"✅ Deleted file, {len(remaining_files)} remaining")
    
    return file1_id


def test_utility_operations(api, session_id):
    """Test utility operations"""
    print("\n🧪 Testing Utility Operations")
    print("-" * 30)
    
    # Get session with files
    full_session = api.get_session_with_files(session_id)
    assert full_session is not None, "Failed to get session with files"
    assert "metadata" in full_session, "Missing metadata"
    assert "files" in full_session, "Missing files"
    print(f"✅ Got session with {len(full_session['files'])} files")
    
    # Search sessions
    results = api.search_sessions("Updated")
    assert len(results) >= 1, "Search returned no results"
    print(f"✅ Search found {len(results)} sessions")
    
    # Get database stats
    stats = api.get_database_stats()
    assert "total_sessions" in stats, "Missing total_sessions in stats"
    assert "total_files" in stats, "Missing total_files in stats"
    assert stats["total_sessions"] >= 1, "No sessions in stats"
    print(f"✅ Database stats: {stats['total_sessions']} sessions, {stats['total_files']} files")


def test_edge_cases(api):
    """Test edge cases and error conditions"""
    print("\n🧪 Testing Edge Cases")
    print("-" * 30)
    
    # Get non-existent session
    result = api.get_session("non-existent-id")
    assert result is None, "Should return None for non-existent session"
    print("✅ Handled non-existent session")
    
    # Add file to non-existent session
    file_id = api.add_file("non-existent-session", "test.txt", {"data": "test"})
    assert file_id is None, "Should return None when adding file to non-existent session"
    print("✅ Handled file addition to non-existent session")
    
    # Delete non-existent session
    success = api.delete_session("non-existent-id")
    assert not success, "Should return False for non-existent session deletion"
    print("✅ Handled non-existent session deletion")
    
    # Search with empty query
    results = api.search_sessions("")
    # Should return all sessions (empty query matches all)
    print(f"✅ Empty search returned {len(results)} sessions")


def cleanup_test_data(api):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Get all sessions and delete test ones
    sessions = api.list_sessions()
    deleted_count = 0
    
    for session in sessions:
        if "test" in session["name"].lower() or "updated" in session["name"].lower():
            success = api.delete_session(session["session_id"])
            if success:
                deleted_count += 1
    
    print(f"✅ Cleaned up {deleted_count} test sessions")


def main():
    """Run all tests"""
    print("🚀 Starting Showtech Database API Tests")
    print("=" * 50)
    
    # Initialize API
    try:
        api = ShowtechDatabaseAPI()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("Make sure MongoDB is running: ./start-mongo.sh")
        sys.exit(1)
    
    try:
        # Run tests
        session_id = test_session_operations(api)
        file_id = test_file_operations(api, session_id)
        test_utility_operations(api, session_id)
        test_edge_cases(api)
        
        # Clean up
        cleanup_test_data(api)
        
        print("\n🎉 All tests passed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        api.close()


if __name__ == "__main__":
    main()
