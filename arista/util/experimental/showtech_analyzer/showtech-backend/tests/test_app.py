"""
Flask API tests - Essential endpoints
"""
import pytest
import os
from io import BytesIO
from app import app


class TestFlaskAPI:
    """Test Flask API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_status_endpoint(self, client):
        """Test /api/status endpoint"""
        response = client.get('/api/status')
        assert response.status_code == 200
        assert response.get_json() == {"status": "Success"}

    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/api/upload')
        assert response.status_code == 400

    def test_upload_clean_file(self, client):
        """Test upload clean showtech file"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')

        with open(sample_file, 'rb') as f:
            response = client.post('/api/upload', data={
                'file': (BytesIO(f.read()), 'sample_clean.txt')
            })

        assert response.status_code == 200
        data = response.get_json()
        assert data[0]['name'] == 'sample_clean.txt'
        assert len(data[0]['sections']) == 4  # Expected: 4 sections (including comment section)