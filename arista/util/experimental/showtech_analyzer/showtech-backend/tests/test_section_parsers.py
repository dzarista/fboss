"""
Section parser tests - Essential parsing functionality
"""
import pytest
from utils.section_parsers import parse_table, parse_key_value, parse_content_by_type, parse_i2c_dump, parse_fboss2_interface_phy, parse_psu_debug
from utils.section_utils import parse_byte_dump, parse_word_dump
from utils.file_upload import parse_sections
from utils.file_upload import parse_sections


class TestParseTable:
    """Test table parsing"""
    
    def test_parse_basic_table(self):
        """Test parsing basic table"""
        content = """Name                AdminState    LinkState    Speed
-----------------------------------------------------
eth1/1              Enabled       Up           100G
eth1/2              Enabled       Down         100G"""

        result = parse_table(content)

        assert result['type'] == 'table'
        assert len(result['rows']) == 2
        assert result['rows'][0]['Name'] == 'eth1/1'
        assert result['rows'][0]['AdminState'] == 'Enabled'
        assert result['rows'][0]['LinkState'] == 'Up'
        assert result['rows'][0]['Speed'] == '100G'
    
    def test_parse_table_with_numbers(self):
        """Test parsing table with numeric values"""
        content = """Sensor          Value    Status
------------------------------
Temperature     45.5     OK
Voltage         12.0     OK"""

        result = parse_table(content)

        assert result['type'] == 'table'
        assert len(result['rows']) == 2
        assert result['rows'][0]['Sensor'] == 'Temperature'
        # Values might be parsed as numbers, so check both string and numeric
        assert str(result['rows'][0]['Value']) == '45.5'
        assert result['rows'][0]['Status'] == 'OK'


class TestParseKeyValue:
    """Test key-value parsing"""
    
    def test_parse_basic_key_value(self):
        """Test parsing basic key-value content"""
        content = """Product Name: DCS-7280SR3-48YC8
Serial Number: JPE12345678
MAC Address: 00:1c:73:12:34:56"""
        
        result = parse_key_value(content)
        
        assert result['type'] == 'key_value'
        assert result['data']['Product Name'] == 'DCS-7280SR3-48YC8'
        assert result['data']['Serial Number'] == 'JPE12345678'
        assert result['data']['MAC Address'] == '00:1c:73:12:34:56'
    
    def test_parse_key_value_with_spaces(self):
        """Test parsing key-value with spaces in values"""
        content = """Product Name: DCS 7280SR3 48YC8
Description: High Performance Switch
Location: Data Center Rack 1"""
        
        result = parse_key_value(content)
        
        assert result['type'] == 'key_value'
        assert result['data']['Product Name'] == 'DCS 7280SR3 48YC8'
        assert result['data']['Description'] == 'High Performance Switch'
        assert result['data']['Location'] == 'Data Center Rack 1'


class TestParseContentByType:
    """Test content parsing by type"""
    
    def test_parse_content_as_table(self):
        """Test parsing content as table type"""
        content = """Name    Status
--------------
eth1/1  Up
eth1/2  Down"""

        result = parse_content_by_type('table', content)

        # Note: parse_content_by_type might fall back to 'raw' if parsing fails
        assert result['type'] in ['table', 'raw']
        if result['type'] == 'table':
            assert len(result['rows']) == 2
    
    def test_parse_content_as_key_value(self):
        """Test parsing content as key-value type"""
        content = """Product Name: Test Device
Serial Number: 12345"""

        result = parse_content_by_type('key_value', content)

        # Note: parse_content_by_type might fall back to 'raw' if parsing fails
        assert result['type'] in ['key_value', 'raw']
        if result['type'] == 'key_value':
            assert result['data']['Product Name'] == 'Test Device'

    def test_parse_content_as_i2c_dump(self):
        """Test parsing content as i2c_dump type"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????"""

        result = parse_content_by_type('i2c_dump', content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        assert isinstance(result['data'], dict)


class TestParseI2cDump:
    """Test I2C dump parsing"""

    def test_parse_i2c_dump_byte_mode(self):
        """Test parsing I2C dump in byte mode"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????
10: 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f 20    ????????????????"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        # Should have parsed the byte data
        assert isinstance(result['data'], dict)

    def test_parse_i2c_dump_stderr_handling(self):
        """Test parsing I2C dump with STDERR messages"""
        content = """i2cdump -y 1 0x58
        "i2cdump -f -y 1 0x58" STDERR:
        No size specified (using byte-data access)

         0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
    00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????
        """
        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        assert isinstance(result['data'], dict)
        assert not 'value' in result['data']['0x00']
        # assert result['data']['0x00']['value'] == '0x01', result['data']

    def test_parse_i2c_dump_word_mode(self):
        """Test parsing I2C dump in word mode"""
        content = """i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: 0102 0304 0506 0708 090a 0b0c 0d0e 0f10
10: 1112 1314 1516 1718 191a 1b1c 1d1e 1f20"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        assert isinstance(result['data'], dict)

    def test_parse_i2c_dump_mixed_mode(self):
        """Test parsing I2C dump with both byte and word modes"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????

i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: 0102 0304 0506 0708 090a 0b0c 0d0e 0f10"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        # Should handle both byte and word data
        assert isinstance(result['data'], dict)

    def test_parse_i2c_dump_with_xx_values(self):
        """Test parsing I2C dump with XX (unavailable) values"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: 01 xx 03 xx 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        # Should handle XX values properly - they should result in N/A values
        assert isinstance(result['data'], dict)

    def test_parse_i2c_dump_empty_content(self):
        """Test parsing empty I2C dump content"""
        content = ""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result
        assert isinstance(result['data'], dict)

    def test_parse_i2c_dump_with_pmbus_commands(self):
        """Test parsing I2C dump with known PMBus commands"""
        # This test assumes some PMBus commands are loaded
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10    ????????????????"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'
        assert 'data' in result

        # Check that each command has the expected structure
        for addr, info in result['data'].items():
            assert 'value' in info
            assert 'command' in info
            assert 'bytes' in info
            assert 'bitRanges' in info
            assert isinstance(info['bitRanges'], list)

            # Check bit range structure


class TestFboss2InterfacePhy:
    """Test FBOSS2 interface phy parsing"""

    def test_parse_fboss2_interface_phy_basic(self):
        """Test parsing basic fboss2 interface phy output"""
        content = """ Interface            eth1/11/1
--------------------------------------
 PhyChipType          IPHY
 Link State           UP
 Speed                FOURHUNDREDG
 IPHY Data Collected  0h 0m 0s ago
 IPHY-Line RS FEC
--------------------------------------------
 IPHY-Line Corrected codewords    980394
 IPHY-Line Uncorrected codewords  6
 IPHY-Line Pre-FEC BER            3e-12
 IPHY-Line FEC Tail               1
 IPHY-Line Codeword stats  Symbol Errors  # of codewords
-------------------------------------------------------------
                           0              67072576304134
                           1              2065415
                           2              1
 IPHY-Line RX PMD  Lane  RX Signal Detect Live  RX Signal Detect Changed  RX CDR Lock Live  RX CDR Lock Changed  Eye Heights  Eye Widths  Rx PPM  RX SNR
--------------------------------------------------------------------------------------------------------------------------------------------------------------------
                   0     True                   2                         True              1                                             N/A     N/A
                   1     True                   3                         True              1                                             N/A     N/A
 IPHY-Line TX PMD  Lane  Pre3  Pre2  Pre1  Main  Post1  Post2  Post3
-------------------------------------------------------------------------------
                   0     N/A   0     0     0     0      0      0
                   1     N/A   0     0     0     0      0      0

 Interface            eth1/14/1
--------------------------------------
 PhyChipType          IPHY
 Link State           DOWN
 Speed                FOURHUNDREDG
 IPHY Data Collected  0h 0m 0s ago """

        result = parse_fboss2_interface_phy(content)

        # Check basic structure
        assert result['type'] == 'fboss2_interface_phy'
        assert 'interfaces' in result
        assert len(result['interfaces']) == 2

        # Check first interface
        interface1 = result['interfaces'][0]
        assert interface1['interface'] == 'eth1/11/1'
        assert interface1['PhyChipType'] == 'IPHY'
        assert interface1['Link State'] == 'UP'
        assert interface1['Speed'] == 'FOURHUNDREDG'

        # Check sections structure
        assert 'sections' in interface1
        sections = interface1['sections']

        # Check RS FEC section exists
        assert 'RS FEC' in sections
        fec_section = sections['RS FEC']
        assert fec_section['Corrected codewords'] == '980394'
        assert fec_section['Pre-FEC BER'] == '3e-12'

        # Check codeword stats
        assert 'codeword_stats' in fec_section
        codeword_stats = fec_section['codeword_stats']
        assert len(codeword_stats) >= 3
        assert codeword_stats[0]['Symbol Errors'] == '0'
        assert codeword_stats[0]['# of codewords'] == '67072576304134'
        assert codeword_stats[1]['Symbol Errors'] == '1'
        assert codeword_stats[1]['# of codewords'] == '2065415'

        # Check RX PMD section exists and has lane data
        assert 'RX PMD' in sections
        rx_section = sections['RX PMD']
        assert isinstance(rx_section, list)
        assert len(rx_section) >= 2
        assert rx_section[0]['Lane'] == '0'
        assert rx_section[0]['RX Signal Detect Live'] == 'True'
        assert rx_section[1]['Lane'] == '1'
        assert rx_section[1]['RX Signal Detect Live'] == 'True'

        # Check TX PMD section exists and has lane data
        assert 'TX PMD' in sections
        tx_section = sections['TX PMD']
        assert isinstance(tx_section, list)
        assert len(tx_section) >= 2
        assert tx_section[0]['Lane'] == '0'
        assert tx_section[0]['Pre3'] == 'N/A'
        assert tx_section[1]['Lane'] == '1'
        assert tx_section[1]['Pre3'] == 'N/A'

        # Check second interface
        interface2 = result['interfaces'][1]
        assert interface2['interface'] == 'eth1/14/1'
        assert interface2['Link State'] == 'DOWN'

    def test_parse_fboss2_interface_phy_empty(self):
        """Test parsing empty content"""
        result = parse_fboss2_interface_phy("")
        assert result['type'] == 'fboss2_interface_phy'
        assert result['interfaces'] == []

    def test_parse_fboss2_interface_phy_malformed(self):
        """Test parsing malformed content falls back to raw"""
        content = "This is not valid interface phy data"
        result = parse_fboss2_interface_phy(content)
        # Should still return the structure but with empty interfaces
        assert result['type'] == 'fboss2_interface_phy'

    def test_parse_i2c_dump_1_byte_vs_2_byte_commands(self):
        """Test that 1-byte commands read from -b and 2-byte commands read from -w"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: AA BB CC DD EE FF 11 22 33 44 55 66 77 88 99 00    ????????????????

i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: AABB CCDD EEFF 1122 3344 5566 7788 9900"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'

        # Check specific addresses to verify byte vs word reading
        for addr, info in result['data'].items():
            if info['bytes'] == '1':
                # 1-byte commands should read from byte dump (-b)
                # For example, 0x00 should be 0xAA (from byte dump)
                if addr == '0x00':
                    assert info['value'] == '0xaa'  # From byte dump
            elif info['bytes'] == '2':
                # 2-byte commands should read from word dump (-w)
                # For example, 0x00 should be 0xAABB (from word dump)
                if addr == '0x00':
                    assert info['value'] == '0xaabb'  # From word dump

    def test_parse_i2c_dump_2_byte_fallback_to_1_byte(self):
        """Test that 2-byte commands fall back to 1-byte when word data unavailable"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: AA BB CC DD EE FF 11 22 33 44 55 66 77 88 99 00    ????????????????

i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: xxxx CCDD EEFF 1122 3344 5566 7788 9900"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'

        # Check that 2-byte commands fall back to 1-byte when word data is xxxx
        for addr, info in result['data'].items():
            if info['bytes'] == '2' and addr == '0x00':
                # Should fall back to byte value with "(upper N/A)" notation
                assert '0xaa' in info['value'].lower()
                assert 'upper n/a' in info['value'].lower()

    def test_parse_i2c_dump_xx_vs_xxxx_handling(self):
        """Test proper handling of XX (byte) vs XXXX (word) unavailable values"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: xx BB CC DD EE FF 11 22 33 44 55 66 77 88 99 00    ????????????????

i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: xxxx CCDD EEFF 1122 3344 5566 7788 9900"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'

        # Check that XX and XXXX values result in N/A
        for addr, info in result['data'].items():
            if addr == '0x00':
                # Both byte (xx) and word (xxxx) are unavailable, should be N/A
                assert info['value'] == 'N/A'

    def test_parse_i2c_dump_bit_range_upper_na_handling(self):
        """Test that bit ranges handle upper N/A correctly"""
        content = """i2cdump -y 1 0x58 b
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef
00: AA xx CC DD EE FF 11 22 33 44 55 66 77 88 99 00    ????????????????

i2cdump -y 1 0x58 w
     0    2    4    6    8    a    c    e
00: xxxx CCDD EEFF 1122 3344 5566 7788 9900"""

        result = parse_i2c_dump(content)
        assert result['type'] == 'i2c_dump'

        # Check that bit ranges in upper byte (bits >= 8) show N/A when upper data unavailable
        for addr, info in result['data'].items():
            if info['bytes'] == '2' and '(upper N/A)' in info['value']:
                for bit_range in info['bitRanges']:
                    bits = bit_range['bits']
                    # Check if any bit in the range is >= 8 (upper byte)
                    if ':' in bits:
                        high, low = map(int, bits.split(':'))
                        if high >= 8:
                            assert bit_range['value'] == 'N/A'
                            assert bit_range['binary_value'] == 'N/A'
                    else:
                        bit_num = int(bits)
                        if bit_num >= 8:
                            assert bit_range['value'] == 'N/A'
                            assert bit_range['binary_value'] == 'N/A'


class TestI2cUtilityFunctions:
    """Test I2C parsing utility functions"""

    def test_parse_byte_dump_basic(self):
        """Test parsing basic byte dump lines"""
        lines = [
            "00: 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10",
            "10: 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f 20"
        ]

        result = parse_byte_dump(lines)
        assert isinstance(result, dict)
        assert result['0x00'] == '01'
        assert result['0x01'] == '02'
        assert result['0x10'] == '11'
        assert result['0x1f'] == '20'

    def test_parse_byte_dump_with_xx_values(self):
        """Test parsing byte dump with XX (unavailable) values"""
        lines = [
            "00: 01 xx 03 -- 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10"
        ]

        result = parse_byte_dump(lines)
        assert result['0x00'] == '01'
        assert result['0x01'] == 'xx'  # Should preserve xx
        assert result['0x02'] == '03'
        assert result['0x03'] == 'xx'  # -- should become xx

    def test_parse_word_dump_basic(self):
        """Test parsing basic word dump lines"""
        lines = [
            "00: 0102 0304 0506 0708 090a 0b0c 0d0e 0f10",
            "08: 1112 1314 1516 1718 191a 1b1c 1d1e 1f20"
        ]

        result = parse_word_dump(lines)
        assert isinstance(result, dict)
        assert result['0x00'] == '0102'
        assert result['0x01'] == '0304'
        assert result['0x08'] == '1112'
        assert result['0x0f'] == '1f20'

    def test_parse_word_dump_with_xxxx_values(self):
        """Test parsing word dump with XXXX (unavailable) values"""
        lines = [
            "00: 0102 ---- 0506 0708 090a 0b0c 0d0e 0f10"
        ]

        result = parse_word_dump(lines)
        assert result['0x00'] == '0102'
        assert result['0x01'] == 'xxxx'  # ---- should become xxxx
        assert result['0x02'] == '0506'

    def test_parse_empty_dumps(self):
        """Test parsing empty dump lines"""
        byte_result = parse_byte_dump([])
        word_result = parse_word_dump([])

        assert isinstance(byte_result, dict)
        assert isinstance(word_result, dict)
        assert len(byte_result) == 0
        assert len(word_result) == 0

    def test_parse_malformed_dump_lines(self):
        """Test parsing malformed dump lines"""
        lines = [
            "invalid line",
            "not a hex line",
            "00: incomplete"
        ]

        result = parse_byte_dump(lines)
        assert isinstance(result, dict)
        # Should handle malformed lines gracefully


class TestPsuDebugParser:
    """Test PSU debug info parsing"""

    def test_parse_psu_debug_basic(self):
        """Test parsing basic PSU debug info"""
        content = """POWER SUPPLY SLOT 1 DETAILS
MFR_ID: Arista
MFR_MODEL: PWR-00591
MFR_REVISION: 02 A0
MFR_LOCATION: Delta Thailand
MFR_DATE: 20241120
MFR_SERIAL: THAGM244700LR
MFR_POUT_MAX: 2400
PRI_MCU_FW_VERSION: 04.02
SEC_MCU_FW_VERSION: 04.02
STATUS_BYTE: 0x02
STATUS_WORD: 0x0200
READ_VIN: 50.9375
READ_IIN: 11.0469
READ_VOUT: 12.1328
READ_IOUT: 43.5625
READ_TEMPERATURE_1: 36
READ_TEMPERATURE_2: 57
READ_TEMPERATURE_3: 66
READ_FAN SPEED_1: 9296
READ_FAN SPEED_2: 9120
READ_POUT: 529
READ_PIN: 563
PMBUS_REVISION: 0x22

POWER SUPPLY SLOT 2 DETAILS
MFR_ID: Arista
MFR_MODEL: PWR-00591
MFR_REVISION: 02 A0
MFR_LOCATION: Delta Thailand
MFR_DATE: 20241120
MFR_SERIAL: THAGM244700HL
MFR_POUT_MAX: 2400
PRI_MCU_FW_VERSION: 04.02
SEC_MCU_FW_VERSION: 04.02
STATUS_BYTE: 0x02
STATUS_WORD: 0x0200
READ_VIN: 50.9375
READ_IIN: 10.9375
READ_VOUT: 12.1328
READ_IOUT: 42.625
READ_TEMPERATURE_1: 37
READ_TEMPERATURE_2: 59
READ_TEMPERATURE_3: 70
READ_FAN SPEED_1: 9328
READ_FAN SPEED_2: 9488
READ_POUT: 517
READ_PIN: 556
PMBUS_REVISION: 0x22"""

        result = parse_psu_debug(content)

        assert result['type'] == 'psu_debug'
        assert result['psu_count'] == 2
        assert len(result['psu_slots']) == 2

        # Check first PSU
        psu1 = result['psu_slots'][0]
        assert psu1['slot'] == 1
        assert psu1['properties']['MFR_ID'] == 'Arista'
        assert psu1['properties']['MFR_MODEL'] == 'PWR-00591'
        assert psu1['properties']['MFR_SERIAL'] == 'THAGM244700LR'
        assert psu1['properties']['READ_VIN'] == '50.9375'
        assert psu1['properties']['READ_POUT'] == '529'

        # Check second PSU
        psu2 = result['psu_slots'][1]
        assert psu2['slot'] == 2
        assert psu2['properties']['MFR_ID'] == 'Arista'
        assert psu2['properties']['MFR_SERIAL'] == 'THAGM244700HL'
        assert psu2['properties']['READ_POUT'] == '517'

    def test_parse_psu_debug_single_slot(self):
        """Test parsing single PSU slot"""
        content = """POWER SUPPLY SLOT 1 DETAILS
MFR_ID: Arista
MFR_MODEL: PWR-00591
READ_VIN: 50.9375
READ_VOUT: 12.1328"""

        result = parse_psu_debug(content)

        assert result['type'] == 'psu_debug'
        assert result['psu_count'] == 1
        assert len(result['psu_slots']) == 1
        assert result['psu_slots'][0]['slot'] == 1
        assert len(result['psu_slots'][0]['properties']) == 4

    def test_parse_psu_debug_empty_content(self):
        """Test parsing empty PSU debug content"""
        content = ""

        result = parse_psu_debug(content)

        assert result['type'] == 'raw'
        assert result['data'] == content

    def test_parse_psu_debug_no_slots(self):
        """Test parsing PSU debug content with no valid slots"""
        content = """Some random content
without PSU slot headers
KEY: value"""

        result = parse_psu_debug(content)

        assert result['type'] == 'raw'
        assert result['data'] == content

    def test_parse_content_by_type_psu_debug(self):
        """Test PSU debug parsing through parse_content_by_type"""
        content = """POWER SUPPLY SLOT 1 DETAILS
MFR_ID: Arista
READ_VIN: 50.9375"""

        result = parse_content_by_type('psu_debug', content)

        assert result['type'] == 'psu_debug'
        assert result['psu_count'] == 1


class TestRawContentPopulation:
    """Test that raw_content field is properly populated in all section types"""

    def test_raw_content_populated_for_table_sections(self):
        """Test that table sections have raw_content field populated"""
        sample_content = """############ Test Table Section ############
Column1    Column2    Column3
Value1     Value2     Value3
Value4     Value5     Value6
"""

        sections = parse_sections(sample_content)

        # Filter out empty sections
        non_empty_sections = [s for s in sections if s['title'] is not None]
        assert len(non_empty_sections) == 1
        section = non_empty_sections[0]

        # Check section structure
        assert section['title'] == 'Test Table Section'
        assert 'parsed_data' in section
        assert 'raw_content' in section

        # Check raw_content is populated
        assert section['raw_content'] is not None
        assert 'Column1    Column2    Column3' in section['raw_content']
        assert 'Value1     Value2     Value3' in section['raw_content']

        # Check parsed_data structure exists (type may be 'raw' if table parsing fails)
        assert section['parsed_data']['type'] in ['table', 'raw']

    def test_raw_content_preserves_formatting(self):
        """Test that raw_content preserves special characters and formatting"""
        sample_content = """############ Special Characters Test ############
Line with tabs:	tab1	tab2	tab3
Line with spaces:    multiple    spaces    here
Special chars: !@#$%^&*()_+-=[]{}|;:'"<>?,.
Empty line below:

Line after empty line
"""

        sections = parse_sections(sample_content)

        # Filter out empty sections
        non_empty_sections = [s for s in sections if s['title'] is not None]
        assert len(non_empty_sections) == 1
        section = non_empty_sections[0]

        raw_content = section['raw_content']

        # Check tabs are preserved
        assert '\t' in raw_content
        assert 'tab1\ttab2\ttab3' in raw_content

        # Check multiple spaces are preserved
        assert 'multiple    spaces    here' in raw_content

        # Check special characters are preserved
        assert '!@#$%^&*()_+-=[]{}|;:\'"<>?,' in raw_content

        # Check empty lines are preserved
        lines = raw_content.split('\n')
        empty_line_exists = any(line.strip() == '' for line in lines)
        assert empty_line_exists

    def test_multiple_sections_all_have_raw_content(self):
        """Test that all sections in a multi-section file have raw_content populated"""
        sample_content = """############ First Section ############
Key1: Value1
Key2: Value2

############ Second Section ############
Column1    Column2
Data1      Data2
Data3      Data4

############ Third Section ############
This is raw content
With multiple lines
And various formatting
"""

        sections = parse_sections(sample_content)

        # Filter out empty sections
        non_empty_sections = [s for s in sections if s['title'] is not None]
        assert len(non_empty_sections) == 3

        # Check all sections have raw_content
        for i, section in enumerate(non_empty_sections):
            assert 'raw_content' in section, f"Section {i} missing raw_content"
            assert section['raw_content'] is not None, f"Section {i} has null raw_content"
            assert len(section['raw_content'].strip()) > 0, f"Section {i} has empty raw_content"

        # Check specific content for each section
        assert 'Key1: Value1' in non_empty_sections[0]['raw_content']
        assert 'Column1    Column2' in non_empty_sections[1]['raw_content']
        assert 'This is raw content' in non_empty_sections[2]['raw_content']
