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
 * Driver for SLG4F4527 controller on FanSpinner.
 *
 * This driver controls the SLG4F45247 controller on FanSpinner. It drives a
 * single PWM output and monitors two RPM inputs. Additionally, several I2C
 * registers can be used to drive GPOs for controlling the FanSpinner status
 * LED, IDPROM write protect, Rackmon IDPROM write protect, and Rackmon
 * power cycle. These registers are set via bits in a single virtual input
 * register.
 *
 * There are two PWM target registers, one active and one standby. The set value
 * of the CNT_SEL register bit selects the active PWM. To update the PWM target,
 * write the new target to the standby target register and toggle the CNT_SEL.
 * A third PWM register syncs the PWM generator; this register is written once
 * at init. The PWM target register values indicate the low duty cycle, so
 * the target PWM must be inverted (e.g. 100% = 1, 0% = 254).
 *
 * The RPM is counted downward from an initial count, default 65535, with a
 * 125kHz clock. A new RPM sample must be triggered by software by writing
 * the RPM_SAMPLE register bit then waiting the required interval.
 *
 * This driver creates several device attributes in sysfs hwmon:
 *
 * pwm
 * inner_fan_rpm
 * outer_fan_rpm
 * fan1_input
 * led_red
 * led_green
 * idprom_wp
 * rm_idprom_wp
 * rm_pwr_cyc
 *
 * as well as a rackmon::status LED in /sys/class/leds/.
 */

#include <linux/bitops.h>
#include <linux/delay.h>
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/hwmon-sysfs.h>
#include <linux/hwmon.h>
#include <linux/i2c.h>
#include <linux/init.h>
#include <linux/jiffies.h>
#include <linux/leds.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/sysfs.h>

#define DRIVER_NAME "aslg4f4527"

#define FAN_COUNT 1

/* I2C registers */
#define REG_VIRTUAL_INPUT 0xF4
#define REG_CNT0_CONTROL_DATA 0xC5 /* RPM0 initial count */
#define REG_CNT0_COUNTED_VALUE 0xEB /* RPM0 tach count */
#define REG_CNT1_CONTROL_DATA 0xC7 /* RPM1 initial count */
#define REG_CNT1_COUNTED_VALUE 0xEE /* RPM1 tach count */
#define REG_CNT2_CONTROL_DATA 0xC0 /* PWM sync and set output low */
#define REG_CNT3_CONTROL_DATA 0xC1 /* PWM target 0, CNT_SEL = 0 to select */
#define REG_CNT4_CONTROL_DATA 0xC2 /* PWM target 1, CNT_SEL = 1 to select */

/* Virtual Input register bits */
enum virtual_input_bits {
	CNT_SEL = 0, /* Indicates which PWM target is active */
	RPM_SAMPLE, /* Drive rising edge to take new RPM sample */
	PWR_OFF, /* Device power status, unused */
	IDPROM_WP, /* FanSpinner IDPROM write protect */
	RLED_L, /* Red status LED GPO, active low */
	RM_PWR_CYC, /* Rackmon power cycle GPO */
	GLED_L, /* Green status LED GPO, active low */
	RM_IDPROM_WP, /* Rackmon IDPROM write protect */
};

/* PWM definitions */
#define PWM_MAX 254 /* 255 not supported */
#define PWM_MIN 1 /* 0 not supported */
#define PWM_DEFAULT 127 /* Default 50% duty cycle */

enum cnt_sel_pwm_targets {
	PWM_TARGET_0 = 0,
	PWM_TARGET_1,
};

enum pwm_target_status {
	STANDBY = 0,
	ACTIVE,
};

/* Used for RPM calculations */
#define CLOCK_HZ 125000
#define RPM_SAMPLE_WAIT_MS 53
#define RPM_SAMPLE_INTERVAL_MS 500

struct aslg4f4527_data {
	struct i2c_client *client;
	const struct attribute_group *groups[1 + FAN_COUNT + 1];
	struct mutex update_lock;
	unsigned long last_sample;
	unsigned int sample_interval;
	int pwm_updated;

	/* Register values */
	u16 inner_tach_initial_count;
	u16 outer_tach_initial_count;

	/* Calculated RPMs */
	s32 inner_fan_rpm;
	s32 outer_fan_rpm;
	s32 fan1_input; /* Average of inner and outer */

	struct led_classdev cdev;
};

/*-----------------------------------------------------------------------*/

/* device helpers */

static s32 read_virtual_input(struct i2c_client *client, u8 offset, u8 *val)
{
	s32 err;

	err = i2c_smbus_read_byte_data(client, REG_VIRTUAL_INPUT);
	if (err < 0) {
		return err;
	}

	*val = (err >> offset) & 1;

	return 0;
}

static s32 write_virtual_input(struct i2c_client *client, u8 offset, u8 req_val)
{
	s32 err;

	err = i2c_smbus_read_byte_data(client, REG_VIRTUAL_INPUT);
	if (err < 0) {
		return err;
	}

	err &= ~(1 << offset);
	err |= (req_val & 1) << offset;
	err = i2c_smbus_write_byte_data(client, REG_VIRTUAL_INPUT, err);

	return err;
}

static s32 read_tach(struct i2c_client *client, u8 reg, u16 *val)
{
	s32 err;

	err = i2c_smbus_read_word_data(client, reg);
	if (err < 0) {
		return err;
	}

	*val = err & 0xffff;

	return 0;
}

static s32 calculate_rpm(u16 initial_count, u16 tach)
{
	s32 val;

	/* Prevent division by zero in case of a misread. In valid reading,
	 * tach cannot be greated than initial_count because tach counts down
	 * from initial count. */
	if (initial_count - tach <= 0) {
		return 0;
	}

	val = (CLOCK_HZ * 60) / (initial_count - tach);
	return val;
}

static struct aslg4f4527_data *sample_rpm(struct device *dev)
{
	struct aslg4f4527_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;
	struct aslg4f4527_data *ret = data;
	unsigned long next_sample;
	u16 inner_tach;
	u16 outer_tach;
	s32 err;

	mutex_lock(&data->update_lock);

	/* Take a new sample when the interval has passed or when the PWM target has
	 * been updated.
	 */
	next_sample =
		data->last_sample + msecs_to_jiffies(data->sample_interval);
	if (time_after(jiffies, next_sample) || data->pwm_updated) {
		/* Generate rising edge to trigger new RPM sample. */
		err = write_virtual_input(client, RPM_SAMPLE, 0);
		if (err < 0) {
			ret = ERR_PTR(err);
			goto abort_sample;
		}
		err = write_virtual_input(client, RPM_SAMPLE, 1);
		if (err < 0) {
			ret = ERR_PTR(err);
			goto abort_sample;
		}

		/* Wait for counts to be available */
		msleep(RPM_SAMPLE_WAIT_MS);

		/* Read tach */
		err = read_tach(client, REG_CNT0_COUNTED_VALUE, &inner_tach);
		if (err < 0) {
			ret = ERR_PTR(err);
			goto abort_sample;
		}
		err = read_tach(client, REG_CNT1_COUNTED_VALUE, &outer_tach);
		if (err < 0) {
			ret = ERR_PTR(err);
			goto abort_sample;
		}

		/* Calculate RPM from tach */
		data->inner_fan_rpm = calculate_rpm(
			data->inner_tach_initial_count, inner_tach);
		data->outer_fan_rpm = calculate_rpm(
			data->outer_tach_initial_count, outer_tach);
		data->fan1_input =
			(data->inner_fan_rpm + data->outer_fan_rpm) / 2;

		data->last_sample = jiffies;
		data->pwm_updated = 0;
	}

abort_sample:
	mutex_unlock(&data->update_lock);
	return ret;
}

static s32 get_pwm_target_reg(struct i2c_client *client, u8 status, u8 *reg)
{
	u8 cnt_sel;
	s32 err;

	/* Read the count select bit to get the active PWM target */
	err = read_virtual_input(client, CNT_SEL, &cnt_sel);
	if (err < 0) {
		return err;
	}

	/* If standby register is requested, flip the count select bit */
	if (status == STANDBY) {
		cnt_sel = !cnt_sel;
	}

	*reg = (cnt_sel == PWM_TARGET_0) ? REG_CNT3_CONTROL_DATA :
						 REG_CNT4_CONTROL_DATA;

	return 0;
}

static s32 read_pwm(struct i2c_client *client, u8 *pwm)
{
	u8 active_pwm_target_reg;
	s32 err;

	err = get_pwm_target_reg(client, ACTIVE, &active_pwm_target_reg);
	if (err < 0) {
		return err;
	}

	err = i2c_smbus_read_byte_data(client, active_pwm_target_reg);
	if (err < 0) {
		return err;
	}

	/* Invert PWM target as in SW the target is the high duty cycle but in
	 * the register the value represents low duty cycle.
	 */
	*pwm = 255 - (err & 0xff);

	return 0;
}

static s32 write_pwm(struct i2c_client *client, u8 pwm_target)
{
	u8 standby_pwm_target_reg;
	s32 err;

	err = get_pwm_target_reg(client, STANDBY, &standby_pwm_target_reg);
	if (err < 0) {
		return err;
	}

	/* PWM target registers don't support 0 and 255 values, so adjust as
	 * needed.
	 */
	if (pwm_target < PWM_MIN) {
		pwm_target = PWM_MIN;
	} else if (pwm_target > PWM_MAX) {
		pwm_target = PWM_MAX;
	}

	pwm_target = 255 - pwm_target;

	/* Update the standby PWM target register */
	err = i2c_smbus_write_byte_data(client, standby_pwm_target_reg,
					pwm_target);
	if (err < 0) {
		return err;
	}

	/* Toggle the count select bit for the new PWM target to take effect */
	if (standby_pwm_target_reg == REG_CNT3_CONTROL_DATA) {
		err = write_virtual_input(client, CNT_SEL, PWM_TARGET_0);
	} else {
		err = write_virtual_input(client, CNT_SEL, PWM_TARGET_1);
	}

	return err;
}

/*-----------------------------------------------------------------------*/

/* sysfs attributes for hwmon */

static ssize_t pwm_show(struct device *dev, struct device_attribute *attr,
			char *buf)
{
	struct aslg4f4527_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;
	u8 pwm;
	s32 err;

	mutex_lock(&data->update_lock);
	err = read_pwm(client, &pwm);
	mutex_unlock(&data->update_lock);
	if (err < 0) {
		return err;
	}

	return sprintf(buf, "%hhu\n", pwm);
}

static ssize_t pwm_store(struct device *dev, struct device_attribute *attr,
			 const char *buf, size_t count)
{
	struct aslg4f4527_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;
	u8 pwm;
	s32 err;

	if (sscanf(buf, "%hhu", &pwm) != 1) {
		return -EINVAL;
	}

	mutex_lock(&data->update_lock);
	err = write_pwm(client, pwm);
	mutex_unlock(&data->update_lock);
	if (err < 0) {
		return err;
	};

	data->pwm_updated = 1;
	return count;
}

#define SLG4F4527_FAN_ATTR(_name, _idx)                                        	\
	static ssize_t _name##_show(struct device *dev,                        	\
				    struct device_attribute *attr, char *buf)  	\
	{                                                                      	\
		struct aslg4f4527_data *data = sample_rpm(dev);                	\
										\
		if (IS_ERR(data)) {                                            	\
			return PTR_ERR(data);                                  	\
		}                                                              	\
										\
		return sprintf(buf, "%d\n", data->_name);                      	\
	}                                                                      	\
										\
	static SENSOR_DEVICE_ATTR(_name, S_IRUGO, _name##_show, NULL, _idx);

#define SLG4F4527_GPO_ATTR(_name, _reg)                                        	\
	static ssize_t _name##_show(struct device *dev,                        	\
				    struct device_attribute *attr, char *buf)  	\
	{                                                                      	\
		struct aslg4f4527_data *data = dev_get_drvdata(dev);           	\
		u8 val;                                                        	\
										\
		mutex_lock(&data->update_lock);                                	\
		read_virtual_input(data->client, _reg, &val);                  	\
		mutex_unlock(&data->update_lock);                              	\
										\
		return sprintf(buf, "%hhu\n", val);                            	\
	}                                                                      	\
										\
	static ssize_t _name##_store(struct device *dev,                       	\
				     struct device_attribute *attr,            	\
				     const char *buf, size_t count)            	\
	{									\
		struct aslg4f4527_data *data = dev_get_drvdata(dev);           	\
		u8 val;                                                        	\
		s32 err;                                                       	\
										\
		if (sscanf(buf, "%hhu", &val) != 1) {                          	\
			return -EINVAL;                                        	\
		}                                                              	\
										\
		mutex_lock(&data->update_lock);                                	\
		err = write_virtual_input(data->client, _reg, val);            	\
		mutex_unlock(&data->update_lock);                              	\
										\
		if (err < 0) {                                                 	\
			return err;                                            	\
		}                                                              	\
										\
		return count;                                                 	\
	}                                                                      	\
	static DEVICE_ATTR(_name, S_IRUGO | S_IWGRP | S_IWUSR, _name##_show,   	\
			   _name##_store);

DEVICE_ATTR(pwm, S_IRUGO | S_IWGRP | S_IWUSR, pwm_show, pwm_store);
SLG4F4527_FAN_ATTR(fan1_input, 1);
SLG4F4527_FAN_ATTR(inner_fan_rpm, 2);
SLG4F4527_FAN_ATTR(outer_fan_rpm, 3);

static struct attribute *aslg4f4527_sensor_attrs[] = {
	&dev_attr_pwm.attr,
	&sensor_dev_attr_inner_fan_rpm.dev_attr.attr,
	&sensor_dev_attr_outer_fan_rpm.dev_attr.attr,
	&sensor_dev_attr_fan1_input.dev_attr.attr,
	NULL,
};

static const struct attribute_group aslg4f4527_sensor_group = {
	.attrs = aslg4f4527_sensor_attrs,
};

SLG4F4527_GPO_ATTR(led_red, RLED_L);
SLG4F4527_GPO_ATTR(led_green, GLED_L);
SLG4F4527_GPO_ATTR(idprom_wp, IDPROM_WP);
SLG4F4527_GPO_ATTR(rm_idprom_wp, RM_IDPROM_WP);
SLG4F4527_GPO_ATTR(rm_pwr_cyc, RM_PWR_CYC);

static struct attribute *aslg4f4527_gpo_attrs[] = {
	&dev_attr_led_red.attr,	   &dev_attr_led_green.attr,
	&dev_attr_idprom_wp.attr,  &dev_attr_rm_idprom_wp.attr,
	&dev_attr_rm_pwr_cyc.attr, NULL,
};

static const struct attribute_group aslg4f4527_gpo_group = {
	.attrs = aslg4f4527_gpo_attrs,
};

/*-----------------------------------------------------------------------
 * led_classdev functions for rackmon LED
 *
 * Valid LED settings are:
 * 0 = off
 * 1 = red
 * 2 = green
 *
 * LED registers are active low so negate register values.
 */

#define LED_RED_BIT	0
#define LED_GREEN_BIT	1

static void brightness_set(struct led_classdev *led_cdev,
			   enum led_brightness val)
{
	struct aslg4f4527_data *data =
		container_of(led_cdev, struct aslg4f4527_data, cdev);

	write_virtual_input(data->client, RLED_L, (~val >> LED_RED_BIT) & 1);
	write_virtual_input(data->client, GLED_L, (~val >> LED_GREEN_BIT) & 1);
}

static enum led_brightness brightness_get(struct led_classdev *led_cdev)
{
	struct aslg4f4527_data *data =
		container_of(led_cdev, struct aslg4f4527_data, cdev);
	u8 red_val, green_val;

	read_virtual_input(data->client, RLED_L, &red_val);
	read_virtual_input(data->client, GLED_L, &green_val);

	return ((~red_val & 1) << LED_RED_BIT) | ((~green_val & 1) << LED_GREEN_BIT);
}

/*-----------------------------------------------------------------------*/

/* initializing device  */

static int aslg4f4527_init_client(struct aslg4f4527_data *data,
				  struct i2c_client *client)
{
	int ret = 0;

	mutex_lock(&data->update_lock);

	/* CNT2 register is not used to set PWM, so set to 0xff */
	ret = i2c_smbus_write_byte_data(client, REG_CNT2_CONTROL_DATA,
					PWM_MAX + 1);
	if (ret < 0) {
		goto abort_init;
	}

	/* Set PWM to max by default. */
	ret = write_pwm(client, PWM_DEFAULT);
	if (ret < 0) {
		goto abort_init;
	}
	data->pwm_updated = 1;

	/* Read tach counter initial values. Tach counters cound down from
	 * initial values.
	 */
	ret = i2c_smbus_read_word_data(client, REG_CNT0_CONTROL_DATA);
	if (ret < 0) {
		goto abort_init;
	}
	data->inner_tach_initial_count = ret & 0xffff;

	ret = i2c_smbus_read_word_data(client, REG_CNT1_CONTROL_DATA);
	if (ret < 0) {
		goto abort_init;
	}
	data->outer_tach_initial_count = ret & 0xffff;
	data->sample_interval = RPM_SAMPLE_INTERVAL_MS;

	/* Init led class. */
	data->cdev.name = "rackmon::status";
	data->cdev.brightness_set = brightness_set;
	data->cdev.brightness_get = brightness_get;
	ret = devm_led_classdev_register(&client->dev, &data->cdev);

abort_init:
	mutex_unlock(&data->update_lock);
	return ret;
}

/*-----------------------------------------------------------------------*/

/* device probe and removal */

static void aslg4f4527_remove(struct i2c_client *client)
{
	struct aslg4f4527_data *data = dev_get_drvdata(&client->dev);

	mutex_destroy(&data->update_lock);
}

static int aslg4f4527_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct device *hwmon_dev;
	struct aslg4f4527_data *data;
	int groups = 0;
	int status;

	data = devm_kzalloc(dev, sizeof(struct aslg4f4527_data), GFP_KERNEL);
	if (!data) {
		return -ENOMEM;
	}

	data->client = client;
	mutex_init(&data->update_lock);

	status = aslg4f4527_init_client(data, client);
	if (status < 0) {
		return status;
	}

	/* Register sysfs hooks */
	data->groups[groups++] = &aslg4f4527_sensor_group;
	data->groups[groups++] = &aslg4f4527_gpo_group;

	hwmon_dev = devm_hwmon_device_register_with_groups(dev, client->name,
							   data, data->groups);
	if (IS_ERR(hwmon_dev)) {
		return PTR_ERR(hwmon_dev);
	}
	dev_info(dev, "Detected SLG4F4527\n");

	return 0;
}

static struct i2c_device_id aslg4f4527_id[] = {
	{ DRIVER_NAME, 0 },
	{},
};

MODULE_DEVICE_TABLE(i2c, aslg4f4527_id);

static struct i2c_driver aslg4f4527_driver = {
	.class = I2C_CLASS_HWMON,
	.driver = {
		.name = DRIVER_NAME,
	},
	.id_table = aslg4f4527_id,
	.probe = aslg4f4527_probe,
	.remove = aslg4f4527_remove,
};

module_i2c_driver(aslg4f4527_driver);

MODULE_AUTHOR("Adam Calabrigo");
MODULE_DESCRIPTION("Arista SLG4F4527 Driver");
MODULE_LICENSE("GPL");
