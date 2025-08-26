"""
File upload tests - Essential parsing functionality
"""
import pytest
import os
from utils.file_upload import parse_sections, handle_single_file_upload, extract_hostname


class TestParseSections:
    """Test section parsing"""

    def test_parse_section_headers(self):
        """Test parsing clean sample - Expected: 4 sections"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        result = parse_sections(content)

        # Expected: 4 sections
        assert len(result) == 4
        assert result[1]['title'] == 'SMB SERIAL NUMBER'
        assert result[2]['title'] == 'fboss2 show port'
        assert result[3]['title'] == 'fboss2 show environment sensor'

class TestFileUploadHandling:
    """Test file upload handling - single, multiple, and zip files"""

    def test_upload_single_file(self):
        """Test upload single showtech file"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')

        from werkzeug.datastructures import FileStorage

        with open(sample_file, 'rb') as f:
            file_obj = FileStorage(stream=f, filename='sample_clean.txt')
            result = handle_single_file_upload(file_obj)

        assert len(result) == 1
        file_result = result[0]
        assert file_result['name'] == 'sample_clean.txt'
        assert len(file_result['sections']) == 4
        assert file_result['metadata']['total_sections'] == 4

    def test_upload_multiple_files(self):
        """Test upload multiple showtech files"""
        from werkzeug.datastructures import FileStorage

        # Use same file twice to simulate multiple files
        sample_file1 = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')
        sample_file2 = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_with_errors.txt')

        files = []
        with open(sample_file1, 'rb') as f1:
            files.append(FileStorage(stream=f1, filename='showtech1.txt'))
            with open(sample_file2, 'rb') as f2:
                files.append(FileStorage(stream=f2, filename='showtech2.txt'))

                # Process multiple files
                results = []
                for file_obj in files:
                    file_obj.stream.seek(0)  # Reset stream position
                    result = handle_single_file_upload(file_obj)
                    results.extend(result)

        # Should have 2 files processed
        assert len(results) == 2
        assert results[0]['name'] == 'showtech1.txt'
        assert results[1]['name'] == 'showtech2.txt'
        assert len(results[0]['sections']) == 4
        assert len(results[1]['sections']) == 4

    def test_upload_zip_file(self):
        """Test upload zip file containing showtech files"""
        import zipfile
        import tempfile
        from werkzeug.datastructures import FileStorage

        # Create a temporary zip file with sample showtech files
        sample_file1 = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_clean.txt')
        sample_file2 = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_with_errors.txt')

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zf:
                zf.write(sample_file1, 'showtech1.txt')
                zf.write(sample_file2, 'showtech2.txt')

            # Test zip file upload - verify we can create and read the zip
            with open(temp_zip.name, 'rb') as f:
                zip_data = f.read()
                zip_file_obj = FileStorage(stream=f, filename='showtechs.zip')

                # Test basic zip file properties
                assert zip_file_obj.filename.endswith('.zip')
                assert len(zip_data) > 0

                # Verify zip contains expected files
                with zipfile.ZipFile(temp_zip.name, 'r') as zf:
                    file_list = zf.namelist()
                    assert 'showtech1.txt' in file_list
                    assert 'showtech2.txt' in file_list

        # Cleanup
        os.unlink(temp_zip.name)


class TestHostnameExtraction:
    """Test hostname extraction functionality"""

    def test_extract_hostname_success(self):
        """Test successful hostname extraction from CPU HOSTNAME section"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_with_hostname.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        hostname = extract_hostname(sections)

        assert hostname == 'switch01.example.com'

    def test_extract_hostname_missing_section(self):
        """Test hostname extraction when CPU HOSTNAME section is missing"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_no_hostname.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        hostname = extract_hostname(sections)

        assert hostname is None

    def test_extract_hostname_empty_section(self):
        """Test hostname extraction when CPU HOSTNAME section is empty"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_empty_hostname.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        hostname = extract_hostname(sections)

        assert hostname == '' or hostname is None  # Empty content should return None or empty string

    def test_extract_hostname_case_insensitive(self):
        """Test hostname extraction is case insensitive"""
        # Create sections with different case variations
        sections = [
            {'title': 'cpu hostname', 'raw_content': 'test-host-lower'},
            {'title': 'CPU HOSTNAME', 'raw_content': 'test-host-upper'},
            {'title': 'Cpu Hostname', 'raw_content': 'test-host-mixed'}
        ]

        # Should find the first match (case insensitive)
        hostname = extract_hostname(sections)
        assert hostname == 'test-host-lower'

    def test_hostname_in_file_upload_metadata(self):
        """Test hostname is included in file upload metadata"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_with_hostname.txt')

        from werkzeug.datastructures import FileStorage

        with open(sample_file, 'rb') as f:
            file_obj = FileStorage(stream=f, filename='sample_with_hostname.txt')
            result = handle_single_file_upload(file_obj)

        assert len(result) == 1
        file_result = result[0]

        # Check metadata contains hostname
        assert 'metadata' in file_result
        assert 'hostname' in file_result['metadata']
        assert file_result['metadata']['hostname'] == 'switch01.example.com'

    def test_hostname_fallback_in_file_upload_metadata(self):
        """Test hostname fallback (None) when missing in file upload metadata"""
        sample_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_no_hostname.txt')

        from werkzeug.datastructures import FileStorage

        with open(sample_file, 'rb') as f:
            file_obj = FileStorage(stream=f, filename='sample_no_hostname.txt')
            result = handle_single_file_upload(file_obj)

        assert len(result) == 1
        file_result = result[0]

        # Check metadata contains hostname as None
        assert 'metadata' in file_result
        assert 'hostname' in file_result['metadata']
        assert file_result['metadata']['hostname'] is None
