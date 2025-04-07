/* Copyright (c) 2024 Arista Networks, Inc.
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
#include <linux/jiffies.h>
#include <linux/rtc.h>
#include <linux/workqueue.h>
#include "scratchpad-bits.h"
#include "scd-reload-cause.h"

#define VCPLD_REG_MINOR_REV			(0x0)
#define VCPLD_REG_MAJOR_REV			(0x1)
#define VCPLD_REG_SCRATCHPAD			(0x2)
#define VCPLD_REG_LATCHED_FAULT_CAUSE		(0x60)
#define VCPLD_REG_LATCHED_FAULT_CAUSE_MASK	((1U << 6) - 1)
#define VCPLD_REG_FAULT_TEST_CONTROL		(0x58)
#define VCPLD_REG_FAULT_TEST_CONTROL_CLEAR_BITS	(0x1)
#define VCPLD_REG_RTC_FRACTIONAL_SEC_START	(0x40)
#define VCPLD_RTC_FRACTIONAL_SEC_REG_CNT	(2U)
#define VCPLD_REG_RTC_SEC_START			(0x42)
#define VCPLD_REG_TIMESTAMP_SEC_START		(0x63)
#define VCPLD_RTC_SEC_REG_CNT			(4U)

#define RTC_UPDATE_INTERVAL			(10U)
#define MILLENIUM_UNIX_TIMESTAMP		(946684800U)

struct encoded_reload_cause scd_vcpld_reload_causes[] = {
	DEFINE_RELOAD_CAUSE(1, "Overtemp Fault"),
	DEFINE_RELOAD_CAUSE(2, "SCD CRC"),
	DEFINE_RELOAD_CAUSE(3, "Watchdog Fault"),
	DEFINE_RELOAD_CAUSE(4, "CPU Fault"),
	DEFINE_RELOAD_CAUSE(8, "Software Requested Powercycle"),
	DEFINE_RELOAD_CAUSE(9, "PSU AC Loss"),
	DEFINE_RELOAD_CAUSE(10, "PSU DC Fault"),
	DEFINE_RELOAD_CAUSE(15, "Bitshadow Error"),
	DEFINE_RELOAD_CAUSE(17, "SUP_SEATED loss"),
	DEFINE_RELOAD_CAUSE(18, "Push button power cycle"),
	DEFINE_RELOAD_CAUSE(32, "P5V0_PGOOD"),
	DEFINE_RELOAD_CAUSE(33, "P1V8_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(34, "P0V85C_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(35, "P2V5_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(36, "P1V2_HBM_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(37, "P0V75A_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(38, "P0V9A_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(39, "P1V5_JE0_PGOOD"),
	DEFINE_RELOAD_CAUSE(40, "P3V3_OPTICS_PGOOD")
};

#define MERU_VCPLD_FAULT_COUNT			ARRAY_SIZE(scd_vcpld_reload_causes)

struct i2c_client *vcpld_i2c_client;

static void workqueue_func(struct work_struct *work);
DECLARE_DELAYED_WORK(vcpld_delayed_work, workqueue_func);
static void workqueue_func(struct work_struct *work)
{
	time64_t cur_time;
	u8 rtc_byte;
	int op_status;

	cur_time = ktime_get_real_seconds();
	cur_time -= MILLENIUM_UNIX_TIMESTAMP;
	schedule_delayed_work(&vcpld_delayed_work, RTC_UPDATE_INTERVAL*HZ);

	for (u8 byte = 0; byte < VCPLD_RTC_FRACTIONAL_SEC_REG_CNT; byte++) {
		op_status = i2c_smbus_write_byte_data(
			vcpld_i2c_client,
			VCPLD_REG_RTC_FRACTIONAL_SEC_START + byte,
			0);
		if (op_status < 0) {
			dev_info(&vcpld_i2c_client->dev, "failed to write RTC\n");
			break;
		}
	}
	for (u8 byte = 0; byte < VCPLD_RTC_SEC_REG_CNT; byte++) {
		rtc_byte = (cur_time >> (8 * byte)) & 0xFF;
		op_status = i2c_smbus_write_byte_data(
			vcpld_i2c_client,
			VCPLD_REG_RTC_SEC_START + byte,
			rtc_byte);
		if (op_status < 0) {
			dev_info(&vcpld_i2c_client->dev, "failed to write RTC\n");
			break;
		}
	}
}

static int process_reload_cause(struct i2c_client *client)
{
	int op_status;
	int ret_val = 0;
	u8 fault_cause;
	size_t fault_loop;
	u32 fault_timestamp = 0;
	time64_t rtc_counter_val;
	struct rtc_time rtc_time_val;
	u8 byte;

	op_status = i2c_smbus_read_byte_data(client, VCPLD_REG_LATCHED_FAULT_CAUSE);
	if (op_status < 0) {
		dev_info(&client->dev, "failed to read fault cause register\n");
		return op_status;
	}
	fault_cause = (u8)op_status;
	fault_cause &= VCPLD_REG_LATCHED_FAULT_CAUSE_MASK;
	for (fault_loop = 0; fault_loop < MERU_VCPLD_FAULT_COUNT; fault_loop++) {
		if (scd_vcpld_reload_causes[fault_loop].id == fault_cause)
			break;
	}
	if (fault_loop == MERU_VCPLD_FAULT_COUNT) {
		dev_info(&client->dev, "scd vcpld fault not found in list of reload causes\n");
		ret_val = -1;
	} else {
		dev_info(&client->dev, "scd vcpld reload cause: %s\n",
			scd_vcpld_reload_causes[fault_loop].description);
	}

	for (byte = 0; byte < VCPLD_RTC_SEC_REG_CNT; byte++) {
		op_status = i2c_smbus_read_byte_data(
			client,
			VCPLD_REG_TIMESTAMP_SEC_START + byte);
		if (op_status < 0) {
			dev_info(&client->dev, "failed to read fault timestamp\n");
			break;
		}
		fault_timestamp |= op_status << (8 * byte);
	}
	if (byte == VCPLD_RTC_SEC_REG_CNT) {
		rtc_counter_val = (time64_t)fault_timestamp + MILLENIUM_UNIX_TIMESTAMP;
		rtc_time64_to_tm(rtc_counter_val, &rtc_time_val);
		dev_info(&client->dev, "scd vcpld reload cause timestamp: %d-%d-%d, %d:%d:%d\n",
			rtc_time_val.tm_mon + 1,
			rtc_time_val.tm_mday,
			rtc_time_val.tm_year + 1900,
			rtc_time_val.tm_hour,
			rtc_time_val.tm_min,
			rtc_time_val.tm_sec);
	}

	op_status = i2c_smbus_write_byte_data(
		client,
		VCPLD_REG_FAULT_TEST_CONTROL,
		VCPLD_REG_FAULT_TEST_CONTROL_CLEAR_BITS);
	if (op_status < 0) {
		dev_info(&client->dev, "failed to erase fault memory\n");
		ret_val = op_status;
	}

	op_status = i2c_smbus_write_byte_data(
		client,
		VCPLD_REG_SCRATCHPAD,
		(u8)(1 << MERU_VCPLD_RELOAD_CAUSE_COOKIE_BITPOS));
	if (op_status < 0) {
		dev_info(&client->dev, "failed to write scratchpad register\n");
		ret_val = op_status;
	}

	return ret_val;
}

static int vcpld_i2c_probe(struct i2c_client *client)
{
	int op_status;
	u8 scratchpad, major_rev, minor_rev;

	op_status = i2c_smbus_read_byte_data(client, VCPLD_REG_MINOR_REV);
	if (op_status < 0) {
		dev_info(&client->dev, "failed to read minor revision register\n");
		return op_status;
	}
	minor_rev = (u8)op_status;

	op_status = i2c_smbus_read_byte_data(client, VCPLD_REG_MAJOR_REV);
	if (op_status < 0) {
		dev_info(&client->dev, "failed to read major revision register\n");
		return op_status;
	}
	major_rev = (u8)op_status;
	dev_info(&client->dev, "scd vcpld revision: %02x.%02x\n",
		major_rev, minor_rev);

	op_status = i2c_smbus_read_byte_data(client, VCPLD_REG_SCRATCHPAD);
	if (op_status < 0) {
		dev_info(&client->dev, "failed to read scratchpad register\n");
		return op_status;
	}
	vcpld_i2c_client = client;
	scratchpad = (u8)op_status;
	if ((scratchpad & MERU_VCPLD_RELOAD_CAUSE_COOKIE_MASK) == 0) {
		op_status = process_reload_cause(client);
		if (op_status < 0)
			dev_info(&client->dev, "error in processing reload cause\n");
	} else {
		dev_info(&client->dev, "didn't detect a system power cycle - not processing relaod cause");
	}

	schedule_delayed_work(&vcpld_delayed_work, RTC_UPDATE_INTERVAL*HZ);

	return 0;
}

static void vcpld_i2c_remove(struct i2c_client *client)
{
	cancel_delayed_work_sync(&vcpld_delayed_work);
}

static const struct i2c_device_id cpld_dev_ids[] = {
	{ "scd_vcpld", 0 },
	{}
};
MODULE_DEVICE_TABLE(i2c, cpld_dev_ids);

static struct i2c_driver cpld_i2c_driver = {
	.driver = {
		.name = "scd-vcpld",
	},
	.probe = vcpld_i2c_probe,
	.remove = vcpld_i2c_remove,
	.id_table = cpld_dev_ids,
};
module_i2c_driver(cpld_i2c_driver);

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Meru VCPLD I2C Driver");
MODULE_LICENSE("GPL");
