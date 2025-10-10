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

#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/version.h>

#include "regbit-sysfs.h"
#include "smb-cpld-i2c.h"

#define DRIVER_NAME "decker-cpld"

#define CPLD_SCD0_CTRL_STA	0xA0
#define CPLD_SCD1_CTRL_STA	0xA1
#define CPLD_SCD2_CTRL_STA	0xA2
#define CPLD_SCD3_CTRL_STA	0xA3

static const struct regbit_sysfs_config cpld_attrs[] = {
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
	 * JTAG selects @ address/offset 0xC.
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

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "decker_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

SMB_CPLD_DRIVER(DRIVER_NAME, decker, cpld_attrs, cpld_dev_ids)

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Decker CPLD I2C Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
