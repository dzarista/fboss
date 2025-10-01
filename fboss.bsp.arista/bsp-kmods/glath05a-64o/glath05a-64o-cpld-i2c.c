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

static const struct regbit_sysfs_config glath05a_64o_cpld_attrs[] = {
	/*
	 * JTAG selectors @ address/offset 0xC.
	 */
	{
		.name = "jtag_mux_sel",
		.mode = REGBIT_FMODE_RW,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 0,
		.num_bits = 4,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: No connection (default)\n"
			    "1: SCD\n"
			    "2: FAN",
	},
	{
		.name = "cpld_jtag_sel",
		.mode = REGBIT_FMODE_RO,
		.reg_addr = CPLD_REG_JTAG_SEL,
		.bit_offset = 7,
		.num_bits = 1,
		.flags = RBS_FLAG_SHOW_NOTES,
		.help_str = "0: CPU -> external JTAG selected\n"
			    "1: CPU -> CPLD JTAG selected, bits[6:0] are ignored",
	},
};

SMB_CPLD_PROBE_FN("glath05a_64o", glath05a_64o_cpld_attrs);

static const struct i2c_device_id glath05a_64o_cpld_dev_ids[] = {
	{ "glath05a-64o_cpld", 0 },
	{},
};
MODULE_DEVICE_TABLE(i2c, glath05a_64o_cpld_dev_ids);

static struct i2c_driver glath05a_64o_cpld_i2c_driver = {
	.driver = {
		.name = "glath05a-64o-cpld",
	},
	.probe = smb_cpld_i2c_probe,
	.remove = smb_cpld_i2c_remove,
	.id_table = glath05a_64o_cpld_dev_ids,
};
module_i2c_driver(glath05a_64o_cpld_i2c_driver);

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Glath05a-64o CPLD I2C Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
