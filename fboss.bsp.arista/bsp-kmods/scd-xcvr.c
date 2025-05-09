/* Copyright (c) 2020 Arista Networks, Inc.
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

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/delay.h>

#include "scd-xcvr.h"
#include "fbiob-auxdev.h"

#define DRIVER_NAME "scd-xcvr"

static u32 csr_read(void __iomem *reg_offset)
{
	return ioread32(reg_offset);
}

static void csr_write(void __iomem *reg_offset, u32 val)
{
	iowrite32(val, reg_offset);
}

static u32 scd_xcvr_read_register(const struct scd_xcvr_attribute *gpio)
{
	struct scd_xcvr *xcvr = gpio->xcvr;
	int i;
	u32 reg;

	reg = csr_read(gpio->xcvr->addr);
	for (i = 0; i < XCVR_ATTR_MAX_COUNT; i++) {
		if (xcvr->attr[i].clear_on_read) {
			xcvr->attr[i].clear_on_read_value =
				xcvr->attr[i].clear_on_read_value |
				!!(reg & (1 << i));
		}
	}
	return reg;
}

static ssize_t attribute_xcvr_get(struct device *dev,
				  struct device_attribute *devattr, char *buf)
{
	struct scd_xcvr_attribute *gpio = to_scd_xcvr_attr(devattr);
	u32 res;
	u32 reg;

	reg = scd_xcvr_read_register(gpio);
	res = !!(reg & (1 << gpio->bit));
	res = (gpio->active_low) ? !res : res;
	if (gpio->clear_on_read) {
		res = gpio->clear_on_read_value | res;
		gpio->clear_on_read_value = 0;
	}
	return sprintf(buf, "%u\n", res);
}

static ssize_t attribute_xcvr_set(struct device *dev,
				  struct device_attribute *devattr,
				  const char *buf, size_t count)
{
	const struct scd_xcvr_attribute *gpio = to_scd_xcvr_attr(devattr);
	long value;
	int res;
	u32 reg;

	res = kstrtol(buf, 10, &value);
	if (res < 0)
		return res;

	if (value != 0 && value != 1)
		return -EINVAL;

	reg = scd_xcvr_read_register(gpio);
	if (gpio->active_low) {
		if (value)
			reg &= ~(1 << gpio->bit);
		else
			reg |= 1 << gpio->bit;
	} else {
		if (value)
			reg |= 1 << gpio->bit;
		else
			reg &= ~(1 << gpio->bit);
	}
	csr_write(gpio->xcvr->addr, reg);

	return count;
}

struct gpio_cfg {
	u32 bitpos;
	bool read_only;
	bool active_low;
	bool clear_on_read;
	const char *name;
};

/*
 * Meta qsfp_service expects the following:
 *
 * present: 0 = present,  1 = not present
 * reset:   0 = in reset, 1 = out of reset
 *
 * The gpio definitions below have been adjusted to match these expectations.
 */

static const struct gpio_cfg gpios[] = {
	{ 0, true, true, false, "interrupt" },
	{ 2, true, false, false, "present" },
	{ 3, true, false, true, "interrupt_changed" },
	{ 5, true, false, true, "present_changed" },
	{ 6, false, false, false, "lp_mode" },
	{ 7, false, true, false, "reset" },
	{ 8, false, true, false, "modsel" },
};

static int scd_xcvr_register(struct scd_xcvr *xcvr, const struct gpio_cfg *cfgs,
			     size_t gpio_count)
{
	struct gpio_cfg gpio;
	int res;
	size_t i;
	size_t name_size;
	char name[GPIO_NAME_MAX_SZ];

	for (i = 0; i < gpio_count; i++) {
		gpio = cfgs[i];
		name_size = strlen(xcvr->name) + strlen(gpio.name) + 2;
		BUG_ON(name_size > GPIO_NAME_MAX_SZ);
		snprintf(name, name_size, "%s_%s", xcvr->name, gpio.name);
		if (gpio.read_only) {
			SCD_RO_XCVR_ATTR(xcvr->attr[gpio.bitpos], name,
					 name_size, xcvr, gpio.bitpos,
					 gpio.active_low, gpio.clear_on_read);
		} else {
			SCD_RW_XCVR_ATTR(xcvr->attr[gpio.bitpos], name,
					 name_size, xcvr, gpio.bitpos,
					 gpio.active_low, gpio.clear_on_read);
		}
		res = sysfs_create_file(&xcvr->priv->auxdev->dev.kobj,
					&xcvr->attr[gpio.bitpos].dev_attr.attr);
		if (res) {
			dev_err(&xcvr->priv->auxdev->dev,
				"could not create %s attribute for xcvr: %d",
				xcvr->attr[gpio.bitpos].dev_attr.attr.name,
				res);
			return res;
		}
	}

	return 0;
}

static void scd_xcvr_unregister(struct scd_xcvr *xcvr)
{
	int i;

	for (i = 0; i < XCVR_ATTR_MAX_COUNT; i++) {
		if (xcvr->attr[i].xcvr) {
			sysfs_remove_file(&xcvr->priv->auxdev->dev.kobj,
					  &xcvr->attr[i].dev_attr.attr);
		}
	}
}

static void scd_xcvr_remove(struct auxiliary_device *auxdev)
{
	struct scd_xcvr_priv *priv = dev_get_drvdata(&auxdev->dev);
	scd_xcvr_unregister(&priv->xcvr);
	dev_info(&auxdev->dev, "xcvr port %u removed\n", priv->xcvr.port_num);
}

static int scd_xcvr_init(struct scd_xcvr_priv *priv)
{
	int ret;
	char *prefix = NULL;
	const struct gpio_cfg *cfgs;
	size_t gpio_cnt;
	struct scd_xcvr *dev = &priv->xcvr;

	prefix = "xcvr";
	cfgs = gpios;
	gpio_cnt = ARRAY_SIZE(gpios);

	dev_info(&priv->auxdev->dev, "%s %u @ %pS\n", prefix, dev->port_num,
		   priv->mmio_csr);
	ret = snprintf(dev->name, sizeof_field(typeof(*dev), name), "%s%u",
		       prefix, dev->port_num);
	if (ret < 0)
		return ret;

	dev->addr = priv->mmio_csr;
	dev->priv = priv;

	ret = scd_xcvr_register(dev, cfgs, gpio_cnt);
	if (ret)
		return ret;

	return 0;
}

static int scd_xcvr_probe(struct auxiliary_device *auxdev,
			   const struct auxiliary_device_id *id)
{
	int ret;
	u32 csr_addr;
	struct resource *res;
	struct scd_xcvr_priv *priv;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
				(struct fbiob_aux_adapter *)container_of(auxdev,
						struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;
	struct fbiob_xcvr_data xcvr_data = pdata->xcvr_data;

	priv = devm_kzalloc(dev, sizeof(*priv) + sizeof(priv->xcvr),
			    GFP_KERNEL);
	if (priv == NULL)
		return -ENOMEM;
	dev_set_drvdata(dev, priv);

	csr_addr = pdata->csr_offset;
	res = devm_request_mem_region(dev, csr_addr,
					FBIOB_XCVR_BLK_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	priv->mmio_csr = devm_ioremap(dev, csr_addr, FBIOB_XCVR_BLK_SIZE);
	if (!priv->mmio_csr)
		return -ENOMEM;

	mutex_init(&priv->lock);
	priv->id = auxdev->id;
	priv->auxdev = auxdev;
	priv->pci_dev = to_pci_dev(dev->parent);
	priv->xcvr.port_num = xcvr_data.port_num;

	ret = scd_xcvr_init(priv);
	if (ret)
		goto fail_xcvr;
	return 0;

fail_xcvr:
	scd_xcvr_remove(auxdev);
	return ret;
}

static const struct auxiliary_device_id scd_xcvr_ids[] = {
	{ .name = "scd.xcvr_ctrl" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_xcvr_ids);

static struct auxiliary_driver scd_xcvr_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_xcvr_probe,
	.remove = scd_xcvr_remove,
	.id_table = scd_xcvr_ids,
};

module_auxiliary_driver(scd_xcvr_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("SCD Xcvr driver");
MODULE_VERSION(BSP_VERSION);