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
#include <linux/pci.h>

#include "fbiob-auxdev.h"

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

struct scd_led_priv;

struct scd_led_dev {
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
		 * clear all the color bits before turning on the specific
		 * color.
		 */
		reg &= ~(SCD_LED_BLUE | SCD_LED_GREEN | SCD_LED_RED);
		reg |= ldev->led_on_mask;
		reg |= (SCD_LED_INTENSITY_RED | SCD_LED_INTENSITY_GREEN | SCD_LED_INTENSITY_BLUE);
	}
	csr_write(priv->mmio_csr, reg);

	mutex_unlock(&priv->lock);
	return 0;
}

static int scd_led_init(struct scd_led_priv *priv,
			const char *name,
			const char *color,
			struct scd_led_dev *ldev)
{
	if (!strcmp(color, "amber"))
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

	dev_info(&priv->auxdev->dev, "%s @ %pS\n", name, priv->mmio_csr);

	return devm_led_classdev_register(&priv->auxdev->dev, &ldev->cdev);
}

static int scd_leds_init(struct scd_led_priv *priv, const char *name)
{
	int ret = 0;
	const char *portColors[] = {"blue", "amber"};
	const char *statusColors[] = {"red", "green", "blue", "amber"};
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
	if (led_data.port_num > 0)
		sprintf(led_name, "%s_port%d_led%d", pdata->id.name, led_data.port_num,
			 led_data.led_idx);
	else sprintf(led_name, "%s%d", pdata->id.name, led_data.led_idx);

	ret = scd_leds_init(priv, led_name);

	if (ret)
		return ret;

	return 0;
}

static const struct auxiliary_device_id scd_led_ids[] = {
	{ .name = "scd.osfp_led" },
	{ .name = "scd.qsfp_led" },
	{ .name = "scd.status_led" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_led_ids);

static struct auxiliary_driver scd_led_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_led_probe,
	.id_table = scd_led_ids,
};
module_auxiliary_driver(scd_led_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Driver for Arista SCD LEDs");
MODULE_AUTHOR("Facebook Inc.");