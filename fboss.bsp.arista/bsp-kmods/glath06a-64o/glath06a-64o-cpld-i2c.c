/* Copyright (c) 2025 Arista Networks, Inc.
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

#define DRIVER_NAME "glath06a-64o-cpld"

#define CPLD_REG_SCD0_FPGA_STA	0xA
#define CPLD_REG_SCD1_FPGA_STA	0xB

static const struct regbit_sysfs_config cpld_attrs[] = {
	/*
	 * SCD_FPGA0_STA @ address/offset 0xA.
	 */
	{
		.name = "scd0_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SCD0_FPGA_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD FPGA configuration not done yet\n"
					"1: SCD FPGA configuration done",
	},
	{
		.name = "scd0_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD0_FPGA_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
					"1: initiate SCD FPGA re-configuration",
	},
	{
		.name = "scd0_hold",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD0_FPGA_STA,
		.bit_offset = 4,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
					"1: hold SCD output",
	},
	{
		.name = "scd0_reset",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD0_FPGA_STA,
		.bit_offset = 5,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
					"1: reset SCD",
	},

	/*
	 * SCD_FPGA1_STA @ address/offset 0xB.
	 */
	{
		.name = "scd1_config_done",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_SCD1_FPGA_STA,
		.bit_offset = 0,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: SCD FPGA configuration not done yet\n"
					"1: SCD FPGA configuration done",
	},
	{
		.name = "scd1_config",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD1_FPGA_STA,
		.bit_offset = 3,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
					"1: initiate SCD FPGA re-configuration",
	},
	{
		.name = "scd1_hold",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD1_FPGA_STA,
		.bit_offset = 4,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: normal operation. Default\n"
					"1: hold SCD output",
	},
	{
		.name = "scd1_reset",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_SCD1_FPGA_STA,
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
		.num_bits = 3,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: No connection (default)\n"
					"1: SCD0\n"
					"2: SCD1\n"
					"3: TH6C Core and PhyTiles\n"
					"4: TH6C Core only\n"
					"5: TH6C PhyTiles only",
	},
};

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "glath06a-64o_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

SMB_CPLD_DRIVER(DRIVER_NAME, glath06a_64o, cpld_attrs, cpld_dev_ids)

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Glath06a-64o CPLD I2C Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
