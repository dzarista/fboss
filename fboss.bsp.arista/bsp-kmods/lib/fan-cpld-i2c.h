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
 *
 */

#ifndef _FAN_CPLD_I2C_H_
#define _FAN_CPLD_I2C_H_

#include <linux/device.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/i2c.h>
#include <linux/leds.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/slab.h>
#include <linux/watchdog.h>
#include <linux/workqueue.h>

#define LED_NAME_MAX_SZ 30
#define FAN_LED_COUNT 2
#define MAX_FAN_COUNT 8

/* Common fan CPLD register definitions */
#define MINOR_VERSION_REG 0x00
#define MAJOR_VERSION_REG 0x01
#define SCRATCHPAD_REG 0x02

#define WDT_ENABLE 0x06
#define WDT_BOOST_PWM 0x07
#define WDT_COUNTER 0x08
#define WDT_TIMEOUT 0x0c // Multiples of 5 seconds
#define WDT_MAX_TIMEOUT 0xff

#define FAN_PWM_REG(Id) (0x10 * ((Id) + 1))
#define FAN_TACH_REG_LOW(Id, Num) (0x10 * ((Id) + 1) + ((Num) * 2) + 1)
#define FAN_TACH_REG_HIGH(Id, Num) (0x10 * ((Id) + 1) + ((Num) * 2) + 2)

#define FAN_INT_OK (1 << 0)
#define FAN_INT_PRES (1 << 1)
#define FAN_INT_ID (1 << 2)

/* Common fan CPLD data structures */
struct fan_cpld_reg_info {
	u8 id_reg_base;
	u8 present_reg;
	u8 ok_reg;
	u8 blue_led_reg;
	u8 amber_led_reg;
	u8 int_reg;
	u8 id_change_reg;
	u8 present_change_reg;
	u8 ok_change_reg;
	u8 change_reg_clear_val;
};

struct fan_cpld_info {
	char *label;
	const struct fan_cpld_reg_info *regs;
	u8 fan_count;
	u8 rotors;
	int pulses;
	int hz;
	int fan_global_offset;
	u8 default_pwm;
	u8 max_pwm;
};

struct fan_cpld_driver_config {
	const struct fan_cpld_info *fan_cpld_infos;
	size_t num_cpld_types;
	const struct i2c_device_id *id_table;
	const struct watchdog_info *wdt_info;
	const struct watchdog_ops *wdt_ops;
	bool safe_mode;
	unsigned long poll_interval;
};

struct fan_cpld_fan_led_data {
	u8 fan_index;
	char name[LED_NAME_MAX_SZ];
	struct led_classdev cdev;
	char color[LED_NAME_MAX_SZ];
};

struct fan_cpld_fan_data {
	bool ok;
	bool present;
	bool reverse;
	u16 tach;
	u8 pwm;
	u8 ident;
	u8 index; /* index relative to this CPLD */
	u8 global_index; /* index relative to all CPLDs */
	struct fan_cpld_fan_led_data leds[FAN_LED_COUNT];
};

struct fan_cpld_data {
	const struct fan_cpld_info *info;
	struct mutex lock;
	struct i2c_client *client;
	struct device *hwmon_dev;
	struct delayed_work dwork;
	struct fan_cpld_fan_data fans[MAX_FAN_COUNT];
	struct watchdog_device wdd;

	const struct attribute_group *groups[1 + MAX_FAN_COUNT + 1];

	u8 minor;
	u8 major;

	u8 present;
	u8 ok;

	u8 blue_led;
	u8 amber_led;

	u8 wdt_boost_pwm;
	unsigned long poll_interval;
};

/* Public functions used by macros */
int fan_cpld_workqueue_init(const char *name);
void fan_cpld_workqueue_cleanup(void);
int fan_wdt_start(struct watchdog_device *wdd);
int fan_wdt_stop(struct watchdog_device *wdd);
int fan_wdt_ping(struct watchdog_device *wdd);
void fan_cpld_remove(struct i2c_client *client);
int fan_cpld_probe(struct i2c_client *client,
		   struct fan_cpld_driver_config *config);

/* Macro for defining module parameters */
#define FAN_CPLD_MODULE_PARAMS()						\
static bool safe_mode;								\
module_param(safe_mode, bool, S_IRUSR | S_IWUSR);				\
MODULE_PARM_DESC(safe_mode, "force fan speed to 100% during probe");		\
										\
static unsigned long poll_interval;						\
module_param(poll_interval, ulong, S_IRUSR);					\
MODULE_PARM_DESC(poll_interval, "interval between two polling in ms");

/* Macro for defining WDT ops and info */
#define FAN_CPLD_WATCHDOG_OPS_AND_INFO()					\
static const struct watchdog_ops fan_wdt_ops = {				\
	.start = fan_wdt_start,							\
	.stop = fan_wdt_stop,							\
	.ping = fan_wdt_ping,							\
	.owner = THIS_MODULE,							\
};										\
										\
static const struct watchdog_info fan_wdt_info = {				\
	.options = WDIOF_KEEPALIVEPING | WDIOF_MAGICCLOSE | WDIOF_SETTIMEOUT,	\
	.identity = KBUILD_MODNAME,						\
};

/* Macro for defining a fan CPLD driver */
#define FAN_CPLD_DRIVER(_driver_name, _driver_prefix, _cpld_infos, _id_table)	\
FAN_CPLD_MODULE_PARAMS()							\
										\
FAN_CPLD_WATCHDOG_OPS_AND_INFO()						\
										\
static struct fan_cpld_driver_config _driver_prefix##_config = {		\
	.fan_cpld_infos = _cpld_infos,						\
	.num_cpld_types = ARRAY_SIZE(_cpld_infos),				\
	.id_table = _id_table,							\
};										\
										\
static int _driver_prefix##_probe(struct i2c_client *client)			\
{										\
	/* Add macro-provided module-level params */				\
	_driver_prefix##_config.safe_mode = safe_mode;				\
	_driver_prefix##_config.poll_interval = poll_interval;			\
	_driver_prefix##_config.wdt_info = &fan_wdt_info;			\
	_driver_prefix##_config.wdt_ops = &fan_wdt_ops;				\
										\
	return fan_cpld_probe(client, &_driver_prefix##_config);		\
}										\
										\
static struct i2c_driver _driver_prefix##_driver = {				\
	.class = I2C_CLASS_HWMON,						\
	.driver = { .name = _driver_name },					\
	.id_table = _id_table,							\
	.probe = _driver_prefix##_probe,					\
	.remove = fan_cpld_remove,						\
};										\
										\
static int __init _driver_prefix##_init(void)					\
{										\
	int err;								\
										\
	err = fan_cpld_workqueue_init(_driver_name);				\
	if (err)								\
		return err;							\
										\
	err = i2c_add_driver(&_driver_prefix##_driver);				\
	if (err < 0)								\
		fan_cpld_workqueue_cleanup();					\
										\
	return err;								\
}										\
module_init(_driver_prefix##_init);						\
										\
static void __exit _driver_prefix##_exit(void)					\
{										\
	i2c_del_driver(&_driver_prefix##_driver);				\
	fan_cpld_workqueue_cleanup();						\
}										\
module_exit(_driver_prefix##_exit);

#endif /* _FAN_CPLD_I2C_H_ */
