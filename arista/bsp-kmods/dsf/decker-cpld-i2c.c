/* Copyright (c) 2023 Arista Networks, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <linux/errno.h>
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/version.h>

#include "regbit-sysfs.h"

#define CPLD_REG_REV_MINOR	0x0
#define CPLD_REG_REV_MAJOR	0x1
#define CPLD_REG_CTRL_STS	0x5
#define CPLD_REG_SYS_STS	0x8
#define CPLD_REG_SCD_FPGA_STA	0xA
#define CPLD_REG_JTAG_SEL	0xC
#define CPLD_REG_IDPROM_WP	0x22
#define CPLD_SCD0_CTRL_STA	0xA0
#define CPLD_SCD1_CTRL_STA	0xA1
#define CPLD_SCD2_CTRL_STA	0xA2
#define CPLD_SCD3_CTRL_STA	0xA3

static const struct regbit_sysfs_config cpld_sys_attrs[] = {
	/*
	 * CPLD version/sub_version @ address/offset 0x0 and 0x1.
	 */
	{
		.name = "cpld_sub_ver",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_REV_MINOR,
		.bit_offset = 0,
		.num_bits = 8,
	},
	{
		.name = "cpld_ver",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_REV_MAJOR,
		.bit_offset = 0,
		.num_bits = 8,
	},

	/*
	 * Power Ctrl/Stat register @ address/offset 0x5.
	 */
	{
		.name = "switch_card_pwr_status",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_CTRL_STS,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: switch card power bad\n"
			    "1: switch card power good",
	},

	/* MERU TODO: add ASIC/port status registers. */

	/*
	 * SCD_FPGA_STA @ address/offset 0xA.
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

	/*
	 * JTAG @ address/offset 0xC.
	 */
	{
		.name = "jtag_mux_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 0,
		.num_bits = 4,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: No connection (default)\n"
			    "1: JTAG connected to Blackcomb SCD 0\n"
			    "2: JTAG connected to Blackcomb SCD 1\n"
			    "3: JTAG connected to Blackcomb SCD 2\n"
			    "4: JTAG connected to Blackcomb SCD 3\n"
			    "5: JTAG connected to Oasis CPLD 0\n"
			    "6: JTAG connected to Oasis CPLD 1\n"
			    "7: JTAG connected to Oasis CPLD 2\n"
			    "8: JTAG connected to Ramon ASIC 0\n"
			    "9: JTAG connected to Ramon ASIC 1",
	},
	{
		.name = "cpld_jtag_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 7,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: CPU -> external JTAG selected\n"
			    "1: CPU -> CPLD JTAG selected, bits[6:0] are ignored",
	},

	/*
	 * IDPROM Write-Protect @ address/offset 0x22.
	 */
	{
		.name = "idprom_wp",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_IDPROM_WP,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: IDPROM write-protect disabled\n"
			    "1: IDPROM write-protect enabled (default)",
	},

	/*
	 * SCD0_CTRL_STA @ address/offset 0xA0.
	 */
	{
		.name = "scd0_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_SCD0_CTRL_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD0 configuration not done yet\n"
			    "1: SCD0 configuration done",
	},
	{
		.name = "scd0_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_SCD0_CTRL_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: initiate SCD0 re-configuration",
	},

	/*
	 * SCD1_CTRL_STA @ address/offset 0xA1.
	 */
	{
		.name = "scd1_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_SCD1_CTRL_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD1 configuration not done yet\n"
			    "1: SCD1 configuration done",
	},
	{
		.name = "scd1_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_SCD1_CTRL_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: initiate SCD1 re-configuration",
	},

	/*
	 * SCD2_CTRL_STA @ address/offset 0xA2.
	 */
	{
		.name = "scd2_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_SCD2_CTRL_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD2 configuration not done yet\n"
			    "1: SCD2 configuration done",
	},
	{
		.name = "scd2_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_SCD2_CTRL_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: initiate SCD2 re-configuration",
	},

	/*
	 * SCD3_CTRL_STA @ address/offset 0xA3.
	 */
	{
		.name = "scd3_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_SCD3_CTRL_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD3 configuration not done yet\n"
			    "1: SCD3 configuration done",
	},
	{
		.name = "scd3_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_SCD3_CTRL_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
			    "1: initiate SCD3 re-configuration",
	},
};

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 3, 0)
static int cpld_i2c_probe(struct i2c_client *client)
#else
static int cpld_i2c_probe(struct i2c_client *client,
			  const struct i2c_device_id *id)
#endif
{
	int ret;
	u8 major_rev, minor_rev;

	ret = i2c_smbus_read_byte_data(client, CPLD_REG_REV_MINOR);
	if (ret < 0)
		return ret;
	minor_rev = (u8)ret;

	ret = i2c_smbus_read_byte_data(client, CPLD_REG_REV_MAJOR);
	if (ret < 0)
		return ret;
	major_rev = (u8)ret;
	dev_info(&client->dev, "decker cpld revision: %02x.%02x\n",
		 major_rev, minor_rev);

	return regbit_sysfs_init_i2c(&client->dev, cpld_sys_attrs,
				     ARRAY_SIZE(cpld_sys_attrs));
}

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "decker_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

static struct i2c_driver cpld_i2c_driver = {
	.driver = {
		.name = "decker-cpld",
	},
	.probe = cpld_i2c_probe,
	.id_table = cpld_dev_ids,
};
module_i2c_driver(cpld_i2c_driver);

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Decker CPLD I2C Driver");
MODULE_LICENSE("GPL");
