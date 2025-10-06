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

#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/version.h>

#include "fan-cpld-i2c.h"

#define DRIVER_NAME "glath05a-64o-fan-cpld"

enum cpld_type {
	PALI2_CPLD = 0,
};

static const struct fan_cpld_info cpld_infos[] = {
	[PALI2_CPLD] = {
		.label = "quicksilver",
		.fan_count = 4,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 0,
		.default_pwm = 179, // 70% duty cycle
		.max_pwm = 255,
	},
};

static const struct i2c_device_id cpld_ids[] = {
		{ "glath05a64o_fancpld", PALI2_CPLD },
						{} };
MODULE_DEVICE_TABLE(i2c, cpld_ids);

FAN_CPLD_DRIVER(DRIVER_NAME, glath05a64o_fancpld, cpld_infos, cpld_ids)

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("quicksilver Fan Cpld Driver");
MODULE_VERSION(BSP_VERSION);
