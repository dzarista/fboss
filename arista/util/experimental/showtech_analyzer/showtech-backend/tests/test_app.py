"""
Flask API tests - Essential endpoints
"""
import pytest
import os
from io import BytesIO


class TestFlaskAPI:
    """Test Flask API endpoints"""

    def test_status_endpoint(self, client):
        """Test /api/status endpoint"""
        response = client.get('/api/status')
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "Success"
        assert "database" in data
        assert "environment" in data

    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/api/upload')
        assert response.status_code == 400

    def test_upload_clean_file(self, client, mock_database):
        """Test upload clean showtech file"""
        # Mock session exists
        mock_database.get_session.return_value = {
            'session_id': 'test-session-123',
            'name': 'Test Session'
        }

        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')

        with open(sample_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'file': (BytesIO(f.read()), 'sample_clean.txt'),
                'session_id': 'test-session-123'
            })

        assert response.status_code == 200
        data = response.get_json()
        assert data[0]['name'] == 'sample_clean.txt'
        assert len(data[0]['sections']) == 4  # Expected: 4 sections (including comment section)