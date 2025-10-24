"""
Unit tests for regex detection functionality in log_sanity.py
Tests both single-line and multi-line regex pattern matching with dynamic content.
"""
import unittest
from utils.log_sanity import detect_regex_matches, perform_sanity_checks


class TestRegexDetection(unittest.TestCase):
    """Test regex pattern detection functionality"""

    def test_single_line_regex_basic(self):
        """Test basic single-line regex detection"""
        section = {
            'raw_content': 'This is a test line\nAnother line here\nFinal line'
        }
        regexes = [
            {'name': 'Test Pattern', 'patterns': ['test']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'Regex Match')
        self.assertEqual(result[0]['value'], 'Test Pattern')
        self.assertEqual(result[0]['line'], 0)  # First line (0-indexed)
        self.assertEqual(len(result[0]['line_spans']), 1)
        self.assertEqual(result[0]['line_spans'][0]['line'], 0)
        self.assertEqual(result[0]['line_spans'][0]['span'], [10, 14])  # Position of 'test'

    def test_multiple_patterns_single_regex(self):
        """Test single regex entry with multiple patterns"""
        section = {
            'raw_content': 'Variant1 detected\nVariant2 found\nVariant3 ignored'
        }
        regexes = [
            {'name': 'Multi-Pattern Test', 'patterns': ['Variant1', 'Variant2']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        # Should find both Variant1 and Variant2, but not Variant3
        self.assertEqual(len(result), 2)
        
        # Both should have the same name but different matches
        self.assertTrue(all(r['value'] == 'Multi-Pattern Test' for r in result))
        self.assertEqual(result[0]['line'], 0)  # Variant1 on line 0
        self.assertEqual(result[1]['line'], 1)  # Variant2 on line 1

    def test_multi_line_regex_basic(self):
        """Test basic multi-line regex detection"""
        section = {
            'raw_content': 'Starting process\nERROR: Something went wrong\nProcess failed\nSystem recovered'
        }
        regexes = [
            {'name': 'Error Block', 'patterns': ['ERROR:.*?\\nProcess failed']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'Regex Match')
        self.assertEqual(result[0]['value'], 'Error Block')
        self.assertEqual(result[0]['line'], 1)  # Starts on line 1
        self.assertEqual(len(result[0]['line_spans']), 2)  # Spans 2 lines

    def test_regex_edge_cases(self):
        """Test edge cases for regex detection"""
        
        # Empty content
        section = {'raw_content': ''}
        regexes = [{'name': 'Test', 'patterns': ['test']}]
        result = detect_regex_matches(section, regexes)
        self.assertEqual(len(result), 0)
        
        # Empty regexes
        section = {'raw_content': 'test content'}
        regexes = []
        result = detect_regex_matches(section, regexes)
        self.assertEqual(len(result), 0)
        
        # Missing patterns field
        section = {'raw_content': 'test content'}
        regexes = [{'name': 'Test'}]  # No patterns field at all
        result = detect_regex_matches(section, regexes)
        self.assertEqual(len(result), 0)

    def test_invalid_regex_patterns(self):
        """Test handling of invalid regex patterns"""
        section = {
            'raw_content': 'This is test content'
        }
        regexes = [
            {'name': 'Valid Pattern', 'patterns': ['test']},
            {'name': 'Invalid Pattern', 'patterns': ['[invalid']},  # Unclosed bracket
            {'name': 'Another Valid', 'patterns': ['content']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        # Should only match valid patterns, skip invalid ones
        self.assertEqual(len(result), 2)
        pattern_names = [r['value'] for r in result]
        self.assertIn('Valid Pattern', pattern_names)
        self.assertIn('Another Valid', pattern_names)
        self.assertNotIn('Invalid Pattern', pattern_names)

    def test_regex_integration_with_perform_sanity_checks(self):
        """Test regex detection integrated with perform_sanity_checks"""
        sections = [
            {
                'title': 'Test Section',
                'section_type': 'raw',
                'raw_content': '''System starting up
ERROR: Database connection failed
Attempting retry...
FAILED: Could not establish connection
System shutdown initiated''',
                'parsed_data': {'type': 'raw'}
            }
        ]
        
        regexes = [
            {'name': 'Error Pattern', 'patterns': ['ERROR:.*']},
            {'name': 'Failure Block', 'patterns': ['ERROR:.*?\\n.*?\\nFAILED:.*']}
        ]
        
        result = perform_sanity_checks(sections, None, regexes)
        
        self.assertEqual(len(result), 1)
        section = result[0]
        self.assertIn('anomalies', section)
        
        anomalies = section['anomalies']
        self.assertEqual(len(anomalies), 2)  # Should find both patterns
        
        # Check that anomalies have correct structure
        for anomaly in anomalies:
            self.assertEqual(anomaly['type'], 'Regex Match')
            self.assertIn('line_spans', anomaly)
            self.assertIn('line', anomaly)
            self.assertIn('message', anomaly)

    def test_regex_with_real_showtech_content(self):
        """Test regex detection on realistic showtech content"""
        section = {
            'raw_content': '''### System Information ###
Hostname: switch01.example.com
Uptime: 45 days, 12:34:56

### Error Log ###
2023-12-01 10:30:45 ERROR: Port eth1/1 link down
2023-12-01 10:30:46 WARNING: High temperature detected: 85°C
2023-12-01 10:30:47 INFO: Attempting port recovery
2023-12-01 10:30:48 ERROR: Port recovery failed
2023-12-01 10:30:49 CRITICAL: System overheating

### Stack Trace ###
Traceback (most recent call last):
  File "/usr/bin/port_manager.py", line 123, in recover_port
    self.reset_port(port_id)
  File "/usr/lib/network.py", line 456, in reset_port
    raise PortError("Hardware fault detected")
PortError: Hardware fault detected'''
        }
        
        regexes = [
            {'name': 'Error Log Entry', 'patterns': ['\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2} ERROR:.*']},
            {'name': 'Temperature Warning', 'patterns': ['High temperature.*?\\d+°C']},
            {'name': 'Stack Trace', 'patterns': ['Traceback.*?\\n(?:.*?\\n)*?.*?Error:.*']},
            {'name': 'Critical Alert', 'patterns': ['CRITICAL:.*']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        # Should find multiple matches
        self.assertGreaterEqual(len(result), 4)
        
        pattern_names = [r['value'] for r in result]
        self.assertIn('Error Log Entry', pattern_names)
        self.assertIn('Temperature Warning', pattern_names)
        self.assertIn('Stack Trace', pattern_names)
        self.assertIn('Critical Alert', pattern_names)

    def test_regex_line_span_calculation(self):
        """Test accurate line span calculation for multi-line matches"""
        section = {
            'raw_content': 'Line 0: Start\nLine 1: ERROR occurred here\nLine 2: Details follow\nLine 3: END of error'
        }
        regexes = [
            {'name': 'Multi-line Error', 'patterns': ['ERROR occurred.*?\\n.*?Details.*?\\n.*?END']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['line'], 1)  # Starts on line 1
        self.assertEqual(len(result[0]['line_spans']), 3)  # Spans 3 lines
        
        # Check each line span
        spans = result[0]['line_spans']
        
        # Line 1: "ERROR occurred here" - should start at "ERROR"
        line1_span = next(s for s in spans if s['line'] == 1)
        self.assertEqual(line1_span['span'], [8, 27])  # "ERROR occurred here"

        # Line 2: "Details follow" - full line content matched
        line2_span = next(s for s in spans if s['line'] == 2)
        self.assertEqual(line2_span['span'], [0, 22])  # "Line 2: Details follow"

        # Line 3: "END" - should end at "END"
        line3_span = next(s for s in spans if s['line'] == 3)
        self.assertEqual(line3_span['span'], [0, 11])  # "Line 3: END"

    def test_regex_backward_compatibility(self):
        """Test that new regex format works correctly"""
        section = {
            'raw_content': 'Simple test line\nAnother test here'
        }
        
        regexes = [
            {'name': 'Test Pattern', 'patterns': ['test']}
        ]
        
        result = detect_regex_matches(section, regexes)
        
        self.assertEqual(len(result), 2)
        
        # Each result should have both navigation line and line_spans for highlighting
        for anomaly in result:
            self.assertIn('line', anomaly)  # For navigation
            self.assertIn('line_spans', anomaly)  # For highlighting
            self.assertEqual(len(anomaly['line_spans']), 1)  # Single line match
            self.assertEqual(anomaly['line_spans'][0]['line'], anomaly['line'])


if __name__ == '__main__':
    unittest.main()
