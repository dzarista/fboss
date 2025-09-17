// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Hardware monitoring driver for UCD90xxx Sequencer and System Health
 * Controller series
 *
 * Copyright (C) 2011 Ericsson AB.
 */

#include <linux/debugfs.h>
#include <linux/delay.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/init.h>
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/i2c.h>
#include <linux/pmbus.h>
#include <linux/gpio/driver.h>
#include <linux/timekeeping.h>
#include <linux/ktime.h>
#include <linux/time64.h>
#include <linux/rtc.h>
#include <linux/list.h>
#include <linux/workqueue.h>
#include "pmbus.h"
#include "aucd9000-reload-cause.h"
#include "aucd9000-darwin-reload-cause.h"
#include "aucd9000-meru800bfa-reload-cause.h"

enum chips { ucd9000, ucd90120, ucd90124, ucd90160, ucd90320, ucd9090,
	     ucd90910 };

#define UCD9000_MONITOR_CONFIG		0xd5
#define UCD9000_NUM_PAGES		0xd6
#define UCD9000_RTC_SET		0xd7
#define UCD9000_FAN_CONFIG_INDEX	0xe7
#define UCD9000_FAN_CONFIG		0xe8
#define UCD9000_LOGGED_FAULTS	0xea
#define UCD9000_LOGGED_FAULT_DETAIL_INDEX	0xeb
#define UCD9000_LOGGED_FAULT_DETAIL		0xec
#define UCD9000_MFR_STATUS		0xf3
#define UCD9000_GPIO_SELECT		0xfa
#define UCD9000_GPIO_CONFIG		0xfb
#define UCD9000_DEVICE_ID		0xfd

/* GPIO CONFIG bits */
#define UCD9000_GPIO_CONFIG_ENABLE	BIT(0)
#define UCD9000_GPIO_CONFIG_OUT_ENABLE	BIT(1)
#define UCD9000_GPIO_CONFIG_OUT_VALUE	BIT(2)
#define UCD9000_GPIO_CONFIG_STATUS	BIT(3)
#define UCD9000_GPIO_INPUT		0
#define UCD9000_GPIO_OUTPUT		1

#define UCD9000_MON_TYPE(x)	(((x) >> 5) & 0x07)
#define UCD9000_MON_PAGE(x)	((x) & 0x1f)

#define UCD9000_MON_VOLTAGE	1
#define UCD9000_MON_TEMPERATURE	2
#define UCD9000_MON_CURRENT	3
#define UCD9000_MON_VOLTAGE_HW	4

#define UCD9000_NUM_FAN		4

#define UCD9000_GPIO_NAME_LEN	16
#define UCD9090_NUM_GPIOS	23
#define UCD901XX_NUM_GPIOS	26
#define UCD90320_NUM_GPIOS	84
#define UCD90910_NUM_GPIOS	26

#define UCD9000_DEBUGFS_NAME_LEN	24
#define UCD9000_GPI_COUNT		8
#define UCD90320_GPI_COUNT		32

#define UCD9000_RTC_SET_LEN	8
#define UCD9000_RTC_UPDATE_INTERVAL_MSECS	(10 * 60 * 1000) // 10 minutes
#define SECS_PER_DAY		86400
#define MSECS_PER_DAY		(SECS_PER_DAY * 1000)

#define UCD9000_LOGGED_FAULTS_NOT_EMPTY_BIT	1

#define UCD9000_LOGGED_FAULTS_BYTE_COUNT	12
#define UCD9012X_LOGGED_FAULTS_BYTE_COUNT	13
#define UCD90320_LOGGED_FAULTS_BYTE_COUNT	32
#define UCD90160_LOGGED_FAULTS_BYTE_COUNT	18
#define UCD90910_LOGGED_FAULTS_BYTE_COUNT	14

#define UCD9000_FAULT_DETAIL_BYTE_COUNT	10
#define UCD90320_FAULT_DETAIL_BYTE_COUNT	12
enum {
	FAULT_DETAIL_BYTE_MSEC0,
	FAULT_DETAIL_BYTE_MSEC1,
	FAULT_DETAIL_BYTE_MSEC2,
	FAULT_DETAIL_BYTE_MSEC3,
	FAULT_DETAIL_BYTE_FID0,
	FAULT_DETAIL_BYTE_FID1,
	FAULT_DETAIL_BYTE_FID2,
	FAULT_DETAIL_BYTE_FID3,
	FAULT_DETAIL_BYTE_VAL0,
	FAULT_DETAIL_BYTE_VAL1,
	FAULT_DETAIL_BYTE_VAL2,
	FAULT_DETAIL_BYTE_VAL3
};

enum ucd9000_fault_format {
	FAULT_FORMAT_NA,
	FAULT_FORMAT_LINEAR11,
	FAULT_FORMAT_LINEAR16,
	FAULT_FORMAT_BITMASK
};

struct ucd9000_fault_type {
	u8 id;
	const char *reason;
	enum ucd9000_fault_format format;
	const char *unit;
};

#define UCD9000_FAULT_TYPE_SEQ_ON 6
#define UCD9000_FAULT_TYPE_SEQ_OFF 7
#define UCD9000_FAULT_TYPE_FAN 8
#define UCD9000_FAULT_TYPE_GPI 9

#define UCD9000_FAULT_TYPE(fault_id, fault_reason, fault_format, fault_unit)	\
{										\
	.id = fault_id,								\
	.reason = fault_reason,							\
	.format = fault_format,							\
	.unit = fault_unit							\
}

static const struct ucd9000_fault_type ucd9000_fault_types[][BITS_PER_BYTE] = {
	// Non-paged faults
	{
		UCD9000_FAULT_TYPE(0, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(1, "System Watchdog Timeout", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(2, "Resequence Error", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(3, "Watchdog Timeout", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(4, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(5, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(6, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(7, "Unknown", FAULT_FORMAT_NA, ""),
	},
	// Paged faults
	{
		UCD9000_FAULT_TYPE(0, "Over-Voltage", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(1, "Under-Voltage", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(2, "Ton Max", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(3, "Over-Current", FAULT_FORMAT_LINEAR11, "mA"),
		UCD9000_FAULT_TYPE(4, "Under-Current", FAULT_FORMAT_LINEAR11, "mA"),
		UCD9000_FAULT_TYPE(5, "Over-Temperature", FAULT_FORMAT_LINEAR11, "C"),
		UCD9000_FAULT_TYPE(6, "Sequence On Timeout", FAULT_FORMAT_BITMASK, ""),
		UCD9000_FAULT_TYPE(7, "Sequence Off Timeout", FAULT_FORMAT_BITMASK, "")
	}
};

static const struct ucd9000_fault_type ucd9012x_fault_types[][BITS_PER_BYTE] = {
	// Non-paged faults
	{
		UCD9000_FAULT_TYPE(0, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(1, "Unknown", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(2, "Resequence Error", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(3, "Watchdog Timeout", FAULT_FORMAT_NA, ""),
		UCD9000_FAULT_TYPE(4, "Fan 1", FAULT_FORMAT_LINEAR11, "RPM"),
		UCD9000_FAULT_TYPE(5, "Fan 2", FAULT_FORMAT_LINEAR11, "RPM"),
		UCD9000_FAULT_TYPE(6, "Fan 3", FAULT_FORMAT_LINEAR11, "RPM"),
		UCD9000_FAULT_TYPE(7, "Fan 4", FAULT_FORMAT_LINEAR11, "RPM")
	},
	// Paged faults
	{
		UCD9000_FAULT_TYPE(0, "Over-Voltage", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(1, "Under-Voltage", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(2, "Ton Max", FAULT_FORMAT_LINEAR16, "mV"),
		UCD9000_FAULT_TYPE(3, "Over-Current", FAULT_FORMAT_LINEAR11, "mA"),
		UCD9000_FAULT_TYPE(4, "Under-Current", FAULT_FORMAT_LINEAR11, "mA"),
		UCD9000_FAULT_TYPE(5, "Over-Temperature", FAULT_FORMAT_LINEAR11, "C"),
		UCD9000_FAULT_TYPE(6, "Sequence On Timeout", FAULT_FORMAT_BITMASK, ""),
		UCD9000_FAULT_TYPE(7, "Slaved Fault", FAULT_FORMAT_NA, ""),
	}
};

struct ucd9000_fault_detail {
	bool paged;
	u8 page;
	u8 type;
	u32 value;
	struct rtc_time timestamp;
	s32 time_msecs;
};

#define UCD9000_FAULT_REASON_STR_LEN	64
#define UCD9000_FAULT_VALUE_STR_LEN	16
#define UCD9000_FAULT_TIMESTAMP_STR_LEN	24
#define UCD9000_FAULT_DESC_STR_LEN	256

struct ucd9000_fault {
	struct list_head list;

	struct ucd9000_fault_detail detail;
	char description_str[UCD9000_FAULT_DESC_STR_LEN];
	char timestamp_str[UCD9000_FAULT_TIMESTAMP_STR_LEN];
};

struct ucd9000_exponent {
	bool valid;
	s16 value;
};

const struct encoded_reload_cause ucd9000_encoded_gpis[] = {};
const struct encoded_reload_cause ucd9000_encoded_rails[] = {};

struct ucd9000_fault_log {
	u8 logged_faults_byte_count;
	u8 detail_byte_count;
	time64_t base_time;
	const struct ucd9000_fault_type (*fault_types)[BITS_PER_BYTE];
	const struct encoded_reload_cause *encoded_gpis;
	u8 encoded_gpi_count;
	const struct encoded_reload_cause *encoded_rails;
	u8 encoded_rail_count;

	struct ucd9000_exponent exponents[PMBUS_PAGES];

	u8 raw_bytes[I2C_SMBUS_BLOCK_MAX];
	struct list_head fault_list;
};

struct ucd9000_data {
	u8 fan_data[UCD9000_NUM_FAN][I2C_SMBUS_BLOCK_MAX];
	struct pmbus_driver_info info;
#ifdef CONFIG_GPIOLIB
	struct gpio_chip gpio;
#endif
	struct dentry *debugfs;
	ktime_t write_time;
	struct ucd9000_fault_log fault_log;
	struct i2c_client *client;
	struct delayed_work rtc_work;
};
#define to_ucd9000_data(_info) container_of(_info, struct ucd9000_data, info)

struct ucd9000_debugfs_entry {
	struct i2c_client *client;
	u8 index;
};

/*
 * It has been observed that the UCD90320 randomly fails register access when
 * doing another access right on the back of a register write. To mitigate this
 * make sure that there is a minimum delay between a write access and the
 * following access. The 500 is based on experimental data. At a delay of
 * 350us the issue seems to go away. Add a bit of extra margin to allow for
 * system to system differences.
 */
#define UCD90320_WAIT_DELAY_US 500

static inline void ucd90320_wait(const struct ucd9000_data *data)
{
	s64 delta = ktime_us_delta(ktime_get(), data->write_time);

	if (delta < UCD90320_WAIT_DELAY_US)
		udelay(UCD90320_WAIT_DELAY_US - delta);
}

static int ucd90320_read_word_data(struct i2c_client *client, int page,
				   int phase, int reg)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);

	if (reg >= PMBUS_VIRT_BASE)
		return -ENXIO;

	ucd90320_wait(data);
	return pmbus_read_word_data(client, page, phase, reg);
}

static int ucd90320_read_byte_data(struct i2c_client *client, int page, int reg)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);

	ucd90320_wait(data);
	return pmbus_read_byte_data(client, page, reg);
}

static int ucd90320_write_word_data(struct i2c_client *client, int page,
				    int reg, u16 word)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);
	int ret;

	ucd90320_wait(data);
	ret = pmbus_write_word_data(client, page, reg, word);
	data->write_time = ktime_get();

	return ret;
}

static int ucd90320_write_byte(struct i2c_client *client, int page, u8 value)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);
	int ret;

	ucd90320_wait(data);
	ret = pmbus_write_byte(client, page, value);
	data->write_time = ktime_get();

	return ret;
}

static int ucd9000_get_fan_config(struct i2c_client *client, int fan)
{
	int fan_config = 0;
	struct ucd9000_data *data
	  = to_ucd9000_data(pmbus_get_driver_info(client));

	if (data->fan_data[fan][3] & 1)
		fan_config |= PB_FAN_2_INSTALLED;   /* Use lower bit position */

	/* Pulses/revolution */
	fan_config |= (data->fan_data[fan][3] & 0x06) >> 1;

	return fan_config;
}

static int ucd9000_read_byte_data(struct i2c_client *client, int page, int reg)
{
	int ret = 0;
	int fan_config;

	switch (reg) {
	case PMBUS_FAN_CONFIG_12:
		if (page > 0)
			return -ENXIO;

		ret = ucd9000_get_fan_config(client, 0);
		if (ret < 0)
			return ret;
		fan_config = ret << 4;
		ret = ucd9000_get_fan_config(client, 1);
		if (ret < 0)
			return ret;
		fan_config |= ret;
		ret = fan_config;
		break;
	case PMBUS_FAN_CONFIG_34:
		if (page > 0)
			return -ENXIO;

		ret = ucd9000_get_fan_config(client, 2);
		if (ret < 0)
			return ret;
		fan_config = ret << 4;
		ret = ucd9000_get_fan_config(client, 3);
		if (ret < 0)
			return ret;
		fan_config |= ret;
		ret = fan_config;
		break;
	default:
		ret = -ENODATA;
		break;
	}
	return ret;
}

/*
 * "a" prefix is curerntly needed for testing since ucd9000 driver is packaged
 * with existing kernel.
 */
static const struct i2c_device_id aucd9000_id[] = {
	{"aucd9000", ucd9000},
	{"aucd90120", ucd90120},
	{"aucd90124", ucd90124},
	{"aucd90160", ucd90160},
	{"aucd90320", ucd90320},
	{"aucd9090", ucd9090},
	{"aucd90910", ucd90910},
	/* Platform-specific devices used for encoded reload causes. */
	{"darwin_aucd90160", ucd90160},
	{"darwin_aucd90320", ucd90320},
	{"meru_aucd90320", ucd90320},
	{}
};
MODULE_DEVICE_TABLE(i2c, aucd9000_id);

static const struct of_device_id __maybe_unused aucd9000_of_match[] = {
	{
		.compatible = "ti,aucd9000",
		.data = (void *)ucd9000
	},
	{
		.compatible = "ti,aucd90120",
		.data = (void *)ucd90120
	},
	{
		.compatible = "ti,aucd90124",
		.data = (void *)ucd90124
	},
	{
		.compatible = "ti,aucd90160",
		.data = (void *)ucd90160
	},
	{
		.compatible = "ti,aucd90320",
		.data = (void *)ucd90320
	},
	{
		.compatible = "ti,aucd9090",
		.data = (void *)ucd9090
	},
	{
		.compatible = "ti,aucd90910",
		.data = (void *)ucd90910
	},
	{
		.compatible = "ti,darwin_aucd90160",
		.data = (void *)ucd90160
	},
	{
		.compatible = "ti,darwin_aucd90320",
		.data = (void *)ucd90320
	},
	{
		.compatible = "ti,meru_aucd90320",
		.data = (void *)ucd90320
	},
	{ },
};
MODULE_DEVICE_TABLE(of, aucd9000_of_match);

#ifdef CONFIG_GPIOLIB
static int ucd9000_gpio_read_config(struct i2c_client *client,
				    unsigned int offset)
{
	int ret;

	/* No page set required */
	ret = i2c_smbus_write_byte_data(client, UCD9000_GPIO_SELECT, offset);
	if (ret < 0)
		return ret;

	return i2c_smbus_read_byte_data(client, UCD9000_GPIO_CONFIG);
}

static int ucd9000_gpio_get(struct gpio_chip *gc, unsigned int offset)
{
	struct i2c_client *client  = gpiochip_get_data(gc);
	int ret;

	ret = ucd9000_gpio_read_config(client, offset);
	if (ret < 0)
		return ret;

	return !!(ret & UCD9000_GPIO_CONFIG_STATUS);
}

static void ucd9000_gpio_set(struct gpio_chip *gc, unsigned int offset,
			     int value)
{
	struct i2c_client *client = gpiochip_get_data(gc);
	int ret;

	ret = ucd9000_gpio_read_config(client, offset);
	if (ret < 0) {
		dev_dbg(&client->dev, "failed to read GPIO %d config: %d\n",
			offset, ret);
		return;
	}

	if (value) {
		if (ret & UCD9000_GPIO_CONFIG_STATUS)
			return;

		ret |= UCD9000_GPIO_CONFIG_STATUS;
	} else {
		if (!(ret & UCD9000_GPIO_CONFIG_STATUS))
			return;

		ret &= ~UCD9000_GPIO_CONFIG_STATUS;
	}

	ret |= UCD9000_GPIO_CONFIG_ENABLE;

	/* Page set not required */
	ret = i2c_smbus_write_byte_data(client, UCD9000_GPIO_CONFIG, ret);
	if (ret < 0) {
		dev_dbg(&client->dev, "Failed to write GPIO %d config: %d\n",
			offset, ret);
		return;
	}

	ret &= ~UCD9000_GPIO_CONFIG_ENABLE;

	ret = i2c_smbus_write_byte_data(client, UCD9000_GPIO_CONFIG, ret);
	if (ret < 0)
		dev_dbg(&client->dev, "Failed to write GPIO %d config: %d\n",
			offset, ret);
}

static int ucd9000_gpio_get_direction(struct gpio_chip *gc,
				      unsigned int offset)
{
	struct i2c_client *client = gpiochip_get_data(gc);
	int ret;

	ret = ucd9000_gpio_read_config(client, offset);
	if (ret < 0)
		return ret;

	return !(ret & UCD9000_GPIO_CONFIG_OUT_ENABLE);
}

static int ucd9000_gpio_set_direction(struct gpio_chip *gc,
				      unsigned int offset, bool direction_out,
				      int requested_out)
{
	struct i2c_client *client = gpiochip_get_data(gc);
	int ret, config, out_val;

	ret = ucd9000_gpio_read_config(client, offset);
	if (ret < 0)
		return ret;

	if (direction_out) {
		out_val = requested_out ? UCD9000_GPIO_CONFIG_OUT_VALUE : 0;

		if (ret & UCD9000_GPIO_CONFIG_OUT_ENABLE) {
			if ((ret & UCD9000_GPIO_CONFIG_OUT_VALUE) == out_val)
				return 0;
		} else {
			ret |= UCD9000_GPIO_CONFIG_OUT_ENABLE;
		}

		if (out_val)
			ret |= UCD9000_GPIO_CONFIG_OUT_VALUE;
		else
			ret &= ~UCD9000_GPIO_CONFIG_OUT_VALUE;

	} else {
		if (!(ret & UCD9000_GPIO_CONFIG_OUT_ENABLE))
			return 0;

		ret &= ~UCD9000_GPIO_CONFIG_OUT_ENABLE;
	}

	ret |= UCD9000_GPIO_CONFIG_ENABLE;
	config = ret;

	/* Page set not required */
	ret = i2c_smbus_write_byte_data(client, UCD9000_GPIO_CONFIG, config);
	if (ret < 0)
		return ret;

	config &= ~UCD9000_GPIO_CONFIG_ENABLE;

	return i2c_smbus_write_byte_data(client, UCD9000_GPIO_CONFIG, config);
}

static int ucd9000_gpio_direction_input(struct gpio_chip *gc,
					unsigned int offset)
{
	return ucd9000_gpio_set_direction(gc, offset, UCD9000_GPIO_INPUT, 0);
}

static int ucd9000_gpio_direction_output(struct gpio_chip *gc,
					 unsigned int offset, int val)
{
	return ucd9000_gpio_set_direction(gc, offset, UCD9000_GPIO_OUTPUT,
					  val);
}

static void ucd9000_probe_gpio(struct i2c_client *client,
			       const struct i2c_device_id *mid,
			       struct ucd9000_data *data)
{
	int rc;

	switch (mid->driver_data) {
	case ucd9090:
		data->gpio.ngpio = UCD9090_NUM_GPIOS;
		break;
	case ucd90120:
	case ucd90124:
	case ucd90160:
		data->gpio.ngpio = UCD901XX_NUM_GPIOS;
		break;
	case ucd90320:
		data->gpio.ngpio = UCD90320_NUM_GPIOS;
		break;
	case ucd90910:
		data->gpio.ngpio = UCD90910_NUM_GPIOS;
		break;
	default:
		return; /* GPIO support is optional. */
	}

	/*
	 * Pinmux support has not been added to the new gpio_chip.
	 * This support should be added when possible given the mux
	 * behavior of these IO devices.
	 */
	data->gpio.label = client->name;
	data->gpio.get_direction = ucd9000_gpio_get_direction;
	data->gpio.direction_input = ucd9000_gpio_direction_input;
	data->gpio.direction_output = ucd9000_gpio_direction_output;
	data->gpio.get = ucd9000_gpio_get;
	data->gpio.set = ucd9000_gpio_set;
	data->gpio.can_sleep = true;
	data->gpio.base = -1;
	data->gpio.parent = &client->dev;

	rc = devm_gpiochip_add_data(&client->dev, &data->gpio, client);
	if (rc)
		dev_warn(&client->dev, "Could not add gpiochip: %d\n", rc);
}
#else
static void ucd9000_probe_gpio(struct i2c_client *client,
			       const struct i2c_device_id *mid,
			       struct ucd9000_data *data)
{
}
#endif /* CONFIG_GPIOLIB */

static void ucd9000_fault_log_get_config(const struct i2c_device_id *mid,
				struct ucd9000_fault_log *fault_log)
{
	int i;

	switch(mid->driver_data) {
	case ucd90120:
	case ucd90124:
		fault_log->base_time = 0;
		fault_log->logged_faults_byte_count = UCD9012X_LOGGED_FAULTS_BYTE_COUNT;
		fault_log->detail_byte_count = UCD9000_FAULT_DETAIL_BYTE_COUNT;
		fault_log->fault_types = ucd9012x_fault_types;
		break;
	case ucd90160:
		fault_log->base_time = 0;
		fault_log->logged_faults_byte_count = UCD90160_LOGGED_FAULTS_BYTE_COUNT;
		fault_log->detail_byte_count = UCD9000_FAULT_DETAIL_BYTE_COUNT;
		fault_log->fault_types = ucd9000_fault_types;
		break;
	case ucd90320:
		fault_log->base_time = RTC_TIMESTAMP_BEGIN_2000;
		fault_log->logged_faults_byte_count = UCD90320_LOGGED_FAULTS_BYTE_COUNT;
		fault_log->detail_byte_count = UCD90320_FAULT_DETAIL_BYTE_COUNT;
		fault_log->fault_types = ucd9000_fault_types;
		break;
	case ucd90910:
		fault_log->base_time = 0;
		fault_log->logged_faults_byte_count = UCD90910_LOGGED_FAULTS_BYTE_COUNT;
		fault_log->detail_byte_count = UCD9000_FAULT_DETAIL_BYTE_COUNT;
		fault_log->fault_types = ucd9000_fault_types;
		break;
	default:
		fault_log->base_time = 0;
		fault_log->logged_faults_byte_count = UCD9000_LOGGED_FAULTS_BYTE_COUNT;
		fault_log->detail_byte_count = UCD9000_FAULT_DETAIL_BYTE_COUNT;
		fault_log->fault_types = ucd9000_fault_types;
		break;
	}

	if (!strcmp(mid->name, "darwin_aucd90160")) {
		fault_log->encoded_gpis = darwin_aucd90160_encoded_gpis;
		fault_log->encoded_gpi_count = ARRAY_SIZE(darwin_aucd90160_encoded_gpis);
		fault_log->encoded_rails = darwin_aucd90160_encoded_rails;
		fault_log->encoded_rail_count = ARRAY_SIZE(darwin_aucd90160_encoded_rails);
	} else if (!strcmp(mid->name, "darwin_aucd90320")) {
		fault_log->encoded_gpis = darwin_aucd90320_encoded_gpis;
		fault_log->encoded_gpi_count = ARRAY_SIZE(darwin_aucd90320_encoded_gpis);
		fault_log->encoded_rails = darwin_aucd90320_encoded_rails;
		fault_log->encoded_rail_count = ARRAY_SIZE(darwin_aucd90320_encoded_rails);
	} else if (!strcmp(mid->name, "meru_aucd90320")) {
		fault_log->encoded_gpis = meru800bfa_aucd90320_encoded_gpis;
		fault_log->encoded_gpi_count = ARRAY_SIZE(meru800bfa_aucd90320_encoded_gpis);
		fault_log->encoded_rails = meru800bfa_aucd90320_encoded_rails;
		fault_log->encoded_rail_count = ARRAY_SIZE(meru800bfa_aucd90320_encoded_rails);
	} else {
		fault_log->encoded_gpis = ucd9000_encoded_gpis;
		fault_log->encoded_gpi_count = ARRAY_SIZE(ucd9000_encoded_gpis);
		fault_log->encoded_rails = ucd9000_encoded_rails;
		fault_log->encoded_rail_count = ARRAY_SIZE(ucd9000_encoded_rails);
	}

	for (i = 0; i < PMBUS_PAGES; i++)
		fault_log->exponents[i].valid = false;
}

static int ucd9000_fault_log_read_faults(struct i2c_client *client,
				struct ucd9000_fault_log *fault_log)
{
	u8 read_byte_count;
	u8 read_buffer[I2C_SMBUS_BLOCK_MAX];
	char hex_str[I2C_SMBUS_BLOCK_MAX * 2] = { 0 };
	int i, count, pos, ret;

	read_byte_count = fault_log->logged_faults_byte_count + 1;
	if (read_byte_count > I2C_SMBUS_BLOCK_MAX)
		read_byte_count = I2C_SMBUS_BLOCK_MAX;

	ret = i2c_smbus_read_i2c_block_data(client, UCD9000_LOGGED_FAULTS,
			read_byte_count, read_buffer);
	if (ret < 0) {
		dev_dbg(&client->dev, "Failed to read logged faults register: %d\n",
			ret);
		return ret;
	}

	/* The first byte is the number of LOGGED_FAULTS bytes. UCD90320 actually
	 * supports first byte + 37 logged faults bytes, but the kernel SMBus
	 * implementation limits block reads to 32 bytes. Accept the limitation
	 * rather than implementing our own block read.
	 */
	count = read_buffer[0];
	if (count > ret - 1)
		count = ret - 1;
	memcpy(fault_log->raw_bytes, read_buffer + 1, count);

	for (i = 0, pos = 0; i < count && pos < sizeof(hex_str) - 3; i++) {
		pos += snprintf(hex_str + pos, sizeof(hex_str) - pos, "%02x",
					fault_log->raw_bytes[i]);
	}
	hex_str[pos] = '\0';

	dev_info(&client->dev, "Read %d bytes from fault log: 0x%s\n", count,
		hex_str);

	return count;
}

static void ucd9000_fault_log_clear_faults(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_fault_log *fault_log)
{
	u8 clear_byte_count;
	u8 clear_buffer[I2C_SMBUS_BLOCK_MAX] = {0};
	int ret;

	clear_byte_count = fault_log->logged_faults_byte_count + 1;
	if (clear_byte_count > I2C_SMBUS_BLOCK_MAX)
		clear_byte_count = I2C_SMBUS_BLOCK_MAX;

	ret = i2c_smbus_write_block_data(client, UCD9000_LOGGED_FAULTS,
			clear_byte_count, clear_buffer);
	if (mid->driver_data == ucd90320)
		udelay(UCD90320_WAIT_DELAY_US);
	if (ret < 0)
		dev_warn(&client->dev, "Failed to clear fault log: %d\n", ret);
	else
		dev_info(&client->dev, "Cleared fault log\n");
}

static int ucd9000_fault_log_detailed_fault_count(struct i2c_client *client)
{
	int ret;

	ret = i2c_smbus_read_word_data(client, UCD9000_LOGGED_FAULT_DETAIL_INDEX);
	if (ret < 0) {
		dev_dbg(&client->dev,
			"Failed to read logged fault detail index register: %d\n", ret);
		return ret;
	}
	return (ret >> 8) & 0xff;
}

static void ucd9000_fault_log_parse_fault_detail(u8 *detail_buffer,
				u8 detail_buffer_len, time64_t base_time,
				struct ucd9000_fault_detail *detail)
{
	u16 days;
	u32 page_and_msecs, fault_id_and_days, msecs;
	time64_t secs_since_base, fault_time;

	page_and_msecs = (detail_buffer[FAULT_DETAIL_BYTE_MSEC0] << 24) |
		(detail_buffer[FAULT_DETAIL_BYTE_MSEC1] << 16) |
		(detail_buffer[FAULT_DETAIL_BYTE_MSEC2] << 8) |
		(detail_buffer[FAULT_DETAIL_BYTE_MSEC3]);
	fault_id_and_days = (detail_buffer[FAULT_DETAIL_BYTE_FID0] << 24) |
		(detail_buffer[FAULT_DETAIL_BYTE_FID1] << 16) |
		(detail_buffer[FAULT_DETAIL_BYTE_FID2] << 8) |
		(detail_buffer[FAULT_DETAIL_BYTE_FID3]);
	detail->paged = (fault_id_and_days >> 31) & 0x1;
	detail->type = (fault_id_and_days >> 27) & 0xf;
	detail->value = (detail_buffer[FAULT_DETAIL_BYTE_VAL1] << 8) |
		(detail_buffer[FAULT_DETAIL_BYTE_VAL0]);

	switch(detail_buffer_len) {
	case UCD90320_FAULT_DETAIL_BYTE_COUNT:
		detail->page = (page_and_msecs >> 27);
		msecs = page_and_msecs & 0x7ffffff;
		days = (fault_id_and_days >> 11) & 0xffff;
		/* Sequence faults use additional two value bytes. */
		if (detail->type == UCD9000_FAULT_TYPE_SEQ_ON ||
			detail->type == UCD9000_FAULT_TYPE_SEQ_OFF) {
			detail->value |= ((detail_buffer[FAULT_DETAIL_BYTE_VAL3] << 24) |
				(detail_buffer[FAULT_DETAIL_BYTE_VAL2] << 16));
		}
		break;
	case UCD9000_FAULT_DETAIL_BYTE_COUNT:
	default:
		detail->page = ((fault_id_and_days >> 23) & 0xf);
		msecs = page_and_msecs;
		days = fault_id_and_days & 0x7fffff;
		break;
	}

	/* Compute the fault time from the base. */
	secs_since_base = (time64_t) days * SECS_PER_DAY;
	secs_since_base += msecs / 1000;
	fault_time = base_time + secs_since_base;
	rtc_time64_to_tm(fault_time, &detail->timestamp);
	detail->time_msecs = msecs % 1000;
}

static void ucd9000_fault_log_create_timestamp_str(const struct rtc_time *tm,
				s32 time_msecs, char *timestamp_str, size_t timestamp_str_len)
{
    snprintf(timestamp_str, timestamp_str_len, "%02d-%02d-%04d %02d:%02d:%02d.%03d",
        tm->tm_mon + 1, tm->tm_mday, tm->tm_year + 1900, tm->tm_hour,
        tm->tm_min, tm->tm_sec, time_msecs);
}

static int ucd9000_read_vout_mode_exponent(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_exponent *exponents,
				u8 page)
{
	int ret;

	/* Only read VOUT_MODE if we haven't already successfuly read it. */
	if (!exponents[page].valid) {
		i2c_smbus_write_byte_data(client, PMBUS_PAGE, page);
		if (mid->driver_data == ucd90320)
			udelay(UCD90320_WAIT_DELAY_US);
		ret = i2c_smbus_read_byte_data(client, PMBUS_VOUT_MODE);
		if (ret < 0) {
			dev_dbg(&client->dev,
				"Failed to read vout_mode register: %d\n", ret);
			return ret;
		} else {
			exponents[page].valid = true;
			exponents[page].value = (s16) (((ret & 0x1f) << 27) >> 27);
		}
	}

	return 0;
}

static void ucd9000_fault_log_create_value_str(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_exponent *exponents,
				enum ucd9000_fault_format format, u8 page, u32 value,
				char *value_str, size_t value_str_len)
{
	s16 exponent, linear11_mantissa;
	u16 linear16_mantissa;
	s32 decoded_value;
	int ret;

	switch (format) {
	case FAULT_FORMAT_LINEAR11:
		exponent = ((s16) value) >> 11;
		linear11_mantissa = ((s16) ((value & 0x7ff) << 5)) >> 5;
		if (exponent >= 0)
			decoded_value = linear11_mantissa << exponent;
		else
			decoded_value = linear11_mantissa >> (-exponent);
		ret = snprintf(value_str, value_str_len, "%d", decoded_value);
		break;
	case FAULT_FORMAT_LINEAR16:
		ret = ucd9000_read_vout_mode_exponent(client, mid, exponents, page);
		if (ret < 0) {
			snprintf(value_str, value_str_len, "Unknown");
		} else {
			exponent = exponents[page].value;
			linear16_mantissa = (u16) value;
			if (exponent >= 0)
				decoded_value = linear16_mantissa << exponent;
			else
				decoded_value = linear16_mantissa >> (-exponent);
			snprintf(value_str, value_str_len, "%d", decoded_value);
		}
		break;
	case FAULT_FORMAT_BITMASK:
		snprintf(value_str, value_str_len, "0x%08x", value);
		break;
	case FAULT_FORMAT_NA:
	default:
		snprintf(value_str, value_str_len, "N/A");
		break;
	}
}

static bool ucd9000_get_encoded_reload_cause(
				const struct encoded_reload_cause *encoded_reload_causes,
				u8 encoded_reload_cause_count, u8 fault_id,
				const struct encoded_reload_cause **found_encoded_reload_cause)

{
	u8 i;

	if (encoded_reload_cause_count < 0)
		return false;

    for (i = 0; i < encoded_reload_cause_count; i++) {
        if (encoded_reload_causes[i].id == fault_id) {
            *found_encoded_reload_cause = &encoded_reload_causes[i];
            return true;
        }
    }

    return false;
}

static void ucd9000_fault_log_create_description_str(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_fault_log *fault_log,
				struct ucd9000_fault *fault,
				char *description_str, size_t description_str_len)
{
	char reason_str[UCD9000_FAULT_REASON_STR_LEN];
	char value_str[UCD9000_FAULT_VALUE_STR_LEN];
	enum ucd9000_fault_format fault_fmt;
	const struct encoded_reload_cause *encoded_reload_cause;
	const char *unit;
	bool paged;

	if (fault->detail.type == UCD9000_FAULT_TYPE_GPI) {
		if (ucd9000_get_encoded_reload_cause(fault_log->encoded_gpis,
				fault_log->encoded_gpi_count, fault->detail.page + 1,
				&encoded_reload_cause)) {
			snprintf(reason_str, sizeof(reason_str), "%s",
				encoded_reload_cause->description);
		} else {
			snprintf(reason_str, sizeof(reason_str), "GPI %u",
				fault->detail.page + 1);
		}
		fault_fmt = FAULT_FORMAT_NA;
		unit = "";
	} else if (fault->detail.type == UCD9000_FAULT_TYPE_FAN) {
		snprintf(reason_str, sizeof(reason_str), "Fan %u", fault->detail.page + 1);
		fault_fmt = FAULT_FORMAT_LINEAR11;
		unit = "RPM";
	} else if (fault->detail.type < BITS_PER_BYTE) {
		paged = fault->detail.paged;
		if (paged && ucd9000_get_encoded_reload_cause(fault_log->encoded_rails,
				fault_log->encoded_rail_count, fault->detail.page + 1,
				&encoded_reload_cause)) {
					snprintf(reason_str, sizeof(reason_str), "%s %s",
						encoded_reload_cause->description,
						fault_log->fault_types[paged][fault->detail.type].reason);
		} else {
			snprintf(reason_str, sizeof(reason_str), "%s",
				fault_log->fault_types[paged][fault->detail.type].reason);
		}
		fault_fmt = fault_log->fault_types[paged][fault->detail.type].format;
		unit = fault_log->fault_types[paged][fault->detail.type].unit;
	} else {
		snprintf(reason_str, sizeof(reason_str), "Unknown");
		fault_fmt = FAULT_FORMAT_NA;
		unit = "";
	}

	ucd9000_fault_log_create_value_str(client, mid, fault_log->exponents,
			fault_fmt, fault->detail.page, fault->detail.value, value_str,
			sizeof(value_str));

	snprintf(description_str, description_str_len,
		"%s %s Fault (Type: %u, Rail: %u, Value: %s%s)",
		reason_str,
		fault->detail.paged ? "Paged" : "Non-Paged",
		fault->detail.type,
		fault->detail.page + 1,
		value_str,
		unit
	);
}

static int ucd9000_fault_log_add_fault(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_fault_log *fault_log,
				u8 *detail_buffer)
{
	struct ucd9000_fault *fault;

	fault = devm_kzalloc(&client->dev, sizeof(*fault), GFP_KERNEL);
	if (!fault)
		return -ENOMEM;

	ucd9000_fault_log_parse_fault_detail(detail_buffer,
		fault_log->detail_byte_count,
		fault_log->base_time, &fault->detail);

	ucd9000_fault_log_create_timestamp_str(&fault->detail.timestamp,
		fault->detail.time_msecs, fault->timestamp_str,
		sizeof(fault->timestamp_str));

	ucd9000_fault_log_create_description_str(client, mid, fault_log, fault,
		fault->description_str, sizeof(fault->description_str));

	list_add_tail(&fault->list, &fault_log->fault_list);

	return 0;
}

static int ucd9000_fault_log_read_detailed_faults(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_fault_log *fault_log,
				u8 fault_count)
{
	u8 detail_buffer[I2C_SMBUS_BLOCK_MAX];
	int i, ret = 0;

	for (i = 0; i < fault_count; i++) {
		ret = i2c_smbus_write_word_data(client,
				UCD9000_LOGGED_FAULT_DETAIL_INDEX, i);
		if (mid->driver_data == ucd90320)
			udelay(UCD90320_WAIT_DELAY_US);
		if (ret < 0) {
			dev_dbg(&client->dev,
				"Failed to set fault detail index register for index %d: %d\n",
				i, ret);
			continue;
		}

		memset(detail_buffer, 0, sizeof(detail_buffer));

		ret = i2c_smbus_read_block_data(client, UCD9000_LOGGED_FAULT_DETAIL,
				detail_buffer);
		if (ret < 0) {
			dev_dbg(&client->dev,
				"Failed to read fault detail register for index %d: %d\n",
				i, ret);
		} else if (ret != fault_log->detail_byte_count) {
			dev_dbg(&client->dev,
				"Unexpected fault detail byte count for index %d: %d\n",
				i, ret);
		}
		else {
			ret = ucd9000_fault_log_add_fault(client, mid,
					fault_log, detail_buffer);
			if (ret < 0)
				return ret;
		}
	}

	return ret;
}

static int ucd9000_probe_fault_log(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_data *data)
{
	struct ucd9000_fault_log *fault_log = &data->fault_log;
	struct ucd9000_fault *fault_iter;
	u8 fault_count = 0;
	int ret;

	ucd9000_fault_log_get_config(mid, fault_log);

	ret = ucd9000_fault_log_read_faults(client, fault_log);
	if (ret < 0)
		return ret;

	INIT_LIST_HEAD(&fault_log->fault_list);

	if (fault_log->raw_bytes[0] & UCD9000_LOGGED_FAULTS_NOT_EMPTY_BIT) {
		ret = ucd9000_fault_log_detailed_fault_count(client);
		if (ret < 0)
			return ret;

		fault_count = ret;

		if (fault_count) {
			ret = ucd9000_fault_log_read_detailed_faults(client, mid,
					fault_log, fault_count);
			if (ret < 0) {
				dev_dbg(&client->dev,
					"Failed to read fault log details: %d\n", ret);
				return ret;
			}
		}
	}

	dev_info(&client->dev, "Found %d detailed faults\n", fault_count);
	list_for_each_entry(fault_iter, &fault_log->fault_list, list) {
		dev_info(&client->dev, "%s %s", fault_iter->description_str,
			fault_iter->timestamp_str);
	}

	ucd9000_fault_log_clear_faults(client, mid, fault_log);

	return 0;
}

static int ucd9000_set_rtc(struct ucd9000_data *data)
{
	struct i2c_client *client = data->client;
	u8 write_buffer[UCD9000_RTC_SET_LEN];
	u64 sys_run_time_msecs;
	u32 sys_msecs, sys_days;
	time64_t now;

	now = ktime_get_real_seconds();
	sys_run_time_msecs = now * 1000;
	sys_days = sys_run_time_msecs / MSECS_PER_DAY;
	sys_msecs = sys_run_time_msecs % MSECS_PER_DAY;

	if (data->fault_log.base_time == RTC_TIMESTAMP_BEGIN_2000) {
		/*
		 * If the RTC is offset from 0000-01-01 rather than 1970-01-01,
		 * add the days from 0000-01-01 to 1970-01-01 to get the correct
		 * offset.
		 */
		sys_days += 719162;
	}

	write_buffer[0] = (sys_msecs >> 24) & 0xff;
	write_buffer[1] = (sys_msecs >> 16) & 0xff;
	write_buffer[2] = (sys_msecs >> 8) & 0xff;
	write_buffer[3] = sys_msecs & 0xff;
	write_buffer[4] = (sys_days >> 24) & 0xff;
	write_buffer[5] = (sys_days >> 16) & 0xff;
	write_buffer[6] = (sys_days >> 8) & 0xff;
	write_buffer[7] = sys_days & 0xff;

	return i2c_smbus_write_block_data(client, UCD9000_RTC_SET,
				sizeof(write_buffer),
				write_buffer);
}

static void ucd9000_rtc_work_start(struct work_struct *__work)
{
	int ret;
	struct delayed_work *delayed_work = container_of(__work,
						struct delayed_work,
						work);
	struct ucd9000_data *data = container_of(delayed_work,
					struct ucd9000_data,
					rtc_work);

	ret = ucd9000_set_rtc(data);
	if (ret)
		dev_warn(&data->client->dev, "Failed to set RTC: %d\n", ret);

	schedule_delayed_work(&data->rtc_work,
		msecs_to_jiffies(UCD9000_RTC_UPDATE_INTERVAL_MSECS));
}

static void ucd9000_rtc_work_stop(struct i2c_client *client)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);

	cancel_delayed_work_sync(&data->rtc_work);
}

#ifdef CONFIG_DEBUG_FS
static int ucd9000_get_mfr_status(struct i2c_client *client, u8 *buffer)
{
	int ret = pmbus_set_page(client, 0, 0xff);

	if (ret < 0)
		return ret;

	return i2c_smbus_read_block_data(client, UCD9000_MFR_STATUS, buffer);
}

static int ucd9000_debugfs_show_mfr_status_bit(void *data, u64 *val)
{
	struct ucd9000_debugfs_entry *entry = data;
	struct i2c_client *client = entry->client;
	u8 buffer[I2C_SMBUS_BLOCK_MAX];
	int ret, i;

	ret = ucd9000_get_mfr_status(client, buffer);
	if (ret < 0)
		return ret;

	/*
	 * GPI fault bits are in sets of 8, two bytes from end of response.
	 */
	i = ret - 3 - entry->index / 8;
	if (i >= 0)
		*val = !!(buffer[i] & BIT(entry->index % 8));

	return 0;
}
DEFINE_DEBUGFS_ATTRIBUTE(ucd9000_debugfs_mfr_status_bit,
			 ucd9000_debugfs_show_mfr_status_bit, NULL, "%1lld\n");

static ssize_t ucd9000_debugfs_read_mfr_status(struct file *file,
					       char __user *buf, size_t count,
					       loff_t *ppos)
{
	struct i2c_client *client = file->private_data;
	u8 buffer[I2C_SMBUS_BLOCK_MAX];
	char str[(I2C_SMBUS_BLOCK_MAX * 2) + 2];
	char *res;
	int rc;

	rc = ucd9000_get_mfr_status(client, buffer);
	if (rc < 0)
		return rc;

	res = bin2hex(str, buffer, min(rc, I2C_SMBUS_BLOCK_MAX));
	*res++ = '\n';
	*res = 0;

	return simple_read_from_buffer(buf, count, ppos, str, res - str);
}

static const struct file_operations ucd9000_debugfs_show_mfr_status_fops = {
	.llseek = noop_llseek,
	.read = ucd9000_debugfs_read_mfr_status,
	.open = simple_open,
};

static int ucd9000_init_debugfs(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_data *data)
{
	struct dentry *debugfs;
	struct ucd9000_debugfs_entry *entries;
	int i, gpi_count;
	char name[UCD9000_DEBUGFS_NAME_LEN];

	debugfs = pmbus_get_debugfs_dir(client);
	if (!debugfs)
		return -ENOENT;

	data->debugfs = debugfs_create_dir(client->name, debugfs);
	if (!data->debugfs)
		return -ENOENT;

	/*
	 * Of the chips this driver supports, only the UCD9090, UCD90160,
	 * UCD90320, and UCD90910 report GPI faults in their MFR_STATUS
	 * register, so only create the GPI fault debugfs attributes for those
	 * chips.
	 */
	if (mid->driver_data == ucd9090 || mid->driver_data == ucd90160 ||
	    mid->driver_data == ucd90320 || mid->driver_data == ucd90910) {
		gpi_count = mid->driver_data == ucd90320 ? UCD90320_GPI_COUNT
							 : UCD9000_GPI_COUNT;
		entries = devm_kcalloc(&client->dev,
				       gpi_count, sizeof(*entries),
				       GFP_KERNEL);
		if (!entries)
			return -ENOMEM;

		for (i = 0; i < gpi_count; i++) {
			entries[i].client = client;
			entries[i].index = i;
			scnprintf(name, UCD9000_DEBUGFS_NAME_LEN,
				  "gpi%d_alarm", i + 1);
			debugfs_create_file(name, 0444, data->debugfs,
					    &entries[i],
					    &ucd9000_debugfs_mfr_status_bit);
		}
	}

	scnprintf(name, UCD9000_DEBUGFS_NAME_LEN, "mfr_status");
	debugfs_create_file(name, 0444, data->debugfs, client,
			    &ucd9000_debugfs_show_mfr_status_fops);

	return 0;
}
#else
static int ucd9000_init_debugfs(struct i2c_client *client,
				const struct i2c_device_id *mid,
				struct ucd9000_data *data)
{
	return 0;
}
#endif /* CONFIG_DEBUG_FS */

static int ucd9000_probe(struct i2c_client *client)
{
	u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1];
	struct ucd9000_data *data;
	struct pmbus_driver_info *info;
	const struct i2c_device_id *mid;
	enum chips chip;
	int i, ret;

	if (!i2c_check_functionality(client->adapter,
				     I2C_FUNC_SMBUS_BYTE_DATA |
				     I2C_FUNC_SMBUS_BLOCK_DATA))
		return -ENODEV;

	ret = i2c_smbus_read_block_data(client, UCD9000_DEVICE_ID,
					block_buffer);
	if (ret < 0) {
		dev_err(&client->dev, "Failed to read device ID\n");
		return ret;
	}
	block_buffer[ret] = '\0';
	dev_info(&client->dev, "Device ID %s\n", block_buffer);

	/*
	 * Explicitly match the device ID used to initialize the driver.
	 * This is currently needed for testing since the existing driver will read
	 * DEVICE_ID and match the value.
	 */
	mid = i2c_match_id(aucd9000_id, client);
	if (!mid) {
		for (mid = aucd9000_id; mid->name[0]; mid++) {
			if (!strncasecmp(mid->name, block_buffer, strlen(mid->name)))
				break;
		}
		if (!mid->name[0]) {
			dev_err(&client->dev, "Unsupported device\n");
			return -ENODEV;
		}
	}

	if (client->dev.of_node)
		chip = (enum chips)of_device_get_match_data(&client->dev);
	else
		chip = mid->driver_data;

	if (chip != ucd9000 && strcmp(client->name, mid->name) != 0)
		dev_notice(&client->dev,
			   "Device mismatch: Configured %s, detected %s\n",
			   client->name, mid->name);

	data = devm_kzalloc(&client->dev, sizeof(struct ucd9000_data),
			    GFP_KERNEL);
	if (!data)
		return -ENOMEM;
	info = &data->info;

	ret = i2c_smbus_read_byte_data(client, UCD9000_NUM_PAGES);
	if (ret < 0) {
		dev_err(&client->dev,
			"Failed to read number of active pages\n");
		return ret;
	}
	info->pages = ret;
	if (!info->pages) {
		dev_err(&client->dev, "No pages configured\n");
		return -ENODEV;
	}

	/* The internal temperature sensor is always active */
	info->func[0] = PMBUS_HAVE_TEMP;

	/* Everything else is configurable */
	ret = i2c_smbus_read_block_data(client, UCD9000_MONITOR_CONFIG,
					block_buffer);
	if (ret <= 0) {
		dev_err(&client->dev, "Failed to read configuration data\n");
		return -ENODEV;
	}
	for (i = 0; i < ret; i++) {
		int page = UCD9000_MON_PAGE(block_buffer[i]);

		if (page >= info->pages)
			continue;

		switch (UCD9000_MON_TYPE(block_buffer[i])) {
		case UCD9000_MON_VOLTAGE:
		case UCD9000_MON_VOLTAGE_HW:
			info->func[page] |= PMBUS_HAVE_VOUT
			  | PMBUS_HAVE_STATUS_VOUT;
			break;
		case UCD9000_MON_TEMPERATURE:
			info->func[page] |= PMBUS_HAVE_TEMP2
			  | PMBUS_HAVE_STATUS_TEMP;
			break;
		case UCD9000_MON_CURRENT:
			info->func[page] |= PMBUS_HAVE_IOUT
			  | PMBUS_HAVE_STATUS_IOUT;
			break;
		default:
			break;
		}
	}

	/* Fan configuration */
	if (mid->driver_data == ucd90124) {
		for (i = 0; i < UCD9000_NUM_FAN; i++) {
			i2c_smbus_write_byte_data(client,
						  UCD9000_FAN_CONFIG_INDEX, i);
			ret = i2c_smbus_read_block_data(client,
							UCD9000_FAN_CONFIG,
							data->fan_data[i]);
			if (ret < 0)
				return ret;
		}
		i2c_smbus_write_byte_data(client, UCD9000_FAN_CONFIG_INDEX, 0);

		info->read_byte_data = ucd9000_read_byte_data;
		info->func[0] |= PMBUS_HAVE_FAN12 | PMBUS_HAVE_STATUS_FAN12
		  | PMBUS_HAVE_FAN34 | PMBUS_HAVE_STATUS_FAN34;
	} else if (mid->driver_data == ucd90320) {
		info->read_byte_data = ucd90320_read_byte_data;
		info->read_word_data = ucd90320_read_word_data;
		info->write_byte = ucd90320_write_byte;
		info->write_word_data = ucd90320_write_word_data;
	}

	ucd9000_probe_gpio(client, mid, data);

	ret = ucd9000_probe_fault_log(client, mid, data);
	if (ret)
		dev_warn(&client->dev, "Failed to read fault log: %d\n", ret);

	data->client = client;
	ret = ucd9000_set_rtc(data);
	if (ret)
		dev_warn(&client->dev, "Failed to set RTC: %d\n", ret);

	ret = pmbus_do_probe(client, info);
	if (ret)
		return ret;

	ret = ucd9000_init_debugfs(client, mid, data);
	if (ret)
		dev_warn(&client->dev, "Failed to register debugfs: %d\n",
			 ret);

	INIT_DELAYED_WORK(&data->rtc_work, ucd9000_rtc_work_start);
	schedule_delayed_work(&data->rtc_work,
		msecs_to_jiffies(UCD9000_RTC_UPDATE_INTERVAL_MSECS));

	return 0;
}

static void ucd9000_remove(struct i2c_client *client)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ucd9000_data *data = to_ucd9000_data(info);

	cancel_delayed_work_sync(&data->rtc_work);
}

/* This is the driver that will be inserted */
static struct i2c_driver aucd9000_driver = {
	.driver = {
		.name = "aucd9000",
		.of_match_table = of_match_ptr(aucd9000_of_match),
	},
	.probe = ucd9000_probe,
	.probe = ucd9000_probe,
	.remove = ucd9000_remove,
	.id_table = aucd9000_id,
};

module_i2c_driver(aucd9000_driver);

MODULE_AUTHOR("Guenter Roeck");
MODULE_DESCRIPTION("PMBus driver for TI UCD90xxx");
MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
