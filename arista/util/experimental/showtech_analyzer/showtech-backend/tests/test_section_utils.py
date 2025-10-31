"""
Section utils tests - Essential utility functions
"""
import pytest
from utils.section_utils import determine_section_type, extract_bit_field


class TestDetermineSectionType:
    """Test section type detection"""
    
    def test_table_type_detection(self):
        """Test table type detection"""
        assert determine_section_type('fboss2 show port') == 'table'
        assert determine_section_type('fboss2 show environment sensor') == 'table'
        assert determine_section_type('LSPCI') == 'lspci'
    
    def test_key_value_type_detection(self):
        """Test key-value type detection"""
        assert determine_section_type('SMB SERIAL NUMBER') == 'key_value'
        assert determine_section_type('fboss2 show product') == 'key_value'
    
    def test_i2c_dump_detection(self):
        """Test i2c dump detection"""
        assert determine_section_type('i2cdump -y 1 0x58 b') == 'i2c_dump'
        assert determine_section_type('I2CDUMP -y 1 0x58 b') == 'i2c_dump'
    
    def test_unknown_section_type(self):
        """Test unknown section defaults to raw"""
        assert determine_section_type('unknown section title') == 'raw'
        assert determine_section_type('random text here') == 'raw'


class TestExtractBitField:
    """Test bit field extraction"""
    
    def test_extract_bit_field_basic(self):
        """Test basic bit field extraction"""
        # Extract bits 7-4 from 0xAB (10101011)
        # Bits 7-4 = 1010 = 0xA
        result = extract_bit_field('0xAB', '7:4')
        assert result == 0xA

    def test_extract_single_bit(self):
        """Test extracting single bit"""
        # Extract bit 3 from 0x08 (00001000)
        # Bit 3 = 1
        result = extract_bit_field('0x08', '3')
        assert result == 1

    def test_extract_all_bits(self):
        """Test extracting all bits"""
        result = extract_bit_field('0xFF', '7:0')
        assert result == 0xFF

    def test_extract_lower_bits(self):
        """Test extracting lower bits"""
        # Extract bits 3-0 from 0x5A (01011010)
        # Bits 3-0 = 1010 = 0xA
        result = extract_bit_field('0x5A', '3:0')
        assert result == 0xA
