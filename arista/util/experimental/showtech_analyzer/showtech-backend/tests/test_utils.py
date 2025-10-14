"""
Test utilities - Helper functions for testing
"""
import tempfile
import os
from pathlib import Path


class TestDataHelper:
    """Helper for test data management"""

    @staticmethod
    def create_temp_file(content: str, suffix: str = '.txt') -> str:
        """Create temporary file with content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name

    @staticmethod
    def load_test_data_file(filename: str) -> str:
        """Load content from test data file"""
        test_data_dir = Path(__file__).parent / 'test_data'
        with open(test_data_dir / filename, 'r') as f:
            return f.read()

    @staticmethod
    def get_test_config_dir() -> str:
        """Get path to test configs directory"""
        return str(Path(__file__).parent / 'test_data' / 'configs')

    @staticmethod
    def mock_config_loader(product_name: str):
        """Mock config loader that uses test configs"""
        if product_name == 'TestSwitch':
            config_file = Path(__file__).parent / 'test_data' / 'configs' / 'Platforms' / 'test_platform.json'
            with open(config_file, 'r') as f:
                import json
                return json.load(f)
        return None


def test_helper_create_temp_file():
    """Test temp file creation helper"""
    content = "test content"
    temp_file = TestDataHelper.create_temp_file(content)

    assert os.path.exists(temp_file)
    with open(temp_file, 'r') as f:
        assert f.read() == content

    # Cleanup
    os.unlink(temp_file)


def test_helper_load_test_data():
    """Test loading test data files"""
    content = TestDataHelper.load_test_data_file('sample_clean.txt')

    assert 'SMB SERIAL NUMBER' in content
    assert 'fboss2 show port' in content
    assert 'TestSwitch' in content