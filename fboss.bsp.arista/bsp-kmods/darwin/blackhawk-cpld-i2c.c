// SPDX-License-Identifier: GPL-2.0-or-later
// // Copyright (c) 2021 Facebook Inc.

#include <linux/errno.h>
#include <linux/module.h>
#include <linux/i2c.h>

#include "regbit-sysfs.h"
#include "smb-cpld-i2c.h"

#define CPLD_REG_SYS_STS	0x8

static const struct regbit_sysfs_config blackhawk_attrs[] = {
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

static int cpld_i2c_probe(struct i2c_client *client)
{
	int ret;

	ret = smb_cpld_fw_ver_read(client, NULL, "blackhawk");
	if (ret < 0)
		return ret;

	ret = smb_cpld_create_fw_ver_attr(client);
	if (ret < 0)
		return ret;

	return smb_cpld_init_with_attrs(&client->dev, blackhawk_attrs,
				ARRAY_SIZE(blackhawk_attrs));
}

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "blackhawk_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

static struct i2c_driver blackhawk_cpld_driver = {
	.driver = {
		.name = "blackhawk-cpld",
	},
	.probe = cpld_i2c_probe,
	.id_table = cpld_dev_ids,
};
module_i2c_driver(blackhawk_cpld_driver);

MODULE_AUTHOR("Facebook, Inc.");
MODULE_DESCRIPTION("Blackhawk CPLD I2C Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
