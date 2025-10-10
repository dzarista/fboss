// SPDX-License-Identifier: GPL-2.0-or-later
// // Copyright (c) 2021 Facebook Inc.

#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/version.h>

#include "regbit-sysfs.h"
#include "smb-cpld-i2c.h"

#define DRIVER_NAME "blackhawk-cpld"

#define CPLD_REG_SYS_STS    0x8

static const struct regbit_sysfs_config cpld_attrs[] = {
	/*
	 * SYSTEM_STATUS @ address/offset 0x8.
	 */
	{
		.name = "scd_crc_error",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SYS_STS,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: No CRC error detected\n"
			    "1: SCD CRC error detected",
	},
	{
		.name = "watchdog_error",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SYS_STS,
		.bit_offset = 1,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: Watchdog OK\n"
			    "1: Watchdog timeout detected",
	},
	{
		.name = "cpu_switch_bus_parity_error",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SYS_STS,
		.bit_offset = 2,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: No parity error\n"
			    "1: Parity error detected",
	},
	{
		.name = "overtemp",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SYS_STS,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: Temperature OK\n"
			    "1: Over temperature detected",
	},

	/*
	 * SCD config bit in SCD_FPGA_STA @ address/offset 0xA.
	 */
	{
		.name = "scd_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SCD_FPGA_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD FPGA configuration not done yet\n"
			    "1: SCD FPGA configuration done",
	},
	{
		.name = "scd_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD_FPGA_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: initiate SCD FPGA re-configuration",
	},
	{
		.name = "scd_hold",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD_FPGA_STA,
		.bit_offset = 4,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: hold SCD output for SCD hitless update",
	},
	{
		.name = "scd_reset",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD_FPGA_STA,
		.bit_offset = 5,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: reset SCD",
	},
	{
		.name = "scd_fpga_init_l",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SCD_FPGA_STA,
		.bit_offset = 6,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD configuration error\n"
			    "1: SCD configuration in progress or completed",
	},

	/*
	 * JTAG selects @ address/offset 0xC.
	 */
	{
		.name = "scd_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: de-select SCD FPGA as JTAG target\n"
			    "1: select SCD FPGA as JTAG target",
	},
	{
		.name = "sr0_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 1,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: de-select shift register 0 as JTAG target\n"
			    "1: select shift register 0 as JTAG target",
	},
	{
		.name = "sr1_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 2,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: de-select shift register 1 as JTAG target\n"
			    "1: select shift register 1 as JTAG target",
	},
	{
		.name = "th3_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: de-select Tomahawk 3 as JTAG target\n"
			    "1: select Tomahawk 3 as JTAG target",
	},
	{
		.name = "cpld_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 7,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: de-select CPLD as JTAG target\n"
			    "1: select CPLD as JTAG target",
	},
};

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "blackhawk_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

SMB_CPLD_DRIVER(DRIVER_NAME, blackhawk, cpld_attrs, cpld_dev_ids)

MODULE_AUTHOR("Facebook, Inc.");
MODULE_DESCRIPTION("Blackhawk CPLD I2C Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
