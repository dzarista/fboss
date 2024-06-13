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
 *
 */


#include <linux/bits.h>
#include <linux/module.h>
#include <linux/leds.h>
#include <linux/limits.h>
#include <linux/pci.h>

#include "fbiob-auxdev.h"
#include "scd-attrs.h"

#define DRIVER_NAME		"scd-leds"

#define SCD_LED_BLUE			BIT(29)
#define SCD_LED_GREEN			BIT(28)
#define SCD_LED_RED				BIT(27)
#define SCD_LED_FLASH_ENABLE	BIT(24)
#define SCD_LED_INTENSITY_BLUE		0xff << 16
#define SCD_LED_INTENSITY_GREEN		0xff << 8
#define SCD_LED_INTENSITY_RED		0xff
#define SCD_LED_MASK_ALL	(SCD_LED_BLUE | SCD_LED_GREEN | \
							SCD_LED_RED | SCD_LED_FLASH_ENABLE)

#define SCD_LED_FLASH_RATE_MASK_1	0xFFFF
#define SCD_LED_FLASH_RATE_MASK_2	0x00FF

#define SCD_LED_ATTR_COUNT 3

struct scd_led_attribute {
	struct device_attribute attr;
	struct scd_led_dev *led;
	char name[NAME_MAX];
};

#define SCD_LED_ATTR(_led_attr, _name, _mode, _show, _store, _led) \
	do {                                                                   \
		snprintf(_led_attr.name, NAME_MAX, _name);                  \
		_led_attr.attr =                                          \
			(struct device_attribute)__ATTR_NAME_PTR(              \
				_led_attr.name, _mode, _show, _store);        \
		_led_attr.led = _led; \
	} while (0)

#define SCD_RW_LED_ATTR(_led_attr, _name, _show, _store, _led) \
	SCD_LED_ATTR(_led_attr, _name, S_IRUGO | S_IWUSR,        \
		      _show, _store, _led)

struct scd_led_priv;

struct scd_led_dev {
	struct scd_led_attribute attr[SCD_LED_ATTR_COUNT];
	struct led_classdev cdev;
	char name[NAME_MAX];
	u32 led_on_mask;

	struct scd_led_priv *priv;
};

struct scd_led_priv {
	struct pci_dev *pci_dev;
	struct auxiliary_device *auxdev;

	void __iomem *mmio_csr;

	u32 id;
	u8 num_leds;
	struct mutex lock;
	struct scd_led_dev leds[0];
};

static u32 csr_read(void __iomem *reg_offset)
{
	return ioread32(reg_offset);
}

static void csr_write(void __iomem *reg_offset, u32 val)
{
	iowrite32(val, reg_offset);
}

static int brightness_set(struct led_classdev *led_cdev,
			  enum led_brightness value)
{
	u32 reg;
	struct scd_led_dev *ldev =
			container_of(led_cdev, struct scd_led_dev, cdev);
	struct scd_led_priv *priv = ldev->priv;

	mutex_lock(&priv->lock);

	reg = csr_read(priv->mmio_csr);
	if (value == 0) {
		reg &= ~(ldev->led_on_mask);
		reg &= ~(SCD_LED_INTENSITY_RED | SCD_LED_INTENSITY_GREEN | SCD_LED_INTENSITY_BLUE);
	} else {
		/*
		 * clear all the color bits before turning on the specific color.
		 */
		reg &= ~(SCD_LED_BLUE | SCD_LED_GREEN | SCD_LED_RED);
		reg |= ldev->led_on_mask;
		reg |= (SCD_LED_INTENSITY_RED | SCD_LED_INTENSITY_GREEN | SCD_LED_INTENSITY_BLUE);
	}
	csr_write(priv->mmio_csr, reg);

	mutex_unlock(&priv->lock);
	return 0;
}

static void scd_led_blink(struct led_classdev *led_cdev)
{
	struct scd_led_dev *ldev = container_of(led_cdev, struct scd_led_dev, cdev);

	led_blink_set(led_cdev, &ldev->cdev.blink_delay_on, &ldev->cdev.blink_delay_off);
}

static ssize_t store_trigger(
				struct device *dev,
				struct device_attribute *attr,
				const char *buf,
				size_t size)
{
	struct scd_led_attribute *led_attr = container_of(attr, struct scd_led_attribute, attr);
	struct scd_led_dev *ldev = led_attr->led;
	struct led_classdev *led_cdev = &ldev->cdev;
	char *nl;

	mutex_lock(&ldev->priv->lock);

	nl = strchr(buf, '\n');
	if (nl)
		*nl = '\0';

	if (strcmp(buf, "timer") == 0)
		scd_led_blink(led_cdev);

	mutex_unlock(&ldev->priv->lock);
	return size;
}

static ssize_t show_trigger(struct device *dev, struct device_attribute *attr, char *buf)
{
	return 0;
}

static ssize_t store_delay(
				struct device *dev,
				struct device_attribute *attr,
				const char *buf,
				size_t size)
{
	struct scd_led_attribute *led_attr = container_of(attr, struct scd_led_attribute, attr);
	struct led_classdev *led_cdev = &led_attr->led->cdev;
	struct scd_led_priv *priv = led_attr->led->priv;
	int res;
	long value;

	mutex_lock(&priv->lock);
	res = kstrtol(buf, 10, &value);
	if (res < 0)
		return res;

	if (!strcmp(led_attr->name, "delay_off"))
		led_cdev->blink_delay_off = value;
	else
		led_cdev->blink_delay_on = value;
	mutex_unlock(&priv->lock);
	return size;
}

static ssize_t show_delay(struct device *dev, struct device_attribute *attr, char *buf)
{
	struct scd_led_attribute *led_attr = container_of(attr, struct scd_led_attribute, attr);
	struct led_classdev *led_cdev = &led_attr->led->cdev;

	if (!strcmp(led_attr->name, "delay_off"))
		return sprintf(buf, "%d\n", led_cdev->blink_delay_off);
	return sprintf(buf, "%d\n", led_cdev->blink_delay_on);
}

static int scd_led_register(struct scd_led_dev *ldev)
{
	int ret;

	ret = devm_led_classdev_register(&ldev->priv->auxdev->dev, &ldev->cdev);
	if (ret) {
		dev_err(&ldev->priv->auxdev->dev, "could not register led: %d", ret);
		return ret;
	}
	dev_info(&ldev->priv->auxdev->dev, "%s @ %pS\n", ldev->name, ldev->priv->mmio_csr);

	SCD_RW_LED_ATTR(ldev->attr[0], "trigger", show_trigger, store_trigger, ldev);
	SCD_RW_LED_ATTR(ldev->attr[1], "delay_on", show_delay, store_delay, ldev);
	SCD_RW_LED_ATTR(ldev->attr[2], "delay_off", show_delay, store_delay, ldev);
	for (int i = 0; i < SCD_LED_ATTR_COUNT; i++) {
		ret = sysfs_create_file(&ldev->cdev.dev->kobj, &ldev->attr[i].attr.attr);
		if (ret) {
			dev_err(&ldev->priv->auxdev->dev,
				"could not create %s attribute for led: %d",
				ldev->attr[i].name,
				ret);
			return ret;
		}
	}
	return ret;
}

static int scd_led_init(struct scd_led_priv *priv,
			const char *name,
			const char *color,
			struct scd_led_dev *ldev)
{
	if (!strcmp(color, "yellow"))
		ldev->led_on_mask = SCD_LED_RED | SCD_LED_GREEN;
	else if (!strcmp(color, "blue"))
		ldev->led_on_mask = SCD_LED_BLUE;
	else if (!strcmp(color, "green"))
		ldev->led_on_mask = SCD_LED_GREEN;
	else if (!strcmp(color, "red"))
		ldev->led_on_mask = SCD_LED_RED;
	else
		return -EINVAL;

	snprintf(ldev->name, sizeof(ldev->name), "%s:%s:%s",
		 name, color, "status");

	ldev->priv = priv;
	ldev->cdev.name = ldev->name;
	ldev->cdev.brightness_set_blocking = brightness_set;
	ldev->cdev.default_trigger = "timer";

	return scd_led_register(ldev);
}

static int scd_leds_init(struct scd_led_priv *priv, const char *name)
{
	int ret = 0;
	const char *portColors[] = {"blue", "yellow"};
	const char *statusColors[] = {"red", "green", "blue", "yellow"};
	const char **colors;

	if (priv->num_leds == 2) colors = portColors;
	else colors = statusColors;

    for (int i = 0; i < priv->num_leds; ++i) {
		ret = scd_led_init(priv, name, colors[i], &priv->leds[i]);
        if (ret) return ret;
    }
    return 0;
}

static int scd_led_probe(struct auxiliary_device *auxdev,
			   const struct auxiliary_device_id *id)
{
	u8 num_leds;
	u32 reg, csr_addr;
	int ret;
	char led_name[NAME_MAX];
	struct resource *res;
	struct scd_led_priv *priv;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
			(struct fbiob_aux_adapter *)container_of(auxdev,
					struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;
	struct fbiob_led_data led_data = pdata->led_data;


	if (led_data.port_num > 0) num_leds = 2;
	else num_leds = 4;

	priv = devm_kzalloc(dev, sizeof(*priv) +
				num_leds * sizeof(priv->leds[0]),
				GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->num_leds = num_leds;

	dev_set_drvdata(dev, priv);

	csr_addr = pdata->csr_offset;
	res = devm_request_mem_region(dev, csr_addr,
					FBIOB_LED_BLK_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	priv->mmio_csr = devm_ioremap(dev, csr_addr,
					FBIOB_LED_BLK_SIZE);
	if (!priv->mmio_csr)
		return -ENOMEM;

	mutex_init(&priv->lock);
	priv->id = auxdev->id;
	priv->auxdev = auxdev;
	priv->pci_dev = to_pci_dev(dev->parent);

	/*
	* Set default color to blue if it's a port LED, no blinking.
	*/
	reg = csr_read(priv->mmio_csr);

	reg &= ~SCD_LED_MASK_ALL;

	if (led_data.port_num > 0)
		reg |= SCD_LED_BLUE;
	else
		reg |= SCD_LED_GREEN;

	csr_write(priv->mmio_csr, reg);

	/*
	* Register led for each color.
	*/
	if (led_data.port_num > 0) {
		sprintf(led_name, "port%d_led%d", led_data.port_num, led_data.led_idx);
	}
	else strcpy(led_name, pdata->id.name);

	ret = scd_leds_init(priv, led_name);

	if (ret)
		return ret;

	return 0;
}

static void scd_led_remove(struct auxiliary_device *auxdev) {
	struct scd_led_priv *priv = dev_get_drvdata(&auxdev->dev);

	for (int i = 0; i < priv->num_leds; ++i) {
		for (int j = 0; j < SCD_LED_ATTR_COUNT; ++j) {
			sysfs_remove_file(&priv->leds[i].cdev.dev->kobj, &priv->leds[i].attr[j].attr.attr);
		}
	}
}

static const struct auxiliary_device_id scd_led_ids[] = {
	{ .name = "scd.fan_led" },
	{ .name = "scd.port_led" },
	{ .name = "scd.psu_led" },
	{ .name = "scd.smb_led" },
	{ .name = "scd.sys_led" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_led_ids);

static struct auxiliary_driver scd_led_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_led_probe,
	.remove = scd_led_remove,
	.id_table = scd_led_ids,
};
module_auxiliary_driver(scd_led_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Driver for Arista SCD LEDs");
MODULE_AUTHOR("Facebook Inc.");
