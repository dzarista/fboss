/* Copyright (c) 2017 Arista Networks, Inc.
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
#include <linux/moduleparam.h>
#include <linux/device.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/i2c.h>
#include <linux/slab.h>
#include <linux/workqueue.h>
#include <linux/leds.h>

#define DRIVER_NAME "rook-fan-cpld"

#define LED_NAME_MAX_SZ 20
#define FAN_LED_COUNT 2
#define MAX_FAN_COUNT 8

#define MINOR_VERSION_REG 0x00
#define MAJOR_VERSION_REG 0x01
#define SCRATCHPAD_REG 0x02

#define FAN_TACH_REG_LOW(Id, Num) (0x10 * ((Num) + 1) + (Id)*2)
#define FAN_TACH_REG_HIGH(Id, Num) (0x10 * ((Num) + 1) + ((Id)*2) + 1)
#define FAN_TACH_A_REG_LOW(Id) (0x10 + ((Id)*2))
#define FAN_TACH_A_REG_HIGH(Id) (0x10 + ((Id)*2) + 1)
#define FAN_TACH_B_REG_LOW(Id) (0x20 + ((Id)*2))
#define FAN_TACH_B_REG_HIGH(Id) (0x20 + ((Id)*2) + 1)
#define FAN_PWM_REG(Id, Num) (0x30 + (Id) + ((Num)*8))
#define FAN_PWM_A_REG(Id) (0x30 + (Id))
#define FAN_PWM_B_REG(Id) (0x38 + (Id))

#define FAN_ID_REG(Id) (0x41 + (Id))
#define FAN_PRESENT_REG 0x49
#define FAN_OK_REG 0x4A

#define FAN_GREEN_LED_REG 0x4B
#define FAN_RED_LED_REG 0x4C

#define FAN_INT_REG 0x4D
#define FAN_ID_CHNG_REG 0x4E
#define FAN_PRESENT_CHNG_REG 0x4F
#define FAN_OK_CHNG_REG 0x50

#define FAN_INT_OK (1 << 0)
#define FAN_INT_PRES (1 << 1)
#define FAN_INT_ID (1 << 2)

#define FAN_LED_GREEN 1
#define FAN_LED_RED 2

#define FAN_MAX_PWM 255
#define FAN_DFT_PWM 127	/* default 50% duty cycle */

static bool safe_mode = false;
module_param(safe_mode, bool, S_IRUSR | S_IWUSR);
MODULE_PARM_DESC(safe_mode, "force fan speed to 100% during probe");

static bool managed_leds = true;
module_param(managed_leds, bool, S_IRUSR | S_IWUSR);
MODULE_PARM_DESC(managed_leds, "let the driver handle the leds");

static unsigned long poll_interval = 0;
module_param(poll_interval, ulong, S_IRUSR);
MODULE_PARM_DESC(poll_interval, "interval between two polling in ms");

static struct workqueue_struct *rook_cpld_workqueue;

enum cpld_type {
	LA_CPLD = 0,
	TEHAMA_CPLD = 1,
};

struct cpld_info {
	enum cpld_type id;
	u8 fan_count;
	u8 rotors;
	int pulses;
	int hz;
	bool swap_fan_index;
};

// these info could also be deducted from the id register
static struct cpld_info cpld_infos[] = {
   [LA_CPLD] = {
      .id = LA_CPLD,
      .fan_count = 4,
      .rotors = 1,
      .pulses = 2,
      .hz = 100000,
      .swap_fan_index = false,
   },
   [TEHAMA_CPLD] = {
      .id = TEHAMA_CPLD,
      .fan_count = 5,
      .rotors = 2,
      .pulses = 2,
      .hz = 100000,
      .swap_fan_index = true,
   },
};

struct cpld_fan_led_data {
	u8 fan_index;
        u8 reg;
	char name[LED_NAME_MAX_SZ];
	struct led_classdev cdev;
};

struct cpld_fan_data {
	bool ok;
	bool present;
	bool forward;
	u16 tach;
	u8 pwm;
	u8 ident;
	u8 index; // The fan index in the CPLD registers
	u8 slot; // The physical fan slot in the rear card
	struct cpld_fan_led_data leds[FAN_LED_COUNT];
};

struct cpld_data {
	const struct cpld_info *info;
	struct mutex lock;
	struct i2c_client *client;
	struct device *hwmon_dev;
	struct delayed_work dwork;
	struct cpld_fan_data fans[MAX_FAN_COUNT];

	const struct attribute_group *groups[1 + MAX_FAN_COUNT + 1];

	u8 minor;
	u8 major;

	u8 present;
	u8 ok;

	u8 green_led;
	u8 red_led;
};

static struct cpld_fan_data *fan_from_cpld(struct cpld_data *cpld, u8 fan_slot)
{
	return &cpld->fans[fan_slot];
}

static struct cpld_fan_data *fan_from_dev(struct device *dev, u8 fan_slot)
{
	struct cpld_data *cpld = dev_get_drvdata(dev);
	return fan_from_cpld(cpld, fan_slot);
}

static struct device *dev_from_cpld(struct cpld_data *cpld)
{
	return &cpld->client->dev;
}

static struct cpld_fan_led_data *led_from_fan(struct cpld_fan_data *fan, u8 led_id)
{
	return &fan->leds[led_id];
}

static struct cpld_fan_led_data *led_from_cpld(struct cpld_data *cpld,
					       u8 fan_slot, u8 led_id)
{
	struct cpld_fan_data *fan = fan_from_cpld(cpld, fan_slot);
	return led_from_fan(fan, led_id);
}

static s32 cpld_read_byte(struct cpld_data *cpld, u8 reg, u8 *res)
{
	int err;

	err = i2c_smbus_read_byte_data(cpld->client, reg);
	if (err < 0) {
		dev_err(&cpld->client->dev,
			"failed to read reg 0x%02x error=%d\n", reg, err);
		return err;
	}

	*res = (err & 0xff);
	return 0;
}

static s32 cpld_write_byte(struct cpld_data *cpld, u8 reg, u8 byte)
{
	int err;

	err = i2c_smbus_write_byte_data(cpld->client, reg, byte);
	if (err) {
		dev_err(&cpld->client->dev,
			"failed to write 0x%02x in reg 0x%02x error=%d\n", byte,
			reg, err);
	}

	return err;
}

static void cpld_work_start(struct cpld_data *cpld)
{
	if (poll_interval) {
		queue_delayed_work(rook_cpld_workqueue, &cpld->dwork,
				   msecs_to_jiffies(poll_interval));
	}
}

static s32 cpld_read_fan_id(struct cpld_data *cpld, u8 fan_slot)
{
	struct cpld_fan_data *fan = fan_from_cpld(cpld, fan_slot);
	s32 err;
	u8 tmp;

	err = cpld_read_byte(cpld, FAN_ID_REG(fan->index), &tmp);
	if (err)
		return err;

	fan->ident = tmp & 0xf;
	fan->forward = (tmp >> 4) & 0x1;

	return 0;
}

static int cpld_update_leds(struct cpld_data *cpld)
{
	struct cpld_fan_data *fan;
	int err;
	int i;

	cpld->green_led = 0;
	cpld->red_led = 0;

	for (i = 0; i < cpld->info->fan_count; ++i) {
		fan = fan_from_cpld(cpld, i);
		if (fan->ok && fan->present)
			cpld->green_led |= (1 << fan->index);
		else
			cpld->red_led |= (1 << fan->index);
	}

	err = cpld_write_byte(cpld, FAN_GREEN_LED_REG, ~cpld->green_led);
	if (err)
		return err;

	err = cpld_write_byte(cpld, FAN_RED_LED_REG, ~cpld->red_led);
	if (err)
		return err;

	return 0;
}

static int cpld_update(struct cpld_data *cpld)
{
	struct device *dev = dev_from_cpld(cpld);
	struct cpld_fan_data *fan;
	const char *str;
	int fans_connected = 0;
	int err;
	int i;
	u8 interrupt, id_chng, ok_chng, pres_chng;

	dev_dbg(dev, "polling cpld information\n");

	err = cpld_read_byte(cpld, FAN_INT_REG, &interrupt);
	if (err)
		goto fail;

	if (interrupt & FAN_INT_ID) {
		err = cpld_read_byte(cpld, FAN_ID_CHNG_REG, &id_chng);
		if (err)
			goto fail;
	}

	if (interrupt & FAN_INT_OK) {
		err = cpld_read_byte(cpld, FAN_OK_CHNG_REG, &ok_chng);
		if (err)
			goto fail;
		err = cpld_read_byte(cpld, FAN_OK_REG, &cpld->ok);
		if (err)
			goto fail;
	}

	if (interrupt & FAN_INT_PRES) {
		err = cpld_read_byte(cpld, FAN_PRESENT_CHNG_REG, &pres_chng);
		if (err)
			goto fail;
		err = cpld_read_byte(cpld, FAN_OK_REG, &cpld->present);
		if (err)
			goto fail;
	}

	for (i = 0; i < cpld->info->fan_count; ++i) {
		fan = fan_from_cpld(cpld, i);

		if ((interrupt & FAN_INT_PRES) && (pres_chng & (1 << fan->index))) {
			if (fan->present && (cpld->present & (1 << fan->index))) {
				str = "hotswapped";
			} else if (!fan->present &&
				   (cpld->present & (1 << fan->index))) {
				str = "plugged";
				fan->present = true;
			} else {
				str = "unplugged";
				fan->present = false;
			}
			dev_info(dev, "fan %d was %s\n", fan->slot + 1, str);
		}

		if ((interrupt & FAN_INT_OK) && (ok_chng & (1 << fan->index))) {
			if (fan->ok && (cpld->ok & (1 << fan->index))) {
				dev_warn(dev, "fan %d had a small snag\n",
					 fan->slot + 1);
			} else if (fan->ok && !(cpld->ok & (1 << fan->index))) {
				dev_warn(dev,
					 "fan %d is in fault, likely stuck\n",
					 fan->slot + 1);
				fan->ok = false;
			} else {
				dev_info(
					dev,
					"fan %d has recovered a running state\n",
					fan->slot + 1);
				fan->ok = true;
			}
		}

		if ((interrupt & FAN_INT_ID) && (id_chng & (1 << fan->index))) {
			dev_info(dev, "fan %d kind has changed\n", fan->slot + 1);
			cpld_read_fan_id(cpld, fan->slot);
		}

		if (fan->present)
			fans_connected += 1;
	}

	if (cpld->info->fan_count - fans_connected > 1) {
		dev_warn(dev,
			 "it is not recommended to have more than one fan "
			 "unplugged. (%d/%d connected)\n",
			 fans_connected, cpld->info->fan_count);
	}

	cpld_write_byte(cpld, FAN_ID_CHNG_REG, id_chng);
	cpld_write_byte(cpld, FAN_OK_CHNG_REG, ok_chng);
	cpld_write_byte(cpld, FAN_PRESENT_CHNG_REG, pres_chng);

	if (managed_leds)
		err = cpld_update_leds(cpld);

fail:
	return err;
}

static s32 cpld_write_pwm(struct cpld_data *cpld, u8 fan_slot, u8 pwm)
{
	struct cpld_fan_data *fan = fan_from_cpld(cpld, fan_slot);
	int err = 0;
	int i;

	for (i = 0; i < cpld->info->rotors; i++) {
		err = cpld_write_byte(cpld, FAN_PWM_REG(fan->index, i), pwm);
		if (err)
			return err;

		fan->pwm = pwm;
	}

	return err;
}

static int cpld_read_present(struct cpld_data *cpld)
{
	struct cpld_fan_data *fan;
	int err;
	int i;

	err = cpld_read_byte(cpld, FAN_PRESENT_REG, &cpld->present);
	if (err)
		return err;

	for (i = 0; i < cpld->info->fan_count; ++i) {
		fan = fan_from_cpld(cpld, i);
		fan->present = !!(cpld->present & (1 << fan->index));
	}

	return 0;
}

static int cpld_read_fault(struct cpld_data *cpld)
{
	struct cpld_fan_data *fan;
	int err;
	int i;

	err = cpld_read_byte(cpld, FAN_OK_REG, &cpld->ok);
	if (err)
		return err;

	for (i = 0; i < cpld->info->fan_count; ++i) {
		fan = fan_from_cpld(cpld, i);
		fan->ok = !!(cpld->ok & (1 << fan->index));
	}

	return 0;
}

static s32 cpld_read_tach_single(struct cpld_data *cpld, u8 fan_index,
				 u8 rotor_num, u16 *tach)
{
	int err;
	u8 low;
	u8 high;

	err = cpld_read_byte(cpld, FAN_TACH_REG_LOW(fan_index, rotor_num), &low);
	if (err)
		return err;

	err = cpld_read_byte(cpld, FAN_TACH_REG_HIGH(fan_index, rotor_num), &high);
	if (err)
		return err;

	*tach = ((u16)high << 8) | low;

	return 0;
}

static s32 cpld_read_fan_tach(struct cpld_data *cpld, u8 fan_slot)
{
	struct cpld_fan_data *fan = fan_from_cpld(cpld, fan_slot);
	s32 err = 0;
	u16 tach;
	int i;

        fan->tach = 0;
	for (i = 0; i < cpld->info->rotors; i++) {
		err = cpld_read_tach_single(cpld, fan->index, i, &tach);
		if (err)
			break;
		fan->tach += tach;

		dev_dbg(dev_from_cpld(cpld), "fan%d/%d tach=0x%04x\n",
			fan->slot + 1, i + 1, fan->tach);
		if (fan->tach == 0xffff) {
			cpld_read_present(cpld);
			cpld_read_fault(cpld);
			if (managed_leds)
				cpld_update_leds(cpld);

			if (!fan->present)
				return -ENODEV;

			dev_warn(
				dev_from_cpld(cpld),
				"Invalid tach information read from fan %d, this is likely "
				"a hardware issue (stuck fan or broken register)\n",
				fan->slot + 1);

			return -EIO;
		}
	}

	fan->tach = fan->tach / cpld->info->rotors;

	return err;
}

static s32 cpld_read_pwm_single(struct cpld_data *cpld, u8 fan_index,
				u8 rotor_num, u8 *pwm)
{
	return cpld_read_byte(cpld, FAN_PWM_REG(fan_index, rotor_num), pwm);
}

static s32 cpld_read_fan_pwm(struct cpld_data *cpld, u8 fan_slot)
{
	struct cpld_fan_data *fan = fan_from_cpld(cpld, fan_slot);
	int err;
	u8 pwm_outer;

	err = cpld_read_pwm_single(cpld, fan->index, 0, &pwm_outer);
	if (err)
		return err;

	// some fans have two rotors but we only fetch the 1st one
	fan->pwm = pwm_outer;

	return 0;
}

static s32 cpld_read_fan_led(struct cpld_data *data,
			     struct cpld_fan_led_data *led, u8 *val)
{
	if (led->reg == FAN_GREEN_LED_REG)
		*val = (data->green_led >> led->fan_index) & 1;
	else
		*val = (data->red_led >> led->fan_index) & 1;

	return 0;
}

static s32 cpld_write_fan_led(struct cpld_data *cpld,
			      struct cpld_fan_led_data *led, u8 val)
{
	u8 *reg_val;
	int err = 0;

	if (val > 1)
		return -EINVAL;

	if (led->reg == FAN_GREEN_LED_REG)
		reg_val = &cpld->green_led;
	else
		reg_val = &cpld->red_led;

	if (val)
		*reg_val |= (1 << led->fan_index);
	else
		*reg_val &= ~(1 << led->fan_index);

	err = cpld_write_byte(cpld, led->reg, ~*reg_val);
	return err;
}

static void brightness_set(struct led_classdev *led_cdev,
			   enum led_brightness val)
{
	struct cpld_fan_led_data *led =
		container_of(led_cdev, struct cpld_fan_led_data, cdev);
	struct cpld_data *data = dev_get_drvdata(led_cdev->dev->parent);

	cpld_write_fan_led(data, led, val);
}

static enum led_brightness brightness_get(struct led_classdev *led_cdev)
{
	struct cpld_fan_led_data *led =
		container_of(led_cdev, struct cpld_fan_led_data, cdev);
	struct cpld_data *data = dev_get_drvdata(led_cdev->dev->parent);
	int err;
	u8 val;

	err = cpld_read_fan_led(data, led, &val);
	if (err)
		return 0;

	return val;
}

static int led_init(struct cpld_fan_led_data *led,
		    struct i2c_client *client, struct cpld_fan_data *fan,
                    u8 led_index)
{
	char *color;

	if (led_index + 1 == FAN_LED_GREEN) {
		color = "green";
                led->reg = FAN_GREEN_LED_REG;
	} else if (led_index + 1 == FAN_LED_RED) {
		color = "red";
                led->reg = FAN_RED_LED_REG;
	} else {
		return -EINVAL;
	}

	scnprintf(led->name, LED_NAME_MAX_SZ, "fan%d:%s:status",
		  fan->slot + 1, color);
	led->fan_index = fan->index;
	led->cdev.name = led->name;
	led->cdev.brightness_set = brightness_set;
	led->cdev.brightness_get = brightness_get;

	return devm_led_classdev_register(&client->dev, &led->cdev);
}

static ssize_t cpld_fan_pwm_show(struct device *dev,
				 struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	struct cpld_fan_data *fan = fan_from_cpld(cpld, attr->index);
	int err;

	mutex_lock(&cpld->lock);
	err = cpld_read_fan_pwm(cpld, attr->index);
	mutex_unlock(&cpld->lock);
	if (err)
		return err;

	return sprintf(buf, "%hhu\n", fan->pwm);
}

static ssize_t cpld_fan_pwm_store(struct device *dev,
				  struct device_attribute *da, const char *buf,
				  size_t count)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	u8 val;
	int err;

	if (sscanf(buf, "%hhu", &val) != 1)
		return -EINVAL;

	mutex_lock(&cpld->lock);
	err = cpld_write_pwm(cpld, attr->index, val);
	mutex_unlock(&cpld->lock);
	if (err)
		return err;

	return count;
}

static ssize_t cpld_fan_present_show(struct device *dev,
				     struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	struct cpld_fan_data *fan = fan_from_cpld(cpld, attr->index);
	int err;

	if (!poll_interval) {
		mutex_lock(&cpld->lock);
		err = cpld_read_present(cpld);
		mutex_unlock(&cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%d\n", fan->present);
}

static ssize_t cpld_fan_id_show(struct device *dev, struct device_attribute *da,
				char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	struct cpld_fan_data *fan = fan_from_cpld(cpld, attr->index);
	int err = 0;

	if (!poll_interval) {
		mutex_lock(&cpld->lock);
		err = cpld_read_fan_id(cpld, attr->index);
		mutex_unlock(&cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%hhu\n", fan->ident);
}

static ssize_t cpld_fan_fault_show(struct device *dev,
				   struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	struct cpld_fan_data *fan = fan_from_cpld(cpld, attr->index);
	int err;

	if (!poll_interval) {
		mutex_lock(&cpld->lock);
		err = cpld_read_fault(cpld);
		mutex_unlock(&cpld->lock);
		if (err)
			return err;
	}

	return sprintf(buf, "%d\n", !fan->ok);
}

static ssize_t cpld_fan_tach_show(struct device *dev,
				  struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
	struct cpld_fan_data *fan = fan_from_cpld(cpld, attr->index);
	int err;
	int rpms;

	mutex_lock(&cpld->lock);
	err = cpld_read_fan_tach(cpld, attr->index);
	mutex_unlock(&cpld->lock);
	if (err)
		return err;

	if (!fan->tach) {
		return -EINVAL;
	}

	rpms = ((cpld->info->hz * 60) / fan->tach) / cpld->info->pulses;

	return sprintf(buf, "%d\n", rpms);
}

static ssize_t cpld_fan_led_show(struct device *dev,
				 struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
        struct cpld_fan_led_data *led;
        u8 val_tmp;
	u8 val = 0;
	int led_id;
	int err;

	for (led_id = 0; led_id < FAN_LED_COUNT; led_id++) {
		led = led_from_cpld(cpld, attr->index, led_id);
		err = cpld_read_fan_led(cpld, led, &val_tmp);
		if (err)
			return err;
		if (val_tmp)
			val += (val_tmp << led_id);
	}
	return sprintf(buf, "%hhu\n", val);
}

static ssize_t cpld_fan_led_store(struct device *dev,
				  struct device_attribute *da, const char *buf,
				  size_t count)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_data *cpld = dev_get_drvdata(dev);
        struct cpld_fan_led_data *led;
	u8 val;
	int led_id;
	int err;

	if (managed_leds)
		return -EPERM;

	if (sscanf(buf, "%hhu", &val) != 1)
		return -EINVAL;

	if (val > 3)
		return -EINVAL;

	for (led_id = 0; led_id < FAN_LED_COUNT; led_id++) {
		led = led_from_cpld(cpld, attr->index, led_id);
		mutex_lock(&cpld->lock);
		err = cpld_write_fan_led(cpld, led, (val >> led_id) & 1);
		mutex_unlock(&cpld->lock);
		if (err)
			return err;
	}

	return count;
}

static ssize_t cpld_fan_airflow_show(struct device *dev,
				     struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct cpld_fan_data *fan = fan_from_dev(dev, attr->index);
	return sprintf(buf, "%s\n", (fan->forward) ? "forward" : "reverse");
}

#define FAN_DEVICE_ATTR(_name)                                                 \
	static SENSOR_DEVICE_ATTR(pwm##_name, S_IRUGO | S_IWGRP | S_IWUSR,     \
				  cpld_fan_pwm_show, cpld_fan_pwm_store,       \
				  _name - 1);                                  \
	static SENSOR_DEVICE_ATTR(fan##_name##_id, S_IRUGO, cpld_fan_id_show,  \
				  NULL, _name - 1);                            \
	static SENSOR_DEVICE_ATTR(fan##_name##_input, S_IRUGO,                 \
				  cpld_fan_tach_show, NULL, _name - 1);        \
	static SENSOR_DEVICE_ATTR(fan##_name##_fault, S_IRUGO,                 \
				  cpld_fan_fault_show, NULL, _name - 1);       \
	static SENSOR_DEVICE_ATTR(fan##_name##_present, S_IRUGO,               \
				  cpld_fan_present_show, NULL, _name - 1);     \
	static SENSOR_DEVICE_ATTR(fan##_name##_led,                            \
				  S_IRUGO | S_IWGRP | S_IWUSR,                 \
				  cpld_fan_led_show, cpld_fan_led_store,       \
				  _name - 1);                                  \
	static SENSOR_DEVICE_ATTR(fan##_name##_airflow, S_IRUGO,               \
				  cpld_fan_airflow_show, NULL, _name - 1);

#define FAN_ATTR(_name)                                                        \
	&sensor_dev_attr_pwm##_name.dev_attr.attr,                             \
		&sensor_dev_attr_fan##_name##_id.dev_attr.attr,                \
		&sensor_dev_attr_fan##_name##_input.dev_attr.attr,             \
		&sensor_dev_attr_fan##_name##_fault.dev_attr.attr,             \
		&sensor_dev_attr_fan##_name##_present.dev_attr.attr,           \
		&sensor_dev_attr_fan##_name##_led.dev_attr.attr,               \
		&sensor_dev_attr_fan##_name##_airflow.dev_attr.attr

#define FAN_ATTR_GROUP(_name) &fan##_name##_attr_group

#define DEVICE_FAN_ATTR_GROUP(_name)                                           \
	FAN_DEVICE_ATTR(_name);                                                \
	static struct attribute *fan##_name##_attrs[] = { FAN_ATTR(_name),     \
							  NULL };              \
	static struct attribute_group fan##_name##_attr_group = {              \
		.attrs = fan##_name##_attrs,                                   \
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

static ssize_t cpld_ver_show(struct device *dev,
			     struct device_attribute *attr, char *buf)
{
	struct cpld_data *cpld = dev_get_drvdata(dev);
	return sprintf(buf, "%02x\n", cpld->major);
}

DEVICE_ATTR(cpld_ver, S_IRUGO, cpld_ver_show, NULL);

static ssize_t cpld_sub_ver_show(struct device *dev,
				 struct device_attribute *attr, char *buf)
{
	struct cpld_data *cpld = dev_get_drvdata(dev);
	return sprintf(buf, "%02x\n", cpld->minor);
}

DEVICE_ATTR(cpld_sub_ver, S_IRUGO, cpld_sub_ver_show, NULL);

static ssize_t cpld_update_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	struct cpld_data *cpld = dev_get_drvdata(dev);
	int err;

	mutex_lock(&cpld->lock);
	err = cpld_update(cpld);
	mutex_unlock(&cpld->lock);

	return err;
}

DEVICE_ATTR(update, S_IRUGO, cpld_update_show, NULL);

static struct attribute *cpld_attrs[] = {
	&dev_attr_cpld_ver.attr,
	&dev_attr_cpld_sub_ver.attr,
	&dev_attr_update.attr,
	NULL,
};

static struct attribute_group cpld_group = {
	.attrs = cpld_attrs,
};

static void cpld_work_fn(struct work_struct *work)
{
	struct delayed_work *dwork = to_delayed_work(work);
	struct cpld_data *cpld = container_of(dwork, struct cpld_data, dwork);

	mutex_lock(&cpld->lock);
	cpld_update(cpld);
	cpld_work_start(cpld);
	mutex_unlock(&cpld->lock);
}

static int cpld_init(struct cpld_data *cpld)
{
	struct cpld_fan_data *fan;
	struct cpld_fan_led_data *led;
	int err;
	int i;
        int j;

	err = cpld_read_byte(cpld, MINOR_VERSION_REG, &cpld->minor);
	if (err)
		return -ENODEV;

	err = cpld_read_byte(cpld, MAJOR_VERSION_REG, &cpld->major);
	if (err)
		return err;

	dev_info(dev_from_cpld(cpld), "rook CPLD version %02x.%02x\n",
		 cpld->major, cpld->minor);

	err = cpld_read_byte(cpld, FAN_PRESENT_REG, &cpld->present);
	if (err)
		return err;

	err = cpld_read_byte(cpld, FAN_OK_REG, &cpld->ok);
	if (err)
		return err;

	for (i = 0; i < cpld->info->fan_count; ++i) {
		fan = fan_from_cpld(cpld, i);

		fan->slot = i;

		if (cpld->info->swap_fan_index)
			// CPLD fan indices don't match the physical fan slots,
			// so swap fan index if needed.
			fan->index = (cpld->info->fan_count - 1) - fan->slot;
		else
			fan->index = fan->slot;

		fan->present = !!(cpld->present & (1 << fan->index));
		fan->ok = !!(cpld->ok & (1 << fan->index));
		if (fan->present) {
			cpld_read_fan_id(cpld, fan->slot);
			cpld_read_fan_tach(cpld, fan->slot);
			cpld_read_fan_pwm(cpld, fan->slot);
			if (safe_mode)
				cpld_write_pwm(cpld, fan->slot, FAN_MAX_PWM);
			else
				cpld_write_pwm(cpld, fan->slot, FAN_DFT_PWM);

			// Add red/green LEDs
			for (j = 0; j < FAN_LED_COUNT; j++) {
				led = led_from_fan(fan, j);
				err = led_init(led, cpld->client, fan, j);
				if (err)
					return err;
			}
		}
	}

	cpld_write_byte(cpld, FAN_OK_CHNG_REG, 0xff);
	cpld_write_byte(cpld, FAN_ID_CHNG_REG, 0xff);
	cpld_write_byte(cpld, FAN_ID_CHNG_REG, 0xff);

	if (managed_leds) {
		err = cpld_update_leds(cpld);
		if (err)
			return err;
	}

	INIT_DELAYED_WORK(&cpld->dwork, cpld_work_fn);
	cpld_work_start(cpld);

	return err;
}

static const struct i2c_device_id cpld_id[] = {
	{ "la_cpld", LA_CPLD },
	{ "tehama_cpld", TEHAMA_CPLD },
	{}
};
MODULE_DEVICE_TABLE(i2c, cpld_id);


static void cpld_remove(struct i2c_client *client)
{
	struct cpld_data *cpld = i2c_get_clientdata(client);

	mutex_lock(&cpld->lock);
	cancel_delayed_work_sync(&cpld->dwork);
	mutex_unlock(&cpld->lock);
}

static int cpld_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct device *hwmon_dev;
	struct cpld_data *cpld;
	int err;
	int i, cid;

	if (!i2c_check_functionality(client->adapter,
				     I2C_FUNC_SMBUS_BYTE_DATA)) {
		dev_err(dev, "adapter doesn't support byte transactions\n");
		return -ENODEV;
	}

	cpld = devm_kzalloc(dev, sizeof(struct cpld_data), GFP_KERNEL);
	if (!cpld)
		return -ENOMEM;

	i2c_set_clientdata(client, cpld);
	cpld->client = client;

	cid = i2c_match_id(cpld_id, client)->driver_data;
	cpld->info = &cpld_infos[cid];
	mutex_init(&cpld->lock);

	cpld->groups[0] = &cpld_group;
	for (i = 0; i < cpld->info->fan_count; ++i) {
		cpld->groups[i + 1] = fan_groups[i];
	}

	mutex_lock(&cpld->lock);
	err = cpld_init(cpld);
	mutex_unlock(&cpld->lock);
	if (err)
		return err;

	hwmon_dev = devm_hwmon_device_register_with_groups(dev, client->name,
							   cpld, cpld->groups);
	if (IS_ERR(hwmon_dev)) {
		cpld_remove(client);
		return PTR_ERR(hwmon_dev);
	}

	cpld->hwmon_dev = hwmon_dev;

	return err;
}

static struct i2c_driver cpld_driver = {
   .class = I2C_CLASS_HWMON,
   .driver = {
      .name = DRIVER_NAME,
   },
   .id_table = cpld_id,
   .probe = cpld_probe,
   .remove = cpld_remove,
};

static int __init rook_cpld_init(void)
{
	int err;

	rook_cpld_workqueue = create_singlethread_workqueue(DRIVER_NAME);
	if (IS_ERR_OR_NULL(rook_cpld_workqueue)) {
		pr_err("failed to initialize workqueue\n");
		return PTR_ERR(rook_cpld_workqueue);
	}

	err = i2c_add_driver(&cpld_driver);
	if (err < 0) {
		destroy_workqueue(rook_cpld_workqueue);
		rook_cpld_workqueue = NULL;
		return err;
	}

	return 0;
}

static void __exit rook_cpld_exit(void)
{
	i2c_del_driver(&cpld_driver);
	destroy_workqueue(rook_cpld_workqueue);
	rook_cpld_workqueue = NULL;
}

module_init(rook_cpld_init);
module_exit(rook_cpld_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Rook fan cpld");
