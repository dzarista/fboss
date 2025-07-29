// SPDX-License-Identifier: GPL-2.0+
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

#include "fbiob-auxdev.h"
#include <linux/auxiliary_bus.h>
#include <linux/bitfield.h>
#include <linux/bits.h>
#include <linux/device.h>
#include <linux/hwmon.h>
#include <linux/module.h>
#include <linux/pci.h>

#define DRIVER_NAME "scd_adc"

#define ADC_THRESH_REG_OFFSET 0x10
#define ADC_VALUE_REG_OFFSET 0x20
#define ADC_INDEX_MASK GENMASK(3, 0)
#define ADC_VALUE_MASK GENMASK(11, 0)
#define ADC_OVER_THRESH_MASK GENMASK(27, 16)
#define ADC_UNDER_THRESH_MASK GENMASK(11, 0)

#define FAIRYWREN_SCD_PCI_SUBDEVICE_ID 0x0008
#define FAIRYWREN_NUM_ADC_RAILS 16
#define FAIRYWREN_SCALING_INT_MASK GENMASK(19, 16)
#define FAIRYWREN_SCALING_FRAC_MASK GENMASK(31, 24)

#define VIPER_SCD_PCI_SUBDEVICE_ID 0x0003
#define VIPER_NUM_ADC_RAILS 16
#define VIPER_SCALING_MASK GENMASK(19, 16)

#define FBIOB_ADC_BLK_SIZE 0x24

#define FAIRYWREN_ADC_LABELS                                                   \
	{                                                                      \
	"POS3V3_ALW", "POS2V5_BMC", "POS1V2_BMC", "POS1V0_BMC", "POS1V8_BMC",  \
	"POS0V96_I226", "POS12V", "POS5V0", "POS3V3_CPU", "POS2V5_VPP",        \
	"POS1V2", "POS1V0_MSW", "POS1V8_CPU", "POS1V0_VCC_PCIE",               \
	"POS1V05_CPU", "POS1V2_VDDQ"                                           \
	}

#define VIPER_ADC_LABELS                                                       \
	{                                                                      \
	"POS1V0_CP", "POS1V2_CP", "POS1V8_CP", "POS3V3_CP", "POS5V0_CP",       \
	"POS3V3_OPTICS", "POS12V_JE", "POS12V_PORT", "POS0V8_JE", "POS1V5_JE", \
	"POS1V8_JE", "POS2V5_JE", "POS0V75A_JE", "POS0V85C_JE", "POS0V9A_JE",  \
	"POS1V2_HBM"                                                           \
	}

#define SCD_ADC_CHAN_ATTRS                                                     \
	(HWMON_I_INPUT | HWMON_I_MIN | HWMON_I_MAX | HWMON_I_LABEL)

struct scd_adc_priv {
	struct pci_dev *pci_dev;
	struct device *dev;
	struct device *hwmon_dev;
	void __iomem *mmio_csr;
	struct mutex lock;
	u16 subsys_id;
	u8 num_rails;
};

static int convert_to_millivolts(u16 subsys_id, int raw_adc_num,
				 int scaling_int, int scaling_frac)
{
  /* To avoid floating point arithmetic in the kernel, the raw values are scaled
   * up and then truncated down to millivolts for a maximum of +- 1 mV
   * inaccuracy. Formulas differ per SCD and can be found in the corresponding
   * HWFS.
   */
	long long scaling_total;
	long long normalized_num;
	int millivolts;

	switch (subsys_id) {
	case FAIRYWREN_SCD_PCI_SUBDEVICE_ID:
		scaling_total = (long long)scaling_int * 256 + scaling_frac;
		normalized_num = (long long)raw_adc_num * scaling_total * 5 * 1000;
		millivolts = (normalized_num >> 21);
		return millivolts;
	case VIPER_SCD_PCI_SUBDEVICE_ID:
		normalized_num = (long long)raw_adc_num * (long long)scaling_int * 1000;
		millivolts = (normalized_num >> 12);
		return millivolts;
	default:
		return 0;
	}
}

static umode_t scd_adc_is_visible(const void *drvdata,
				  enum hwmon_sensor_types type, u32 attr,
				  int channel)
{
	if (type == hwmon_in) {
		switch (attr) {
		case hwmon_in_input:
		case hwmon_in_min:
		case hwmon_in_max:
		case hwmon_in_label:
			return 0444;
		default:
			return 0;
		}
	}
	return 0;
};

static int scd_adc_read(struct device *dev, enum hwmon_sensor_types type,
			u32 attr, int channel, long *val)
{
	int ret = 0;
	int scaling_int;
	int scaling_frac;
	struct scd_adc_priv *priv = dev_get_drvdata(dev);

	if (type != hwmon_in)
		return -EOPNOTSUPP;

	mutex_lock(&priv->lock);
	iowrite32((channel & ADC_INDEX_MASK), priv->mmio_csr);
	switch (priv->subsys_id) {
	case FAIRYWREN_SCD_PCI_SUBDEVICE_ID:
		scaling_int = FIELD_GET(FAIRYWREN_SCALING_INT_MASK,
			ioread32(priv->mmio_csr + ADC_VALUE_REG_OFFSET));
		scaling_frac = FIELD_GET(FAIRYWREN_SCALING_FRAC_MASK,
			ioread32(priv->mmio_csr + ADC_VALUE_REG_OFFSET));
		break;
	case VIPER_SCD_PCI_SUBDEVICE_ID:
		scaling_int = FIELD_GET(VIPER_SCALING_MASK,
			ioread32(priv->mmio_csr + ADC_VALUE_REG_OFFSET));
		scaling_frac = 0;
		break;
	default:
		ret = -EINVAL;
	}

	switch (attr) {
	case hwmon_in_input: {
		int raw_adc_val = FIELD_GET(ADC_VALUE_MASK,
			ioread32(priv->mmio_csr + ADC_VALUE_REG_OFFSET));
		*val = convert_to_millivolts(priv->subsys_id, raw_adc_val, scaling_int,
			scaling_frac);
		break;
	}
	case hwmon_in_min: {
		int raw_adc_under_thresh = FIELD_GET(ADC_UNDER_THRESH_MASK,
			ioread32(priv->mmio_csr + ADC_THRESH_REG_OFFSET));
		*val = convert_to_millivolts(priv->subsys_id, raw_adc_under_thresh,
			scaling_int, scaling_frac);
		break;
	}
	case hwmon_in_max: {
		int raw_adc_over_thresh = FIELD_GET(ADC_OVER_THRESH_MASK,
			ioread32(priv->mmio_csr + ADC_THRESH_REG_OFFSET));
		*val = convert_to_millivolts(priv->subsys_id, raw_adc_over_thresh,
			scaling_int, scaling_frac);
		break;
	}
	default:
		ret = -EOPNOTSUPP;
	}
	mutex_unlock(&priv->lock);
	return ret;
}

static int scd_adc_read_string(struct device *dev, enum hwmon_sensor_types type,
			       u32 attr, int channel, const char **str)
{
	struct scd_adc_priv *priv = dev_get_drvdata(dev);

	if (type != hwmon_in || attr != hwmon_in_label)
		return -EOPNOTSUPP;

	static const char *const fairywren_labels[FAIRYWREN_NUM_ADC_RAILS] = FAIRYWREN_ADC_LABELS;
	static const char *const viper_labels[VIPER_NUM_ADC_RAILS] = VIPER_ADC_LABELS;

	switch (priv->subsys_id) {
	case FAIRYWREN_SCD_PCI_SUBDEVICE_ID:
		*str = fairywren_labels[channel];
		break;
	case VIPER_SCD_PCI_SUBDEVICE_ID:
		*str = viper_labels[channel];
		break;
	default:
		*str = "Unknown Rail";
		break;
	}

	return 0;
}

static const struct hwmon_channel_info *const scd_adc_info[] = {
	HWMON_CHANNEL_INFO(
		in, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS,
		SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS,
		SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS,
		SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS,
		SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS, SCD_ADC_CHAN_ATTRS,
		SCD_ADC_CHAN_ATTRS),
	NULL};

static const struct hwmon_ops scd_adc_hwmon_ops = {
	.is_visible = scd_adc_is_visible,
	.read = scd_adc_read,
	.read_string = scd_adc_read_string
};

static const struct hwmon_chip_info scd_adc_chip_info = {
	.ops = &scd_adc_hwmon_ops,
	.info = scd_adc_info,
};

static int scd_adc_probe(struct auxiliary_device *auxdev,
			 const struct auxiliary_device_id *id)
{
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap = (struct fbiob_aux_adapter *)container_of(
		auxdev, struct fbiob_aux_adapter, auxdev);
	u32 adc_base_csr = aux_adap->data.csr_offset;

	struct scd_adc_priv *priv;
	struct resource *res;
	char *adc_dev_name;
	int ret;
	u16 subsys_id;

	priv = devm_kzalloc(dev, sizeof(struct scd_adc_priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->dev = dev;
	priv->pci_dev = to_pci_dev(dev->parent);

	res = devm_request_mem_region(dev, adc_base_csr, FBIOB_ADC_BLK_SIZE,
				DRIVER_NAME);
	if (!res)
		return -EBUSY;

	priv->mmio_csr = devm_ioremap(dev, adc_base_csr, FBIOB_ADC_BLK_SIZE);
	if (!priv->mmio_csr)
		return -ENOMEM;

	ret = pci_read_config_word(priv->pci_dev, PCI_SUBSYSTEM_ID, &subsys_id);
	priv->subsys_id = subsys_id;
	switch (subsys_id) {
	case FAIRYWREN_SCD_PCI_SUBDEVICE_ID:
		priv->num_rails = FAIRYWREN_NUM_ADC_RAILS;
		adc_dev_name = devm_kasprintf(dev, GFP_KERNEL, "SCM_ADC");
		break;
	case VIPER_SCD_PCI_SUBDEVICE_ID:
		priv->num_rails = VIPER_NUM_ADC_RAILS;
		adc_dev_name = devm_kasprintf(dev, GFP_KERNEL, "SMB_ADC");
		break;
	default:
		ret = -EINVAL;
		dev_err(dev, "unsupported pci device with susbsys_id=%d\n", subsys_id);
	return ret;
	}

	mutex_init(&priv->lock);
	priv->hwmon_dev = devm_hwmon_device_register_with_info(
		dev, adc_dev_name, priv, &scd_adc_chip_info, NULL);

	if (IS_ERR(priv->hwmon_dev)) {
		ret = PTR_ERR(priv->hwmon_dev);
		dev_err(dev, "failed to register hwmon device, error=%d\n", ret);
		return ret;
}

	dev_info(dev, "scd_adc (base=0x%x) initialized successfully\n", adc_base_csr);
	return 0;
}

static const struct auxiliary_device_id scd_adc_ids[] = {
	{.name = SCD_MODULE_NAME ".adc"},
	{},
};

MODULE_DEVICE_TABLE(auxiliary, scd_adc_ids);

static struct auxiliary_driver scd_adc_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_adc_probe,
	.id_table = scd_adc_ids
};

module_auxiliary_driver(scd_adc_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Driver for Arista DSF ADC Rails");
MODULE_AUTHOR("Arista Networks");
MODULE_VERSION(BSP_VERSION);
