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

#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/version.h>

#include "fan-cpld-i2c.h"

#define DRIVER_NAME "glath06a-64o-fan-cpld"

enum cpld_type {
	FAN_CPLD = 0,
};

static const struct fan_cpld_reg_info reg_info = {
	.id_reg_base = 0x91,
	.present_reg = 0xa0,
	.ok_reg = 0xa1,
	.blue_led_reg = 0xa3,
	.amber_led_reg = 0xa4,
	.int_reg = 0xa7,
	.id_change_reg = 0xb0,
	.present_change_reg = 0xb1,
	.ok_change_reg = 0xb2,
	.change_reg_clear_val = 0xff,
};

static const struct fan_cpld_info cpld_infos[] = {
	[FAN_CPLD] = {
		.label = "Glath06a-64o",
		.regs = &reg_info,
		.fan_count = 8,
		.rotors = 2,
		.pulses = 2,
		.hz = 100000,
		.fan_global_offset = 0,
		.default_pwm = 179, // 70% duty cycle
		.max_pwm = 255,
	},
};

static const struct i2c_device_id cpld_ids[] = {
		{ "glath06a64o_fancpld", FAN_CPLD },
						{} };
MODULE_DEVICE_TABLE(i2c, cpld_ids);

FAN_CPLD_DRIVER(DRIVER_NAME, glath6a64o_fancpld, cpld_infos, cpld_ids)

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Glath06a-64o Fan Cpld Driver");
MODULE_VERSION(BSP_VERSION);
