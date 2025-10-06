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

#define DRIVER_NAME "dsf-fan-cpld"

enum cpld_type {
	OASIS_CPLD0 = 0,
	OASIS_CPLD1 = 1,
	OASIS_CPLD2 = 2,
	PALI2_CPLD = 3,
};

static const struct fan_cpld_info cpld_infos[] = {
	[OASIS_CPLD0] = {
		.label = "DSF",
		.fan_count = 4,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 0,
		.default_pwm = 77, // 30% duty cycle
		.max_pwm = 255,
	},
	[OASIS_CPLD1] = {
		.label = "DSF",
		.fan_count = 4,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 4,
		.default_pwm = 77, // 30% duty cycle
		.max_pwm = 255,
	},
	[OASIS_CPLD2] = {
		.label = "DSF",
		.fan_count = 4,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 8,
		.default_pwm = 77, // 30% duty cycle
		.max_pwm = 255,
	},
	[PALI2_CPLD] = {
		.label = "DSF",
		.fan_count = 4,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 0,
		.default_pwm = 77, // 30% duty cycle
		.max_pwm = 255,
	},
};

static const struct i2c_device_id cpld_ids[] = {
						{ "fan_cpld0", OASIS_CPLD0 },
						{ "fan_cpld1", OASIS_CPLD1 },
						{ "fan_cpld2", OASIS_CPLD2 },
						{ "fan_cpld", PALI2_CPLD },
						{} };
MODULE_DEVICE_TABLE(i2c, cpld_ids);

FAN_CPLD_DRIVER(DRIVER_NAME, dsf_fan_cpld, cpld_infos, cpld_ids)

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("DSF Fan Cpld Driver");
MODULE_VERSION(BSP_VERSION);
