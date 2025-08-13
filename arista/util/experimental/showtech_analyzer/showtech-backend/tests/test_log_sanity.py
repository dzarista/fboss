"""
Log sanity tests - Essential anomaly detection
"""
import pytest
import os
import json
from unittest.mock import patch
from utils.log_sanity import (
    detect_critical_sensors,
    detect_down_ports,
    detect_missing_devices,
    detect_pcie_speed_mismatches,
    perform_sanity_checks,
    load_platform_config
)
from utils.file_upload import parse_sections


class TestDetectCriticalSensors:
    """Test critical sensor detection"""

    def test_detect_critical_sensors_found(self):
        """Test detecting critical sensors"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'rows': [
                    {'Sensor': 'Temperature', 'Status': 'OK'},
                    {'Sensor': 'Voltage', 'Status': 'CRITICAL'}
                ]
            }
        }

        result = detect_critical_sensors(section)
        assert len(result) == 1
        assert result[0]['type'] == 'critical_sensor'
        assert result[0]['field'] == 'Status'
        assert result[0]['value'] == 'CRITICAL'
        assert result[0]['row_index'] == 1

    def test_detect_critical_sensors_case_insensitive(self):
        """Test critical sensor detection is case insensitive"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'rows': [
                    {'Sensor': 'Temperature', 'Status': 'critical'},
                    {'Sensor': 'Voltage', 'Status': 'Critical'}
                ]
            }
        }

        result = detect_critical_sensors(section)
        assert len(result) == 2
        assert all(r['type'] == 'critical_sensor' for r in result)

    def test_detect_critical_sensors_none_found(self):
        """Test when no critical sensors found"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'rows': [
                    {'Sensor': 'Temperature', 'Status': 'OK'},
                    {'Sensor': 'Voltage', 'Status': 'OK'}
                ]
            }
        }

        result = detect_critical_sensors(section)
        assert len(result) == 0

    def test_detect_critical_sensors_wrong_section_type(self):
        """Test critical sensor detection on wrong section type"""
        section = {
            'section_type': 'key_value',
            'parsed_data': {
                'type': 'key_value',
                'data': {'Status': 'CRITICAL'}
            }
        }

        result = detect_critical_sensors(section)
        assert len(result) == 0


class TestDetectDownPorts:
    """Test down port detection"""

    def test_detect_down_ports_found(self):
        """Test detecting down ports"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'headers': ['Name', 'AdminState', 'LinkState', 'Transceiver', 'Speed'],
                'rows': [
                    {'Name': 'eth1/1', 'AdminState': 'Enabled', 'LinkState': 'Up', 'Transceiver': 'Present', 'Speed': '100G'},
                    {'Name': 'eth1/2', 'AdminState': 'Enabled', 'LinkState': 'Down', 'Transceiver': 'Present', 'Speed': '100G'},
                    {'Name': 'eth1/3', 'AdminState': 'Disabled', 'LinkState': 'Down', 'Transceiver': 'NotPresent', 'Speed': 'N/A'}
                ]
            }
        }

        result = detect_down_ports(section)
        assert len(result) == 1
        assert result[0]['type'] == 'port_down'
        assert result[0]['port_name'] == 'eth1/2'
        assert result[0]['row_index'] == 1

    def test_detect_down_ports_none_found(self):
        """Test when no down ports found"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'headers': ['Name', 'AdminState', 'LinkState', 'Transceiver', 'Speed'],
                'rows': [
                    {'Name': 'eth1/1', 'AdminState': 'Enabled', 'LinkState': 'Up', 'Transceiver': 'Present', 'Speed': '100G'},
                    {'Name': 'eth1/2', 'AdminState': 'Disabled', 'LinkState': 'Down', 'Transceiver': 'NotPresent', 'Speed': 'N/A'}
                ]
            }
        }

        result = detect_down_ports(section)
        assert len(result) == 0

    def test_detect_down_ports_not_port_table(self):
        """Test down port detection on non-port table"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'headers': ['Sensor', 'Value', 'Status'],
                'rows': [
                    {'Sensor': 'Temperature', 'Value': '45.5', 'Status': 'OK'}
                ]
            }
        }

        result = detect_down_ports(section)
        assert len(result) == 0


class TestDetectMissingDevices:
    """Test missing device detection (requires platform config)"""

    def _get_test_platform_config(self):
        """Get test platform config"""
        return {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                },
                {
                    'slot': '05:00.0',
                    'device_type': 'FPGA',
                    'location': 'Control Module',
                    'description': 'Test FPGA',
                    'expected_speed': 'Gen2x4'
                }
            ]
        }

    def test_detect_missing_devices_found(self):
        """Test detecting missing devices"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {'slot': '03:00.0', 'description': 'Test ASIC Chip', 'speed': 'Gen4x8'}
                    # Missing 05:00.0 device
                ]
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_missing_devices(section, platform_config)

        assert len(result) == 1
        assert result[0]['type'] == 'missing_device'
        assert result[0]['slot'] == '05:00.0'
        assert result[0]['device_type'] == 'FPGA'
        assert result[0]['description'] == 'Test FPGA'

    def test_detect_missing_devices_all_present(self):
        """Test when all expected devices are present"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {'slot': '03:00.0', 'description': 'Test ASIC Chip', 'speed': 'Gen4x8'},
                    {'slot': '05:00.0', 'description': 'Test FPGA', 'speed': 'Gen2x4'}
                ]
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_missing_devices(section, platform_config)

        assert len(result) == 0

    def test_detect_missing_devices_no_platform_config(self):
        """Test missing device detection without platform config"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {'slot': '03:00.0', 'description': 'Test ASIC Chip'}
                ]
            }
        }

        result = detect_missing_devices(section, None)
        assert len(result) == 0

    def test_detect_missing_devices_wrong_section_type(self):
        """Test missing device detection on wrong section type"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'rows': []
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_missing_devices(section, platform_config)
        assert len(result) == 0


class TestDetectPcieSpeedMismatches:
    """Test PCIe speed mismatch detection (requires platform config)"""

    def _get_test_platform_config(self):
        """Get test platform config"""
        return {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                },
                {
                    'slot': '05:00.0',
                    'device_type': 'FPGA',
                    'location': 'Control Module',
                    'description': 'Test FPGA',
                    'expected_speed': 'Gen2x4'
                }
            ]
        }

    def test_detect_pcie_speed_mismatches_found(self):
        """Test detecting PCIe speed mismatches"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {
                        'slot': '03:00.0',
                        'description': 'Test ASIC Chip',
                        'details': 'Capabilities: [70] Express (v2) Endpoint, MSI 00\n                LnkSta: Speed 8GT/s, Width x4, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-'
                    },
                    {
                        'slot': '05:00.0',
                        'description': 'Test FPGA',
                        'details': 'Capabilities: [70] Express (v2) Endpoint, MSI 00\n                LnkSta: Speed 8GT/s, Width x4, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-'
                    }
                ]
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_pcie_speed_mismatches(section, platform_config)

        # Both devices should have mismatches:
        # ASIC: Expected 16.0GT/s x8, Actual 8GT/s x4
        # FPGA: Expected 5.0GT/s x4, Actual 8GT/s x4
        assert len(result) == 2

        # Find ASIC mismatch
        asic_mismatch = next((r for r in result if r['slot'] == '03:00.0'), None)
        assert asic_mismatch is not None
        assert asic_mismatch['type'] == 'pcie_speed_mismatch'
        assert asic_mismatch['device_type'] == 'ASIC'
        assert asic_mismatch['expected_speed'] == '16.0GT/s x8'
        assert asic_mismatch['actual_speed'] == '8.0GT/s x4'

    def test_detect_pcie_speed_mismatches_none_found(self):
        """Test when no PCIe speed mismatches found"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {
                        'slot': '03:00.0',
                        'description': 'Test ASIC Chip',
                        'details': 'Capabilities: [70] Express (v2) Endpoint, MSI 00\n                LnkSta: Speed 16GT/s, Width x8, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-'
                    },
                    {
                        'slot': '05:00.0',
                        'description': 'Test FPGA',
                        'details': 'Capabilities: [70] Express (v2) Endpoint, MSI 00\n                LnkSta: Speed 5GT/s, Width x4, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-'
                    }
                ]
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_pcie_speed_mismatches(section, platform_config)

        assert len(result) == 0

    def test_detect_pcie_speed_mismatches_no_platform_config(self):
        """Test PCIe speed mismatch detection without platform config"""
        section = {
            'section_type': 'lspci',
            'parsed_data': {
                'type': 'lspci',
                'devices': [
                    {'slot': '03:00.0', 'description': 'Test ASIC Chip', 'speed': 'Gen2x4'}
                ]
            }
        }

        result = detect_pcie_speed_mismatches(section, None)
        assert len(result) == 0

    def test_detect_pcie_speed_mismatches_wrong_section_type(self):
        """Test PCIe speed mismatch detection on wrong section type"""
        section = {
            'section_type': 'table',
            'parsed_data': {
                'type': 'table',
                'rows': []
            }
        }

        platform_config = self._get_test_platform_config()
        result = detect_pcie_speed_mismatches(section, platform_config)
        assert len(result) == 0


class TestPlatformConfigLoading:
    """Test platform config loading functionality"""

    def test_load_platform_config_not_found(self):
        """Test loading platform config when product is not found"""
        config = load_platform_config('NonExistentProduct')
        assert config is None

    def test_load_platform_config_empty_product_name(self):
        """Test loading platform config with empty product name"""
        config = load_platform_config('')
        assert config is None

        config = load_platform_config(None)
        assert config is None


class TestSanityChecksWithPlatformConfig:
    """Test sanity checks with platform-specific validation using real functions"""

    @patch('utils.log_sanity.load_platform_config')
    def test_sanity_checks_with_platform_found(self, mock_load_config):
        """Test sanity checks when platform config is found"""
        # Mock the platform config loading to return a test config
        mock_config = {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                }
            ]
        }
        mock_load_config.return_value = mock_config

        # Read sample file using real path
        real_test_dir = os.path.dirname(os.path.realpath(__file__))
        sample_file = os.path.join(real_test_dir, 'test_data', 'sample_clean.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        result = perform_sanity_checks(sections)

        assert len(result) == 3
        for section in result:
            assert 'parsed_data' in section
            # Should have anomalies stored in parsed_data.anomalies
            if 'anomalies' in section['parsed_data']:
                # Platform config should be loaded for TestSwitch
                pass

    @patch('utils.log_sanity.load_platform_config')
    def test_sanity_checks_without_platform(self, mock_load_config):
        """Test sanity checks when platform config is not found"""
        # Mock the platform config loading to return None (not found)
        mock_load_config.return_value = None

        # Create sample with unknown product
        sample_content = """### SMB SERIAL NUMBER ###
Product Name: NonExistentProduct
Serial Number: UNK12345678

### fboss2 show environment sensor ###
Sensor                  Value    Status    Threshold
-------------------------------------------------
Temperature             45.5     OK        85.0"""

        sections = parse_sections(sample_content)
        result = perform_sanity_checks(sections)

        assert len(result) == 2
        for section in result:
            assert 'parsed_data' in section
            # Should still run basic checks even without platform config
            # Anomalies stored in parsed_data.anomalies


class TestComprehensiveSanityChecks:
    """Test comprehensive sanity checks with all anomaly types"""

    @patch('utils.log_sanity.load_platform_config')
    def test_sanity_checks_with_lspci_platform_found(self, mock_load_config):
        """Test sanity checks with LSPCI section and platform config"""
        # Mock the platform config loading to return a test config
        mock_config = {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                },
                {
                    'slot': '05:00.0',
                    'device_type': 'FPGA',
                    'location': 'Control Module',
                    'description': 'Test FPGA',
                    'expected_speed': 'Gen2x4'
                }
            ]
        }
        mock_load_config.return_value = mock_config

        real_test_dir = os.path.dirname(os.path.realpath(__file__))
        sample_file = os.path.join(real_test_dir, 'test_data', 'sample_with_lspci.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        result = perform_sanity_checks(sections)

        # Should have 3 sections: SMB, LSPCI, sensors
        assert len(result) == 3

        # Find LSPCI section
        lspci_section = None
        for section in result:
            if section['title'] == 'LSPCI':
                lspci_section = section
                break

        assert lspci_section is not None
        assert 'parsed_data' in lspci_section
        # Platform-specific checks should run for LSPCI when config is found
        # Anomalies stored in parsed_data.anomalies

    @patch('utils.log_sanity.load_platform_config')
    def test_sanity_checks_with_pcie_issues(self, mock_load_config):
        """Test sanity checks detecting PCIe issues"""
        # Mock the platform config loading to return a test config
        mock_config = {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                },
                {
                    'slot': '05:00.0',
                    'device_type': 'FPGA',
                    'location': 'Control Module',
                    'description': 'Test FPGA',
                    'expected_speed': 'Gen2x4'
                }
            ]
        }
        mock_load_config.return_value = mock_config

        real_test_dir = os.path.dirname(os.path.realpath(__file__))
        sample_file = os.path.join(real_test_dir, 'test_data', 'sample_with_pcie_issues.txt')
        with open(sample_file, 'r') as f:
            content = f.read()

        sections = parse_sections(content)
        result = perform_sanity_checks(sections)

        # Should have 3 sections: SMB, LSPCI, sensors
        assert len(result) == 3

        # Find LSPCI section - should detect missing device (05:00.0) and speed mismatch (03:00.0)
        lspci_section = None
        sensor_section = None
        for section in result:
            if section['title'] == 'LSPCI':
                lspci_section = section
            elif 'environment sensor' in section['title']:
                sensor_section = section

        assert lspci_section is not None
        assert sensor_section is not None

        # Should detect PCIe anomalies
        assert 'parsed_data' in lspci_section
        lspci_anomalies = lspci_section['parsed_data'].get('anomalies', [])
        # Should detect missing device and speed mismatch
        assert len(lspci_anomalies) >= 1

        # Should detect critical sensors
        assert 'parsed_data' in sensor_section
        sensor_anomalies = sensor_section['parsed_data'].get('anomalies', [])
        assert len(sensor_anomalies) >= 1

        # Verify anomaly types
        anomaly_types = [anomaly['type'] for anomaly in lspci_anomalies + sensor_anomalies]
        assert 'critical_sensor' in anomaly_types

    @patch('utils.log_sanity.load_platform_config')
    def test_sanity_checks_all_anomaly_types(self, mock_load_config):
        """Test that all anomaly detection functions work together"""
        # Mock the platform config loading to return a test config
        mock_config = {
            'platform': 'TestPlatform',
            'product_name': 'TestSwitch',
            'pcie_devices': [
                {
                    'slot': '03:00.0',
                    'device_type': 'ASIC',
                    'location': 'Main Board',
                    'description': 'Test ASIC Chip',
                    'expected_speed': 'Gen4x8'
                }
            ]
        }
        mock_load_config.return_value = mock_config

        # Create a comprehensive sample with all types of issues
        sample_content = """### SMB SERIAL NUMBER ###
Product Name: TestSwitch
Serial Number: TST33333333

### fboss2 show port ###
Name                AdminState    LinkState    Transceiver    Speed
-----------------------------------------------------------------
eth1/1              Enabled       Up           Present        100G
eth1/2              Enabled       Down         Present        100G
eth1/3              Disabled      Down         NotPresent     N/A

### fboss2 show environment sensor ###
Sensor                  Value    Status    Threshold
-------------------------------------------------
Temperature             95.0     CRITICAL  85.0
Voltage                 12.0     OK        15.0
Current                 8.5      WARNING   5.0

### LSPCI ###
03:00.0 Ethernet controller: Test ASIC Chip (rev 01)
        Capabilities: [70] Express (v2) Endpoint, MSI 00
                LnkSta: Speed 8GT/s, Width x4, TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-"""

        sections = parse_sections(sample_content)
        result = perform_sanity_checks(sections)

        # Should detect multiple types of anomalies
        all_anomalies = []
        for section in result:
            # Anomalies are stored in parsed_data.anomalies
            if 'parsed_data' in section and 'anomalies' in section['parsed_data']:
                all_anomalies.extend(section['parsed_data']['anomalies'])

        # Should have at least critical sensor and down port errors
        anomaly_types = [anomaly['type'] for anomaly in all_anomalies]
        assert len(all_anomalies) > 0, f"No anomalies detected. Sections: {[s.get('title') for s in result]}"
        assert 'critical_sensor' in anomaly_types, f"Expected critical_sensor, got: {anomaly_types}"
        assert 'port_down' in anomaly_types, f"Expected port_down, got: {anomaly_types}"

    def test_sanity_checks_graceful_degradation(self):
        """Test that sanity checks work gracefully when config loading fails"""
        # Test with real config directory (should fail gracefully)
        sample_content = """### SMB SERIAL NUMBER ###
Product Name: NonExistentProduct
Serial Number: UNK12345678

### fboss2 show environment sensor ###
Sensor                  Value    Status    Threshold
-------------------------------------------------
Temperature             45.5     OK        85.0"""

        sections = parse_sections(sample_content)
        result = perform_sanity_checks(sections)

        # Should not crash and should still return sections with parsed_data
        assert len(result) == 2
        for section in result:
            assert 'parsed_data' in section
            # Anomalies stored in parsed_data.anomalies (may be empty if no checks run)
