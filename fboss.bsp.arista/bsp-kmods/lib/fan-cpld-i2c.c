/* Copyright (c) 2025 Arista Networks, Inc.
 *
 * This program is free software; you can amberistribute it and/or modify
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
#include <linux/moduleparam.h>
#include <linux/device.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/i2c.h>
#include <linux/slab.h>
#include <linux/workqueue.h>
#include <linux/mutex.h>
#include <linux/leds.h>
#include <linux/watchdog.h>
#include <linux/version.h>

#include "fan-cpld-i2c.h"

static struct workqueue_struct *fan_cpld_workqueue = NULL;
static int workqueue_users = 0;
static DEFINE_MUTEX(workqueue_lock);

int fan_cpld_workqueue_init(const char *name)
{
	int ret = 0;

	mutex_lock(&workqueue_lock);

	if (workqueue_users == 0) {
		fan_cpld_workqueue = create_singlethread_workqueue("fan_cpld");
		if (!fan_cpld_workqueue) {
			mutex_unlock(&workqueue_lock);
			return -ENOMEM;
		}
	}

	workqueue_users++;
	mutex_unlock(&workqueue_lock);
	return ret;
}

void fan_cpld_workqueue_cleanup(void)
{
	mutex_lock(&workqueue_lock);

	workqueue_users--;
	if (workqueue_users == 0 && fan_cpld_workqueue) {
		destroy_workqueue(fan_cpld_workqueue);
		fan_cpld_workqueue = NULL;
	}

	mutex_unlock(&workqueue_lock);
}

static struct fan_cpld_data *to_fan_cpld_wdt(struct watchdog_device *wdd)
{
	return container_of(wdd, struct fan_cpld_data, wdd);
}

static struct fan_cpld_fan_data *fan_from_fan_cpld(struct fan_cpld_data *cpld,
						   u8 fan_id)
{
	return &cpld->fans[fan_id];
}

static struct fan_cpld_fan_data *fan_from_dev(struct device *dev, u8 fan_id)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	return fan_from_fan_cpld(fan_cpld, fan_id);
}

static struct device *dev_from_fan_cpld(struct fan_cpld_data *fan_cpld)
{
	return &fan_cpld->client->dev;
}

static s32 fan_cpld_read_byte(struct fan_cpld_data *fan_cpld, u8 reg, u8 *res)
{
	int err;

	err = i2c_smbus_read_byte_data(fan_cpld->client, reg);
	if (err < 0) {
		dev_err(&fan_cpld->client->dev,
			"failed to read reg 0x%02x error=%d\n", reg, err);
		return err;
	}

	*res = (err & 0xff);
	return 0;
}

static s32 fan_cpld_write_byte(struct fan_cpld_data *fan_cpld, u8 reg, u8 byte)
{
	int err;

	err = i2c_smbus_write_byte_data(fan_cpld->client, reg, byte);
	if (err) {
		dev_err(&fan_cpld->client->dev,
			"failed to write 0x%02x in reg 0x%02x error=%d\n", byte,
			reg, err);
	}

	return err;
}

static s32 fan_cpld_read_fan_id(struct fan_cpld_data *fan_cpld, u8 fan_id)
{
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, fan_id);
	s32 err;
	u8 tmp;

	err = fan_cpld_read_byte(fan_cpld, FAN_ID_REG(fan->index), &tmp);
	if (err)
		return err;

	fan->ident = tmp & 0xf;
	fan->reverse = (tmp >> 4) & 0x1;

	return 0;
}

static int fan_cpld_update(struct fan_cpld_data *fan_cpld)
{
	struct device *dev = dev_from_fan_cpld(fan_cpld);
	struct fan_cpld_fan_data *fan;
	const char *str;
	int fans_connected = 0;
	int err;
	int i;
	u8 interrupt, id_chng = 0, ok_chng = 0, pres_chng = 0;

	dev_dbg(dev, "polling cpld information\n");

	err = fan_cpld_read_byte(fan_cpld, FAN_INT_REG, &interrupt);
	if (err)
		goto fail;

	if (interrupt & FAN_INT_ID) {
		err = fan_cpld_read_byte(fan_cpld, FAN_ID_CHNG_REG, &id_chng);
		if (err)
			goto fail;
	}

	if (interrupt & FAN_INT_OK) {
		err = fan_cpld_read_byte(fan_cpld, FAN_OK_CHNG_REG, &ok_chng);
		if (err)
			goto fail;
		err = fan_cpld_read_byte(fan_cpld, FAN_OK_REG, &fan_cpld->ok);
		if (err)
			goto fail;
	}

	if (interrupt & FAN_INT_PRES) {
		err = fan_cpld_read_byte(fan_cpld, FAN_PRESENT_CHNG_REG, &pres_chng);
		if (err)
			goto fail;
		err = fan_cpld_read_byte(fan_cpld, FAN_OK_REG, &fan_cpld->present);
		if (err)
			goto fail;
	}

	for (i = 0; i < fan_cpld->info->fan_count; ++i) {
		fan = fan_from_fan_cpld(fan_cpld, i);

		if ((interrupt & FAN_INT_PRES) && (pres_chng & (1 << fan->index))) {
			if (fan->present && (fan_cpld->present & (1 << fan->index))) {
				str = "hotswapped";
			} else if (!fan->present &&
				   (fan_cpld->present & (1 << fan->index))) {
				str = "plugged";
				fan->present = true;
			} else {
				str = "unplugged";
				fan->present = false;
			}
			dev_info(dev, "fan %d was %s\n", fan->index + 1, str);
		}

		if ((interrupt & FAN_INT_OK) && (ok_chng & (1 << fan->index))) {
			if (fan->ok && (fan_cpld->ok & (1 << fan->index))) {
				dev_warn(dev, "fan %d had a small snag\n",
					 fan->index + 1);
			} else if (fan->ok && !(fan_cpld->ok & (1 << fan->index))) {
				dev_warn(dev,
					 "fan %d is in fault, likely stuck\n",
					 fan->index + 1);
				fan->ok = false;
			} else {
				dev_info(
					dev,
					"fan %d has recoveamber a running state\n",
					fan->index + 1);
				fan->ok = true;
			}
		}

		if ((interrupt & FAN_INT_ID) && (id_chng & (1 << fan->index))) {
			dev_info(dev, "fan %d kind has changed\n", fan->index + 1);
			fan_cpld_read_fan_id(fan_cpld, fan->index);
		}

		if (fan->present)
			fans_connected += 1;
	}

	if (fan_cpld->info->fan_count - fans_connected > 1) {
		dev_warn(dev,
			 "it is not recommended to have more than one fan "
			 "unplugged. (%d/%d connected)\n",
			 fans_connected, fan_cpld->info->fan_count);
	}

	fan_cpld_write_byte(fan_cpld, FAN_ID_CHNG_REG, id_chng);
	fan_cpld_write_byte(fan_cpld, FAN_OK_CHNG_REG, ok_chng);
	fan_cpld_write_byte(fan_cpld, FAN_PRESENT_CHNG_REG, pres_chng);
fail:
	return err;
}

static s32 fan_cpld_write_pwm(struct fan_cpld_data *fan_cpld, u8 fan_id, u8 pwm)
{
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, fan_id);
	int err = 0;

	/* PWM setting is the same for all rotors. */
	err = fan_cpld_write_byte(fan_cpld, FAN_PWM_REG(fan->index), pwm);
	if (err)
		return err;

	fan->pwm = pwm;

	return err;
}

static int fan_cpld_read_present(struct fan_cpld_data *fan_cpld)
{
	struct fan_cpld_fan_data *fan;
	int err;
	int i;

	err = fan_cpld_read_byte(fan_cpld, FAN_PRESENT_REG, &fan_cpld->present);
	if (err)
		return err;

	for (i = 0; i < fan_cpld->info->fan_count; ++i) {
		fan = fan_from_fan_cpld(fan_cpld, i);
		fan->present = !!(fan_cpld->present & (1 << fan->index));
	}

	return 0;
}

static int fan_cpld_read_fault(struct fan_cpld_data *fan_cpld)
{
	struct fan_cpld_fan_data *fan;
	int err;
	int i;

	err = fan_cpld_read_byte(fan_cpld, FAN_OK_REG, &fan_cpld->ok);
	if (err)
		return err;

	for (i = 0; i < fan_cpld->info->fan_count; ++i) {
		fan = fan_from_fan_cpld(fan_cpld, i);
		fan->ok = !!(fan_cpld->ok & (1 << fan->index));
	}

	return 0;
}

static s32 fan_cpld_read_tach_single(struct fan_cpld_data *fan_cpld, u8 fan_index,
				     u8 rotor_num, u16 *tach)
{
	int err;
	u8 low;
	u8 high;

	err = fan_cpld_read_byte(fan_cpld,
				 FAN_TACH_REG_LOW(fan_index, rotor_num),
				 &low);
	if (err)
		return err;

	err = fan_cpld_read_byte(fan_cpld,
				 FAN_TACH_REG_HIGH(fan_index, rotor_num),
				 &high);
	if (err)
		return err;

	*tach = ((u16)high << 8) | low;

	return 0;
}

static s32 fan_cpld_read_fan_tach(struct fan_cpld_data *fan_cpld, u8 fan_id)
{
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, fan_id);
	s32 err = 0;
	u16 tach;
	int i;

	fan->tach = 0;
	for (i = 0; i < fan_cpld->info->rotors; i++) {
		err = fan_cpld_read_tach_single(fan_cpld, fan->index, i, &tach);
		if (err)
			break;
		fan->tach += tach;

		dev_dbg(dev_from_fan_cpld(fan_cpld), "fan%d/%d tach=0x%04x\n",
			fan->index + 1, i + 1, fan->tach);
		if (fan->tach == 0xffff) {
			fan_cpld_read_present(fan_cpld);
			fan_cpld_read_fault(fan_cpld);
			if (!fan->present)
				return -ENODEV;

			dev_warn( dev_from_fan_cpld(fan_cpld),
				  "Invalid tach information read from fan %d, "
				  "this is likely a hardware issue (stuck fan "
				  "or broken register)\n",
				  fan->index + 1);

			return -EIO;
		}
	}

	fan->tach = fan->tach / fan_cpld->info->rotors;

	return err;
}

static s32 fan_cpld_read_fan_pwm(struct fan_cpld_data *fan_cpld, u8 fan_id)
{
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, fan_id);
	int err;
	u8 pwm;

	err = fan_cpld_read_byte(fan_cpld, FAN_PWM_REG(fan->index), &pwm);
	if (err)
		return err;

	fan->pwm = pwm;

	return 0;
}

static enum led_brightness fan_cpld_read_fan_led(struct fan_cpld_data *data,
			   struct fan_cpld_fan_led_data *led) {
	int is_on;
	if (!strcmp(led->color, "blue")) {
		is_on = ((data->blue_led >> led->fan_index) & 1);
	} else {
		is_on = ((data->amber_led >> led->fan_index) & 1);
	}
	if (is_on)
		return LED_FULL;
	return LED_OFF;
}

static s32 fan_cpld_write_fan_led(struct fan_cpld_data *fan_cpld,
				  struct fan_cpld_fan_led_data *led,
				  enum led_brightness val) {
	int err1, err2 = 0;

	if (val == LED_OFF) {
		// turn both leds off
		fan_cpld->blue_led &= ~(1 << led->fan_index);
		fan_cpld->amber_led &= ~(1 << led->fan_index);
	} else {
		if (!strcmp(led->color, "blue")) {
			fan_cpld->blue_led |= (1 << led->fan_index);
			fan_cpld->amber_led &= ~(1 << led->fan_index);
		} else {
			fan_cpld->amber_led |= (1 << led->fan_index);
			fan_cpld->blue_led &= ~(1 << led->fan_index);
		}
	}

	err1 = fan_cpld_write_byte(fan_cpld, FAN_BLUE_LED_REG, fan_cpld->blue_led);
	err2 = fan_cpld_write_byte(fan_cpld, FAN_AMBER_LED_REG, fan_cpld->amber_led);
	return err1|err2;
}

static void brightness_set(struct led_classdev *led_cdev,
			   enum led_brightness val) {
	struct fan_cpld_fan_led_data *led =
		container_of(led_cdev, struct fan_cpld_fan_led_data, cdev);
	struct fan_cpld_data *data = dev_get_drvdata(led_cdev->dev->parent);

	fan_cpld_write_fan_led(data, led, val);
}

static enum led_brightness brightness_get(struct led_classdev *led_cdev) {
	struct fan_cpld_fan_led_data *led =
		container_of(led_cdev, struct fan_cpld_fan_led_data, cdev);
	struct fan_cpld_data *data = dev_get_drvdata(led_cdev->dev->parent);
	return fan_cpld_read_fan_led(data, led);
}

static int led_init(struct fan_cpld_fan_led_data leds[], struct i2c_client *client,
		    struct fan_cpld_fan_data *fan) {
	int err;
	const char *colors[] = {"blue", "amber"};
	for (int i = 0; i < FAN_LED_COUNT; i++) {
		scnprintf(leds[i].name, LED_NAME_MAX_SZ, "fan%d_led:%s:status",
				fan->global_index + 1, colors[i]);
		leds[i].fan_index = fan->index;
		leds[i].cdev.name = leds[i].name;
		scnprintf(leds[i].color, LED_NAME_MAX_SZ, "%s", colors[i]);
		leds[i].cdev.brightness_set = brightness_set;
		leds[i].cdev.brightness_get = brightness_get;
		leds[i].cdev.max_brightness = LED_FULL;

		err = devm_led_classdev_register(&client->dev, &leds[i].cdev);
		if (err) {
		dev_err(&client->dev, "failed to register %s led\n", colors[i]);
		return err;
		}
	}
	return 0;
}

static ssize_t fan_cpld_fan_pwm_show(struct device *dev,
				     struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, attr->index);
	int err;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_read_fan_pwm(fan_cpld, attr->index);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	return sprintf(buf, "%hhu\n", fan->pwm);
}

static ssize_t fan_cpld_fan_pwm_store(struct device *dev,
				      struct device_attribute *da, const char *buf,
				      size_t count)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	u8 val;
	int err;

	if (sscanf(buf, "%hhu", &val) != 1)
		return -EINVAL;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_write_pwm(fan_cpld, attr->index, val);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	return count;
}

static s32 fan_cpld_read_wdt_boost_pwm(struct fan_cpld_data *fan_cpld)
{
	int err;
	u8 pwm;

	err = fan_cpld_read_byte(fan_cpld, WDT_BOOST_PWM, &pwm);
	if (err)
		return err;

	fan_cpld->wdt_boost_pwm = pwm;

	return 0;
}

static s32 fan_cpld_write_wdt_boost_pwm(struct fan_cpld_data *fan_cpld, u8 pwm)
{
	int err = 0;

	err = fan_cpld_write_byte(fan_cpld, WDT_BOOST_PWM, pwm);
	if (err)
		return err;

	fan_cpld->wdt_boost_pwm = pwm;

	return err;
}

int fan_wdt_start(struct watchdog_device *wdd)
{
	int err;
	struct fan_cpld_data *fan_cpld = to_fan_cpld_wdt(wdd);

	err = fan_cpld_write_byte(fan_cpld, WDT_ENABLE, 1);
	if (err)
		return err;

	err = fan_cpld_write_byte(fan_cpld, WDT_COUNTER, wdd->timeout);
	if (err)
		return err;

	return 0;
}

int fan_wdt_stop(struct watchdog_device *wdd)
{
	int err;
	struct fan_cpld_data *fan_cpld = to_fan_cpld_wdt(wdd);

	err = fan_cpld_write_byte(fan_cpld, WDT_ENABLE, 0);
	if (err)
		return err;

	return 0;
}

int fan_wdt_ping(struct watchdog_device *wdd)
{
	int err;

	err = fan_wdt_start(wdd);
	if (err)
		return err;

	return 0;
}

static ssize_t fan_cpld_fan_present_show(struct device *dev,
					 struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, attr->index);
	int err;

	if (!fan_cpld->poll_interval) {
		mutex_lock(&fan_cpld->lock);
		err = fan_cpld_read_present(fan_cpld);
		mutex_unlock(&fan_cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%d\n", fan->present);
}

static ssize_t fan_cpld_fan_id_show(struct device *dev,
				    struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, attr->index);
	int err = 0;

	if (!fan_cpld->poll_interval) {
		mutex_lock(&fan_cpld->lock);
		err = fan_cpld_read_fan_id(fan_cpld, attr->index);
		mutex_unlock(&fan_cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%hhu\n", fan->ident);
}

static ssize_t fan_cpld_fan_fault_show(struct device *dev,
				       struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, attr->index);
	int err;

	if (!fan_cpld->poll_interval) {
		mutex_lock(&fan_cpld->lock);
		err = fan_cpld_read_fault(fan_cpld);
		mutex_unlock(&fan_cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%d\n", !fan->ok);
}

static ssize_t fan_cpld_fan_tach_show(struct device *dev,
				      struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	struct fan_cpld_fan_data *fan = fan_from_fan_cpld(fan_cpld, attr->index);
	int err;
	int rpms;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_read_fan_tach(fan_cpld, attr->index);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	if (!fan->tach) {
		return -EINVAL;
	}

	rpms = ((fan_cpld->info->hz * 60) / fan->tach) / fan_cpld->info->pulses;

	return sprintf(buf, "%d\n", rpms);
}

static ssize_t fan_cpld_fan_airflow_show(struct device *dev,
					 struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct fan_cpld_fan_data *fan = fan_from_dev(dev, attr->index);
	return sprintf(buf, "%s\n", (fan->reverse) ? "reverse" : "forward");
}

#define FAN_DEVICE_ATTR(_name)							\
	static SENSOR_DEVICE_ATTR(pwm##_name, S_IRUGO | S_IWGRP | S_IWUSR,	\
				fan_cpld_fan_pwm_show, fan_cpld_fan_pwm_store,	\
				_name - 1);					\
	static SENSOR_DEVICE_ATTR(fan##_name##_id, S_IRUGO,			\
				  fan_cpld_fan_id_show, NULL, _name - 1);	\
	static SENSOR_DEVICE_ATTR(fan##_name##_input, S_IRUGO,			\
				fan_cpld_fan_tach_show, NULL, _name - 1);	\
	static SENSOR_DEVICE_ATTR(fan##_name##_fault, S_IRUGO,			\
				fan_cpld_fan_fault_show, NULL, _name - 1);	\
	static SENSOR_DEVICE_ATTR(fan##_name##_present, S_IRUGO,		\
				fan_cpld_fan_present_show, NULL, _name - 1);	\
	static SENSOR_DEVICE_ATTR(fan##_name##_airflow, S_IRUGO,		\
				fan_cpld_fan_airflow_show, NULL, _name - 1);	\

#define FAN_ATTR(_name)								\
		&sensor_dev_attr_pwm##_name.dev_attr.attr,			\
		&sensor_dev_attr_fan##_name##_id.dev_attr.attr,			\
		&sensor_dev_attr_fan##_name##_input.dev_attr.attr,		\
		&sensor_dev_attr_fan##_name##_fault.dev_attr.attr,		\
		&sensor_dev_attr_fan##_name##_present.dev_attr.attr,		\
		&sensor_dev_attr_fan##_name##_airflow.dev_attr.attr

#define FAN_ATTR_GROUP(_name) &fan##_name##_attr_group

#define DEVICE_FAN_ATTR_GROUP(_name)						\
	FAN_DEVICE_ATTR(_name);							\
	static struct attribute *fan##_name##_attrs[] = { FAN_ATTR(_name),	\
							  NULL };		\
	static struct attribute_group fan##_name##_attr_group = {		\
		.attrs = fan##_name##_attrs,					\
	}

DEVICE_FAN_ATTR_GROUP(1);
DEVICE_FAN_ATTR_GROUP(2);
DEVICE_FAN_ATTR_GROUP(3);
DEVICE_FAN_ATTR_GROUP(4);
DEVICE_FAN_ATTR_GROUP(5);
DEVICE_FAN_ATTR_GROUP(6);
DEVICE_FAN_ATTR_GROUP(7);
DEVICE_FAN_ATTR_GROUP(8);

static struct attribute_group *fan_groups[] = {
	FAN_ATTR_GROUP(1), FAN_ATTR_GROUP(2), FAN_ATTR_GROUP(3),
	FAN_ATTR_GROUP(4), FAN_ATTR_GROUP(5), FAN_ATTR_GROUP(6),
	FAN_ATTR_GROUP(7), FAN_ATTR_GROUP(8), NULL,
};

static ssize_t fw_ver_show(struct device *dev,
			   struct device_attribute *attr, char *buf)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	return sprintf(buf, "%u.%u\n", fan_cpld->major, fan_cpld->minor);
}

DEVICE_ATTR(fw_ver, S_IRUGO, fw_ver_show, NULL);

static ssize_t fan_cpld_ver_show(struct device *dev,
				 struct device_attribute *attr, char *buf)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	return sprintf(buf, "%02x\n", fan_cpld->major);
}

DEVICE_ATTR(cpld_ver, S_IRUGO, fan_cpld_ver_show, NULL);

static ssize_t fan_cpld_sub_ver_show(struct device *dev,
				     struct device_attribute *attr, char *buf)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	return sprintf(buf, "%02x\n", fan_cpld->minor);
}

DEVICE_ATTR(cpld_sub_ver, S_IRUGO, fan_cpld_sub_ver_show, NULL);

static ssize_t fan_cpld_update_show(struct device *dev,
				    struct device_attribute *attr, char *buf)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	int err;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_update(fan_cpld);
	mutex_unlock(&fan_cpld->lock);

	return err;
}

DEVICE_ATTR(update, S_IRUGO, fan_cpld_update_show, NULL);


static ssize_t wdt_boost_pwm_show(struct device *dev,
				  struct device_attribute *attr, char *buf)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	int err;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_read_wdt_boost_pwm(fan_cpld);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	return sprintf(buf, "%hhu\n", fan_cpld->wdt_boost_pwm);
}

static ssize_t wdt_boost_pwm_store(struct device *dev,
				   struct device_attribute *da, const char *buf,
				   size_t count)
{
	struct fan_cpld_data *fan_cpld = dev_get_drvdata(dev);
	u8 val;
	int err;

	if (sscanf(buf, "%hhu", &val) != 1)
		return -EINVAL;

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_write_wdt_boost_pwm(fan_cpld, val);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	return count;
}

DEVICE_ATTR(wdt_boost_pwm, S_IRUGO | S_IWGRP | S_IWUSR, wdt_boost_pwm_show,
		wdt_boost_pwm_store);

static struct attribute *fan_cpld_attrs[] = {
	&dev_attr_fw_ver.attr,
	&dev_attr_cpld_ver.attr,
	&dev_attr_cpld_sub_ver.attr,
	&dev_attr_update.attr,
	&dev_attr_wdt_boost_pwm.attr,
	NULL,
};

static struct attribute_group fan_cpld_group = {
	.attrs = fan_cpld_attrs,
};

static void fan_cpld_work_start(struct fan_cpld_data *fan_cpld)
{
	if (fan_cpld->poll_interval) {
		queue_delayed_work(fan_cpld_workqueue, &fan_cpld->dwork,
				   msecs_to_jiffies(fan_cpld->poll_interval));
	}
}

static void fan_cpld_work_fn(struct work_struct *work)
{
	struct delayed_work *dwork = to_delayed_work(work);
	struct fan_cpld_data *fan_cpld = container_of(dwork, struct fan_cpld_data,
						      dwork);

	mutex_lock(&fan_cpld->lock);
	fan_cpld_update(fan_cpld);
	fan_cpld_work_start(fan_cpld);
	mutex_unlock(&fan_cpld->lock);
}

static int fan_cpld_init(struct fan_cpld_data *fan_cpld, bool safe_mode)
{
	struct fan_cpld_fan_data *fan;
	int err;
	int i;

	err = fan_cpld_read_byte(fan_cpld, MINOR_VERSION_REG, &fan_cpld->minor);
	if (err)
		return -ENODEV;

	err = fan_cpld_read_byte(fan_cpld, MAJOR_VERSION_REG, &fan_cpld->major);
	if (err)
		return err;

	dev_info(dev_from_fan_cpld(fan_cpld), "%s Fan CPLD version %02x.%02x\n",
		 fan_cpld->info->label,
		 fan_cpld->major, fan_cpld->minor);

	err = fan_cpld_read_byte(fan_cpld, FAN_PRESENT_REG, &fan_cpld->present);
	if (err)
		return err;

	err = fan_cpld_read_byte(fan_cpld, FAN_OK_REG, &fan_cpld->ok);
	if (err)
		return err;

	for (i = 0; i < fan_cpld->info->fan_count; ++i) {
		fan = fan_from_fan_cpld(fan_cpld, i);
		fan->index = i;
		fan->global_index = i + fan_cpld->info->fan_global_offset;
		fan->present = !!(fan_cpld->present & (1 << fan->index));
		fan->ok = !!(fan_cpld->ok & (1 << fan->index));
		if (fan->present) {
			fan_cpld_read_fan_id(fan_cpld, fan->index);
			fan_cpld_read_fan_tach(fan_cpld, fan->index);
			fan_cpld_read_fan_pwm(fan_cpld, fan->index);
			if (safe_mode) {
				fan_cpld_write_pwm(fan_cpld, fan->index,
						   fan_cpld->info->max_pwm);
			} else {
				fan_cpld_write_pwm(fan_cpld, fan->index,
						   fan_cpld->info->default_pwm);
			}

		}

		// Add LED even if the fan isn't currently present.
		fan_cpld->blue_led = 0;
		fan_cpld->amber_led = 0;
		err = led_init(fan->leds, fan_cpld->client, fan);
		if (err)
			return err;
	}

	fan_cpld_write_byte(fan_cpld, FAN_OK_CHNG_REG, 0xff);
	fan_cpld_write_byte(fan_cpld, FAN_ID_CHNG_REG, 0xff);
	fan_cpld_write_byte(fan_cpld, FAN_ID_CHNG_REG, 0xff);

	INIT_DELAYED_WORK(&fan_cpld->dwork, fan_cpld_work_fn);
	fan_cpld_work_start(fan_cpld);

	return err;
}

void fan_cpld_remove(struct i2c_client *client)
{
	struct fan_cpld_data *fan_cpld = i2c_get_clientdata(client);

	mutex_lock(&fan_cpld->lock);
	cancel_delayed_work_sync(&fan_cpld->dwork);
	mutex_unlock(&fan_cpld->lock);

	return;
}

int fan_cpld_probe(struct i2c_client *client,
		   const struct fan_cpld_driver_config *config)
{
	const struct i2c_device_id *id;
	struct device *dev = &client->dev;
	struct device *hwmon_dev;
	struct fan_cpld_data *fan_cpld;
	int err;
	int i;

	id = i2c_match_id(config->id_table, client);
	if (!id) {
		return -ENODEV;
	}

	if (!i2c_check_functionality(client->adapter,
					 I2C_FUNC_SMBUS_BYTE_DATA)) {
		dev_err(dev, "adapter doesn't support byte transactions\n");
		return -ENODEV;
	}

	fan_cpld = devm_kzalloc(dev, sizeof(struct fan_cpld_data), GFP_KERNEL);
	if (!fan_cpld)
		return -ENOMEM;

	i2c_set_clientdata(client, fan_cpld);
	fan_cpld->client = client;
	fan_cpld->poll_interval = config->poll_interval;

	fan_cpld->info = &config->fan_cpld_infos[id->driver_data];
	mutex_init(&fan_cpld->lock);

	fan_cpld->groups[0] = &fan_cpld_group;
	for (i = 0; i < fan_cpld->info->fan_count; ++i) {
		fan_cpld->groups[i + 1] = fan_groups[i];
	}

	mutex_lock(&fan_cpld->lock);
	err = fan_cpld_init(fan_cpld, config->safe_mode);
	mutex_unlock(&fan_cpld->lock);
	if (err)
		return err;

	hwmon_dev = devm_hwmon_device_register_with_groups(dev, client->name,
							   fan_cpld,
							   fan_cpld->groups);
	if (IS_ERR(hwmon_dev)) {
		fan_cpld_remove(client);
		return PTR_ERR(hwmon_dev);
	}

	fan_cpld->hwmon_dev = hwmon_dev;

	fan_cpld->wdd.info = config->wdt_info;
	fan_cpld->wdd.ops = config->wdt_ops;
	fan_cpld->wdd.parent = hwmon_dev;
	fan_cpld->wdd.timeout = WDT_TIMEOUT;
	fan_cpld->wdd.max_timeout = WDT_MAX_TIMEOUT;
	watchdog_init_timeout(&fan_cpld->wdd, 0, dev);

	err = devm_watchdog_register_device(dev, &fan_cpld->wdd);
	if (err) {
		dev_err(hwmon_dev, "watchdog_register_device failed, ret=%d\n", err);
		return err;
	}

	return err;
}

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Fan CPLD I2C Common Functions");
MODULE_LICENSE("GPL");
