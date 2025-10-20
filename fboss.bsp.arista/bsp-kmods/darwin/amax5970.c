/* Copyright (c) 2021 Arista Networks, Inc.
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

/*
 * Driver for ECB controller on PEM.
 *
 * This driver controls the MAX5970 ECB controller on PEM. MAX5970 is a dual
 * channel ECB. In the PEM, the two channels are put parallel and each channel
 * taking half of the PEM output current. From MAX5970 registers, PEM's output
 * current and output voltage can be read. Over voltage, under voltage,
 * over current under current can also be set, and monitored by it.
 *
 * Chip readings and writings are consist of 10 bits using 2 seperate registers.
 * One register has the least significant 2 bits, and the other has the rest.
 *
 * This driver creates several device attributes in sysfs:
 *
 * in1_input
 * in2_input
 * in1_crit
 * in2_crit
 * in1_lcrit
 * in2_lcrit
 * curr1_input
 * curr2_input
 *
 */

#include <linux/err.h>
#include <linux/errno.h>
#include <linux/hwmon-sysfs.h>
#include <linux/hwmon.h>
#include <linux/i2c.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/sysfs.h>

#define DRIVER_NAME "amax5970"

/* I2C registers */
#define REG_CUR_UPPER_CH1 0x0
#define REG_CUR_LOWER_CH1 0x1
#define REG_VOL_UPPER_CH1 0x2
#define REG_VOL_LOWER_CH1 0x3
#define REG_CUR_UPPER_CH2 0x4
#define REG_CUR_LOWER_CH2 0x5
#define REG_VOL_UPPER_CH2 0x6
#define REG_VOL_LOWER_CH2 0x7

#define REG_UV_UPPER_CH1 0x1c
#define REG_UV_LOWER_CH1 0x1d
#define REG_OV_UPPER_CH1 0x20
#define REG_OV_LOWER_CH1 0x21
#define REG_UV_UPPER_CH2 0x26
#define REG_UV_LOWER_CH2 0x27
#define REG_OV_UPPER_CH2 0x2a
#define REG_OV_LOWER_CH2 0x2b

#define MASK_UPPER 0x3fc
#define MASK_LOWER 0x3
#define MAX_VALUE 0x3ff

struct amax5970_data {
	struct i2c_client *client;
	struct mutex update_lock;
};

/*-----------------------------------------------------------------------*/

/* device helpers */

/*-----------------------------------------------------------------------*/
static int __get_registers(enum hwmon_sensor_types type, u32 attr, int channel,
			   bool write, u8 *reg_upper, u8 *reg_lower)
{
	switch (type) {
	case hwmon_in:
		switch (attr) {
		case hwmon_in_input:
			if (write) {
				return -EOPNOTSUPP;
			}
			*reg_upper = (channel == 0 ? REG_VOL_UPPER_CH1 :
							   REG_VOL_UPPER_CH2);
			*reg_lower = (channel == 0 ? REG_VOL_LOWER_CH1 :
							   REG_VOL_LOWER_CH2);
			break;
		case hwmon_in_crit:
			*reg_upper = (channel == 0 ? REG_OV_UPPER_CH1 :
							   REG_OV_UPPER_CH2);
			*reg_lower = (channel == 0 ? REG_OV_LOWER_CH1 :
							   REG_OV_LOWER_CH2);
			break;
		case hwmon_in_lcrit:
			*reg_upper = (channel == 0 ? REG_UV_UPPER_CH1 :
							   REG_UV_UPPER_CH2);
			*reg_lower = (channel == 0 ? REG_UV_LOWER_CH1 :
							   REG_UV_LOWER_CH2);
			break;
		default:
			return -EOPNOTSUPP;
		}
		return 0;
	case hwmon_curr:
		switch (attr) {
		case hwmon_curr_input:
			if (write) {
				return -EOPNOTSUPP;
			}
			*reg_upper = (channel == 0 ? REG_CUR_UPPER_CH1 :
							   REG_CUR_UPPER_CH2);
			*reg_lower = (channel == 0 ? REG_CUR_LOWER_CH1 :
							   REG_CUR_LOWER_CH2);
			break;
		default:
			return -EOPNOTSUPP;
		}
		return 0;
		break;
	default:
		return -EOPNOTSUPP;
	}
	return 0;
}

static int __amax5970_read(struct i2c_client *client, u8 reg_upper,
			   u8 reg_lower)
{
	int value_upper = 0;
	int value_lower = 0;

	value_upper = i2c_smbus_read_byte_data(client, reg_upper);
	if (value_upper < 0) {
		return value_upper;
	}

	value_lower = i2c_smbus_read_byte_data(client, reg_lower);
	if (value_lower < 0) {
		return value_lower;
	}

	return (value_upper << 2 & MASK_UPPER) | (value_lower & MASK_LOWER);
}

static int __amax5970_write(struct i2c_client *client, u8 reg_upper,
			    u8 reg_lower, long val)
{
	int ret = 0;
	u16 value_upper = 0;
	u16 value_lower = 0;

	if (val > MAX_VALUE) {
		val = MAX_VALUE;
	}
	value_upper = (val & MASK_UPPER) >> 2;
	value_lower = val & MASK_LOWER;

	ret = i2c_smbus_write_byte_data(client, reg_upper, value_upper);
	if (ret < 0) {
		return ret;
	}
	ret = i2c_smbus_write_byte_data(client, reg_lower, value_lower);
	if (ret < 0) {
		return ret;
	}

	return 0;
}

/*-----------------------------------------------------------------------*/

/* sysfs attributes for hwmon */

/*-----------------------------------------------------------------------*/
#define AMAX5970_READ_FUNC(_type)						\
	static int amax5970_read_##_type(struct i2c_client *client, u32 attr,	\
					 int channel, long *val)		\
	{									\
		int ret = 0;							\
		u8 reg_upper = 0;						\
		u8 reg_lower = 0;						\
		bool write_chip = false;					\
										\
		ret = __get_registers(hwmon_##_type, attr, channel,		\
				      write_chip, &reg_upper, &reg_lower);	\
		if (ret < 0) {							\
			return ret;						\
		}								\
										\
		ret = __amax5970_read(client, reg_upper, reg_lower);		\
		if (ret < 0) {							\
			return ret;						\
		}								\
		*val = ret;							\
		return 0;							\
	}

AMAX5970_READ_FUNC(in);
AMAX5970_READ_FUNC(curr);

static int amax5970_write_in(struct i2c_client *client, u32 attr, int channel,
			     long val)
{
	int ret = 0;
	u8 reg_upper = 0;
	u8 reg_lower = 0;
	bool write_chip = true;
	if (val < 0)
		val = 0;

	ret = __get_registers(hwmon_in, attr, channel, write_chip, &reg_upper,
			      &reg_lower);
	if (ret < 0) {
		return ret;
	}

	ret = __amax5970_write(client, reg_upper, reg_lower, val);
	if (ret < 0) {
		return ret;
	}

	return 0;
}

static int amax5970_read(struct device *dev, enum hwmon_sensor_types type,
			 u32 attr, int channel, long *val)
{
	int ret = 0;
	struct amax5970_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;

	mutex_lock(&data->update_lock);
	switch (type) {
	case hwmon_in:
		ret = amax5970_read_in(client, attr, channel - 1, val);
		break;
	case hwmon_curr:
		ret = amax5970_read_curr(client, attr, channel, val);
		break;
	default:
		ret = -EOPNOTSUPP;
	}
	mutex_unlock(&data->update_lock);

	return ret;
}

static int amax5970_write(struct device *dev, enum hwmon_sensor_types type,
			  u32 attr, int channel, long val)
{
	int ret = 0;
	struct amax5970_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;

	mutex_lock(&data->update_lock);
	switch (type) {
	case hwmon_in:
		ret = amax5970_write_in(client, attr, channel - 1, val);
		break;
	default:
		ret = -EOPNOTSUPP;
	}
	mutex_unlock(&data->update_lock);

	return ret;
}

static umode_t amax5970_is_visible(const void *data,
				   enum hwmon_sensor_types type, u32 attr,
				   int channel)
{
	switch (type) {
	case hwmon_in:
		if (channel == 0) {
			return 0;
		}
		switch (attr) {
		case hwmon_in_input:
			return 0444;
		case hwmon_in_crit:
		case hwmon_in_lcrit:
			return 0644;
		default:
			return 0;
		}
	case hwmon_curr:
		switch (attr) {
		case hwmon_curr_input:
			return 0444;
		case hwmon_curr_crit:
		case hwmon_curr_lcrit:
			return 0644;
		default:
			return 0;
		}
	default:
		return 0;
	}
}

static const u32 amax5970_in_config[] = {
	HWMON_I_INPUT, /* Place holder */
	HWMON_I_INPUT | HWMON_I_CRIT | HWMON_I_LCRIT,
	HWMON_I_INPUT | HWMON_I_CRIT | HWMON_I_LCRIT, 0
};

static const struct hwmon_channel_info amax5970_in = {
	.type = hwmon_in,
	.config = amax5970_in_config,
};

static const u32 amax5970_curr_config[] = { HWMON_C_INPUT, HWMON_C_INPUT, 0 };

static const struct hwmon_channel_info amax5970_curr = {
	.type = hwmon_curr,
	.config = amax5970_curr_config,
};

static const struct hwmon_channel_info *amax5970_info[] = { &amax5970_in,
							    &amax5970_curr,
							    NULL };

static const struct hwmon_ops amax5970_hwmon_ops = {
	.is_visible = amax5970_is_visible,
	.read = amax5970_read,
	.write = amax5970_write,
};

static const struct hwmon_chip_info amax5970_chip_info = {
	.ops = &amax5970_hwmon_ops,
	.info = amax5970_info,
};

/*-----------------------------------------------------------------------*/

/* device probe and removal */

/*-----------------------------------------------------------------------*/

static void amax5970_remove(struct i2c_client *client)
{
	struct amax5970_data *data = dev_get_drvdata(&client->dev);

	mutex_destroy(&data->update_lock);
}

static int amax5970_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct device *hwmon_dev;
	struct amax5970_data *data;

	data = devm_kzalloc(dev, sizeof(struct amax5970_data), GFP_KERNEL);
	if (!data) {
		return -ENOMEM;
	}

	data->client = client;
	mutex_init(&data->update_lock);

	/* Register sysfs hooks */
	hwmon_dev = devm_hwmon_device_register_with_info(
		dev, client->name, data, &amax5970_chip_info, NULL);

	if (IS_ERR(hwmon_dev)) {
		return PTR_ERR(hwmon_dev);
	}
	dev_info(dev, "Detected MAX5970\n");

	return 0;
}

static struct i2c_device_id amax5970_id[] = {
	{ DRIVER_NAME, 0 },
	{},
};

MODULE_DEVICE_TABLE(i2c, amax5970_id);

static struct i2c_driver amax5970_driver = {
	.class = I2C_CLASS_HWMON,
	.driver = {
		.name = DRIVER_NAME,
	},
	.id_table = amax5970_id,
	.probe = amax5970_probe,
	.remove = amax5970_remove,
};

module_i2c_driver(amax5970_driver);

MODULE_AUTHOR("Tom Meng");
MODULE_DESCRIPTION("Arista MAX5970 Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(BSP_VERSION);
