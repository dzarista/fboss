#!/usr/bin/env python3
"""
Command Line Interface for Showtech Database API
Provides easy access to database operations from the command line
"""

import sys
import json
import argparse
from db_api import ShowtechDatabaseAPI


def format_session(session):
    """Format session data for display"""
    return f"ID: {session['session_id'][:8]}... | Name: {session['name']} | Files: {session['file_count']} | Size: {session['total_size_bytes']} bytes"


def format_file(file_data):
    """Format file data for display"""
    return f"ID: {file_data['file_id'][:8]}... | Name: {file_data['filename']} | Size: {file_data['size_bytes']} bytes"


def cmd_list_sessions(api, args):
    """List all sessions"""
    sessions = api.list_sessions(limit=args.limit)
    
    if not sessions:
        print("No sessions found.")
        return
    
    print(f"Found {len(sessions)} sessions:")
    print("-" * 80)
    for session in sessions:
        print(format_session(session))


def cmd_create_session(api, args):
    """Create a new session"""
    session = api.create_session(args.name, args.description or "")
    print(f"✅ Created session: {session['session_id']}")
    print(f"   Name: {session['name']}")
    if session['description']:
        print(f"   Description: {session['description']}")


def cmd_get_session(api, args):
    """Get session details"""
    if args.with_files:
        session_data = api.get_session_with_files(args.session_id)
        if not session_data:
            print(f"Session {args.session_id} not found.")
            return
        
        session = session_data['metadata']
        files = session_data['files']
        
        print(f"Session: {session['name']}")
        print(f"ID: {session['session_id']}")
        print(f"Description: {session.get('description', 'N/A')}")
        print(f"Created: {session['created_at']}")
        print(f"Files: {len(files)}")
        
        if files:
            print("\nFiles:")
            print("-" * 40)
            for file_data in files:
                print(format_file(file_data))
    else:
        session = api.get_session(args.session_id)
        if not session:
            print(f"Session {args.session_id} not found.")
            return
        
        print(json.dumps(session, indent=2, default=str))


def cmd_delete_session(api, args):
    """Delete a session"""
    if not args.force:
        confirm = input(f"Are you sure you want to delete session {args.session_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    success = api.delete_session(args.session_id)
    if success:
        print(f"✅ Deleted session: {args.session_id}")
    else:
        print(f"❌ Failed to delete session: {args.session_id}")


def cmd_add_file(api, args):
    """Add a file to a session"""
    try:
        # Read file content
        with open(args.file_path, 'r') as f:
            content = f.read()
        
        # Create file content structure
        file_content = {
            "raw_content": content,
            "filename": args.filename or args.file_path.split('/')[-1]
        }
        
        file_id = api.add_file(
            session_id=args.session_id,
            filename=args.filename or args.file_path.split('/')[-1],
            file_content=file_content,
            size_bytes=len(content)
        )
        
        if file_id:
            print(f"✅ Added file: {file_id}")
        else:
            print("❌ Failed to add file")
            
    except FileNotFoundError:
        print(f"❌ File not found: {args.file_path}")
    except Exception as e:
        print(f"❌ Error adding file: {e}")


def cmd_list_files(api, args):
    """List files in a session"""
    files = api.list_files(args.session_id)
    
    if not files:
        print("No files found in session.")
        return
    
    print(f"Found {len(files)} files:")
    print("-" * 60)
    for file_data in files:
        print(format_file(file_data))


def cmd_delete_file(api, args):
    """Delete a file from a session"""
    if not args.force:
        confirm = input(f"Are you sure you want to delete file {args.file_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    success = api.delete_file(args.session_id, args.file_id)
    if success:
        print(f"✅ Deleted file: {args.file_id}")
    else:
        print(f"❌ Failed to delete file: {args.file_id}")


def cmd_search(api, args):
    """Search sessions"""
    results = api.search_sessions(args.query, limit=args.limit)
    
    if not results:
        print(f"No sessions found matching '{args.query}'.")
        return
    
    print(f"Found {len(results)} sessions matching '{args.query}':")
    print("-" * 80)
    for session in results:
        print(format_session(session))


def cmd_stats(api, args):
    """Show database statistics"""
    stats = api.get_database_stats()
    
    print("Database Statistics:")
    print("-" * 20)
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"Total Files: {stats['total_files']}")
    print(f"Total Size: {stats['total_size_mb']} MB ({stats['total_size_bytes']} bytes)")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Showtech Database CLI")
    parser.add_argument("--connection", help="MongoDB connection string")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List sessions
    list_parser = subparsers.add_parser("list", help="List sessions")
    list_parser.add_argument("--limit", type=int, default=50, help="Maximum number of sessions")
    
    # Create session
    create_parser = subparsers.add_parser("create", help="Create a new session")
    create_parser.add_argument("name", help="Session name")
    create_parser.add_argument("--description", help="Session description")
    
    # Get session
    get_parser = subparsers.add_parser("get", help="Get session details")
    get_parser.add_argument("session_id", help="Session ID")
    get_parser.add_argument("--with-files", action="store_true", help="Include file list")
    
    # Delete session
    delete_parser = subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument("session_id", help="Session ID")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Add file
    add_file_parser = subparsers.add_parser("add-file", help="Add file to session")
    add_file_parser.add_argument("session_id", help="Session ID")
    add_file_parser.add_argument("file_path", help="Path to file")
    add_file_parser.add_argument("--filename", help="Custom filename")
    
    # List files
    list_files_parser = subparsers.add_parser("list-files", help="List files in session")
    list_files_parser.add_argument("session_id", help="Session ID")
    
    # Delete file
    delete_file_parser = subparsers.add_parser("delete-file", help="Delete file from session")
    delete_file_parser.add_argument("session_id", help="Session ID")
    delete_file_parser.add_argument("file_id", help="File ID")
    delete_file_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Search
    search_parser = subparsers.add_parser("search", help="Search sessions")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    
    # Stats
    subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize API
    try:
        api = ShowtechDatabaseAPI(args.connection)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Execute command
        if args.command == "list":
            cmd_list_sessions(api, args)
        elif args.command == "create":
            cmd_create_session(api, args)
        elif args.command == "get":
            cmd_get_session(api, args)
        elif args.command == "delete":
            cmd_delete_session(api, args)
        elif args.command == "add-file":
            cmd_add_file(api, args)
        elif args.command == "list-files":
            cmd_list_files(api, args)
        elif args.command == "delete-file":
            cmd_delete_file(api, args)
        elif args.command == "search":
            cmd_search(api, args)
        elif args.command == "stats":
            cmd_stats(api, args)
        else:
            print(f"Unknown command: {args.command}")
            
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        api.close()


if __name__ == "__main__":
    main()
