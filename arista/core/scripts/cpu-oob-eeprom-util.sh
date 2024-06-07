#!/bin/bash
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# This script has been adapted from the OpenBmc script oob-eeprom-util.sh
# script to be able to run on the CPU. This has only been tested on
# Fairywren and may need changes to run elsewhere.

# shellcheck disable=SC2059

EWEN_CMD=0x0
EWEN_ADDR=0x300
EWDS_CMD=0x0
EWDS_ADDR=0x0
READ_CMD=0x2
WRITE_CMD=0x1

SPEED_1MHZ=0x1

SCM_CPLD="/run/devmap/fpgas/MERU_SCM_CPLD"
COMMAND_REG="${SCM_CPLD}/oob_eeprom_cmd"
RESPONSE_REG="${SCM_CPLD}/oob_eeprom_resp"
OPMODE_REG="${SCM_CPLD}/opmode_override"

EEPROM_SIZE=1024

WRITES_ENABLED=0

trap cleanup EXIT
trap handle_signal INT TERM QUIT

usage() {
    echo "Dumps or programs the OOB Eeprom"
    echo
    echo "dump [--full]"
    echo "save <filename>"
    echo "program <filename>"
    echo "read <index> [<num-words>]"
    echo "write <index> <word>"
    echo "version"
}

read_index() {
    local cmd_reg
    cmd_reg=$(( ( READ_CMD << 30 ) | ( SPEED_1MHZ << 28 ) | ( $1 << 16 ) ))
    desc="reading index $idx"
    send_cmd "$cmd_reg" "$desc"
}

write_index() {
    local idx=$1
    local val=$2
    local cmd_reg
    cmd_reg=$(( ( WRITE_CMD << 30 ) | ( SPEED_1MHZ << 28 ) \
              | ( idx << 16 ) | val ))
    desc="writing index $idx value $val"
    local resp_val
    local try_num=0
    while [ $try_num -lt 5 ]
    do
        resp_val=$( send_cmd "$cmd_reg" "$desc" ) || exit 1
        if [ $(( resp_val )) -eq $(( val )) ]
        then
            # verify the value read matches the value programmed
            read_val=$( read_index "$idx" )
            if [ $(( read_val )) = $(( val )) ]
            then
                return
            fi

            printf "Error: try %d: read value after write(" $try_num >&2
            printf "0x%x) does not match write val(0x%x)\n" "$read_val" "$val" >&2
        else
            printf "Error: try %d: response value from write(" $try_num >&2
            printf "0x%x) does not match write val(0x%x)\n" "$resp_val" "$val" >&2
        fi

        try_num=$(( try_num + 1 ))
    done

    echo "failed to write register" >&2
    exit 1
}

enable_eeprom_access() {
    # Drive opmode_0 and opmode_2 low to enable the CPLD to talk to the EEPROM.
    # This overrides the DS4520 setting for this opmode.
    # Bits 7:5 control opmodes 2:0. This works for both BMC and CPU mode.
    echo 2 > "${OPMODE_REG}"
}

disable_eeprom_access() {
    # Clear all opmode overrides by setting bits 7:5.
    echo 7 > "${OPMODE_REG}"
}

eeprom_disable_write() {
    echo "Write interrupted. Disabling writes." >&2
    eeprom_write_protect "disable"
}

cleanup() {
    if [ $WRITES_ENABLED -eq 1 ]
    then
        eeprom_disable_write
        WRITES_ENABLED=0
    fi
    disable_eeprom_access
}

handle_signal() {
    echo "Exiting because of signal" >&2
    cleanup
    exit 1
}

eeprom_write_protect() {
    local enable=$1

    local cmd cmd_addr
    if [ "$enable" = "enable" ]
    then
        cmd=$EWEN_CMD
        cmd_addr=$EWEN_ADDR
        WRITES_ENABLED=1
    else
        cmd=$EWDS_CMD
        cmd_addr=$EWDS_ADDR
    fi

    local cmd_reg
    cmd_reg=$(( ( cmd << 30 ) | ( SPEED_1MHZ << 28 ) \
           | ( cmd_addr << 16 ) ))
    desc="setting write protect to $enable"
    send_cmd "$cmd_reg" "$desc" > /dev/null

    if [ "$enable" = "disable" ]
    then
        WRITES_ENABLED=0
    fi
}

eeprom_init() {
    enable_eeprom_access

    # Clear write cycle error, if present
    echo $(( 1 << 27 )) > "${RESPONSE_REG}"
}

send_cmd() {
    local cmd_reg=$1
    local desc="$2"

    local try_num=0
    while [ $try_num -lt 5 ]
    do
        echo "${cmd_reg}" > "${COMMAND_REG}"

        get_response "$desc" && return
        if [ $? -gt 1 ]
        then
           exit 1
        fi

        printf "Send command failed on try %d\n" $try_num >&2
        try_num=$(( try_num + 1 ))
    done

    echo "Send command failed" >&2
    exit 1
}

get_response() {
    local desc=$1
    local timeout=5
    local interval=0.1
    local time_limit=0
    local resp_val
    while true
    do
        raw=$(cat "${RESPONSE_REG}")
        resp_val=$(( raw ))

        if [ $(( ( resp_val >> 27 ) & 0x1 )) -ne 0 ]
        then
            echo "Error: Write cycle error" >&2
            return 2
        fi

        if [ $(( ( resp_val >> 28 ) & 0x1 )) -ne 0 ]
        then
            echo $(( resp_val & 0xffff ))
            return 0
        fi

        if [ $time_limit -eq 0 ]
        then
            time_limit=$(( $( date +%s ) + timeout ))
        fi
        if [ "$( date +%s )" -gt $time_limit ]
        then
            break
        fi

        sleep $interval
    done

    echo "Timed out $desc" >&2
    return 1
}

eeprom_read() {
    if [ $# -lt 1 ]
    then
        echo "Error: missing read index" >&2
        usage
        exit 1
    fi

    local start=$(( $1 ))
    local num_words=1
    if [ $# -gt 1 ]
    then
        num_words=$2
    fi
    local end=$(( start + num_words ))
    if [ $end -gt $EEPROM_SIZE ]
    then
        echo "Error: end index exceeds size" >&2
        exit 1
    fi

    eeprom_write_protect "disable"

    local idx=$start
    local val
    while [ $idx -lt "$end" ]
    do
        val=$( read_index $idx )
        printf "0x%x: 0x%x\n" $idx "$val"
        idx=$(( idx + 1 ))
    done
}

add_to_csum() {
    local csum=$1
    local idx=$2
    local val=$3
    csum=$(( csum + ( idx << 16 ) + val ))
    # To prevent overflowing 32 bits, modulus with bit 31.
    csum=$(( csum % 0x80000000 ))
    echo $csum
}

eeprom_dump() {
    local csum_lsb csum_msb header version

    local full="no"
    if [ $# -gt 0 ] && [ "$1" = "--full" ]
    then
        full="yes"
    fi

    eeprom_write_protect "disable"
    local calc_csum=0

    header=$( read_index 0 )
    printf "0x%x: 0x%x\n" 0 "$header"
    # As described in Broadcom's BCM53134P data sheet, the magic code
    # is in bits 15:11 of the first word in the EEPROM and the expected
    # value is 0x15.
    local magic_code=$(( header >> 11 ))
    if [ $magic_code -ne $(( 0x15 )) ]
    then
        printf "Error: magic code 0x%x does not match expected " $magic_code >&2
        printf "0x15\n" >&2
        if [ $full = "no" ]
        then
            exit 1
        fi
    fi
    calc_csum=$( add_to_csum $calc_csum 0 "$header" )

    local num_entries=$(( header & 0x3ff ))
    local stream_end=$(( 1 + num_entries ))
    echo "Number of data words: $num_entries"
    local start=1
    # 3 words are reserved at the end of the image.
    # 2 are for the checksum. 1 is for the version.
    local eeprom_end=$(( EEPROM_SIZE - 3 ))
    local end=$eeprom_end
    if [ $full = "no" ]
    then
        end=$stream_end
    fi

    local idx=$start
    while [ $idx -lt "$end" ]
    do
        val=$( read_index $idx )
        printf "0x%x: 0x%x\n" $idx "$val"
        if [ $idx -lt $stream_end ]
        then
            calc_csum=$( add_to_csum "$calc_csum" $idx "$val" )
        fi
        idx=$(( idx + 1 ))
    done

    idx=$eeprom_end
    csum_lsb=$( read_index idx )
    printf "0x%x: 0x%x\n" $idx "$csum_lsb"
    idx=$(( idx + 1 ))
    csum_msb=$( read_index idx )
    printf "0x%x: 0x%x\n" $idx "$csum_msb"
    idx=$(( idx + 1 ))
    version=$( read_index idx )
    printf "0x%x: 0x%x\n" $idx "$version"
    printf "Version: %x.%x\n" $(( version >> 8 )) $(( version & 0xff ))

    csum=$(( ( csum_msb << 16 ) | csum_lsb ))
    printf "Checksum: 0x%x\n" $csum
    printf "Calculated checksum: 0x%x\n" "$calc_csum"

    if [ "$csum" -ne "$calc_csum" ]
    then
        echo "Error: Checksum is not expected value" >&2
        exit 1
    fi
}

eeprom_version() {
    local idx version

    eeprom_write_protect "disable"

    # Last word at the end of the image contains version.
    idx=$(( EEPROM_SIZE - 1 ))
    version=$( read_index idx )
    printf "Version: %x.%x\n" $(( version >> 8 )) $(( version & 0xff ))
}

eeprom_save() {
    if [ $# -lt 1 ]
    then
        echo "Error: missing filename" >&2
        usage
        exit 1
    fi

    local filename=$1
    if [ -f "$filename" ]
    then
        echo "Error: file $filename already exists. Remove this file." >&2
        exit 1
    fi

    touch "$filename"
    local idx=0
    local val
    while [ $idx -lt "$EEPROM_SIZE" ]
    do
        val=$( read_index $idx )
        printf "\\$( printf "%o" $(( val & 0xff )) )" >> "$filename"
        printf "\\$( printf "%o" $(( val >> 8 )) )" >> "$filename"
        if [ $(( ( idx + 1 ) % 0x80 )) -eq 0 ]
        then
            printf "Saved word 0x%x\n" "$idx"
        fi
        idx=$(( idx + 1 ))
    done
    sync
}

eeprom_write() {
    if [ $# -lt 2 ]
    then
        echo "Error: missing arguments" >&2
        usage
        exit 1
    fi

    eeprom_write_protect "enable"

    local idx=$1
    local val=$2

    write_index "$idx" "$val"
    printf "Wrote 0x%x to 0x%x\n" "$val" "$idx"

    eeprom_write_protect "disable"
}

program_file() {
    local i=0
    local idx=0
    local val=0

    while read -r c
    do
        if [ $i -eq 0 ]
        then
            val=$c
            i=1
        else
            val=$(( val | ( c << 8 ) ))
            write_index "$idx" "$val"
            printf "Wrote 0x%x to 0x%x\n" "$val" "$idx"

            idx=$(( idx + 1 ))
            i=0
        fi
    done
}

eeprom_program() {
    if [ $# -lt 1 ]
    then
        echo "Error: missing filename" >&2
        usage
        exit 1
    fi

    local filename=$1

    if [ ! -f "$filename" ]
    then
        echo "Error: could not access file $filename" >&2
        exit 1
    fi

    size=$( stat -c %s "$filename" )
    words=$(( size / 2 ))
    if [ "$words" -ne $EEPROM_SIZE ]
    then
        printf "Error: words in file(%d) does not match eeprom " "$words" >&2
        printf "size(%d)\n" $EEPROM_SIZE >&2
        exit 1
    fi

    eeprom_write_protect "enable"
    hexdump -v -e '/1 "%u\n"' "$filename" | program_file
    eeprom_write_protect "disable"
}

if [ $# -lt 1 ]
then
    echo "Error: missing command" >&2
    usage
    exit 1
fi

# Only allow one instance of script to run at a time.
script=$(realpath "$0")
exec 100< "$script"
flock -n 100 || { echo "ERROR: $0 already running" && exit 1; }

command="$1"
shift

eeprom_init

case "$command" in
    dump)
        eeprom_dump "$@"
        ;;
    save)
        eeprom_save "$@"
        ;;
    program)
        eeprom_program "$@"
        ;;
    read)
        eeprom_read "$@"
        ;;
    write)
        eeprom_write "$@"
        ;;
    version)
        eeprom_version "$@"
        ;;
    *)
        echo "Error: invalid command: $command" >&2
        usage
        exit 1
        ;;
esac
