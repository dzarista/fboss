"""
Test configuration and fixtures for backend tests
"""
import pytest
import os
from unittest.mock import Mock, patch

# Mock database connection for all tests
@pytest.fixture(autouse=True)
def mock_database():
    """Mock the database connection for all tests"""
    # Create a mock instance
    mock_db_instance = Mock()

    # Mock common database methods
    mock_db_instance.create_session.return_value = {
        'session_id': 'test-session-123',
        'name': 'Test Session',
        'description': 'Test Description'
    }
    mock_db_instance.get_session.return_value = {
        'session_id': 'test-session-123',
        'name': 'Test Session'
    }
    mock_db_instance.list_sessions.return_value = []
    mock_db_instance.add_file.return_value = 'test-file-123'
    mock_db_instance.get_file.return_value = None
    mock_db_instance.delete_file.return_value = True
    mock_db_instance.delete_session.return_value = True

    # Patch the db_api instance in the app module
    with patch('app.db_api', mock_db_instance):
        yield mock_db_instance

@pytest.fixture
def app():
    """Create test Flask app"""
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DB_HOST'] = 'localhost'
    
    # Import app after setting environment
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
