// SPDX-License-Identifier: GPL-2.0+
// Copyright (c) Meta Platforms, Inc. and affiliates.

#include <linux/auxiliary_bus.h>
#include <linux/device.h>
#include <linux/errno.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/regmap.h>
#include <linux/bits.h>

#include "fbiob-auxdev.h"
#include "regbit-sysfs.h"

#define DRIVER_NAME "scd_info"

#define FPGA_INFO_MEM_SIZE	4

#define FPGA_VER_REG 0
#define FPGA_VER_OFFSET 16
#define FPGA_VER_BITLEN 16

#define FPGA_SUB_VER_REG 0x100
#define FPGA_SUB_VER_OFFSET 0
#define FPGA_SUB_VER_BITLEN 8

static
ssize_t fpga_fw_ver_show(struct device *dev,
			 struct device_attribute *attr,
			 char *buf)
{
	int ret;
	u32 val;
	struct regmap *regmap;
	u16 major_rev;
	u8 minor_rev;
	u32 ver_mask, subver_mask;

	regmap = dev_get_regmap(dev, NULL);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	ret = regmap_read(regmap, FPGA_VER_REG, &val);
	if (ret)
		return ret;

	ver_mask = GENMASK(FPGA_VER_BITLEN - 1, 0);
	subver_mask = GENMASK(FPGA_SUB_VER_BITLEN - 1, 0);


	major_rev = (u16)((val >> FPGA_VER_OFFSET) & ver_mask);
	minor_rev = (u8)((val >> FPGA_SUB_VER_OFFSET) &
			    subver_mask);
	return sprintf(buf, "%u.%u\n", major_rev, minor_rev);
}

struct regbit_sysfs_config sysfs_files[] = {
	{
		.name = "fw_ver",
		.mode = REGBIT_FMODE_RO,
		.show_func = fpga_fw_ver_show,
	},
};

static int scd_info_probe(struct auxiliary_device *auxdev,
			   const struct auxiliary_device_id *id)
{
	int ret;
	struct resource *res;
	void __iomem *mmio_base;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
		(struct fbiob_aux_adapter *)container_of(auxdev,
				struct fbiob_aux_adapter, auxdev);
	u32 bus_addr = aux_adap->data.csr_offset;

	res = devm_request_mem_region(dev, bus_addr, FPGA_INFO_MEM_SIZE,
					auxdev->name);
	if (!res) {
		dev_err(dev, "failed to request mem_region (0x%x-0x%x)\n",
			bus_addr, bus_addr + FPGA_INFO_MEM_SIZE - 1);
		return -EBUSY;
	}

	mmio_base = devm_ioremap(dev, bus_addr, FPGA_INFO_MEM_SIZE);
	if (!mmio_base)
		return -ENOMEM;

	ret = regbit_sysfs_init_mmio(dev, mmio_base, sysfs_files,
				      ARRAY_SIZE(sysfs_files));
	if (ret) {
		dev_err(dev, "failed to initizlize regbit_sysfs, error=%d\n",
			ret);
		return ret;
	}

	dev_info(dev, "fpga_info (base=0x%x) initialized successfully\n",
		bus_addr);
	return 0;
}

static const struct auxiliary_device_id scd_info_ids[] = {
	{.name = SCD_MODULE_NAME".fpga_info_iob"},
	{.name = SCD_MODULE_NAME".fpga_info_dom"},
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_info_ids);

static struct auxiliary_driver fboss_iob_info_driver = {
	.driver = {
		.name = "scd_info",
	},
	.probe = scd_info_probe,
	.id_table = scd_info_ids,
};
module_auxiliary_driver(fboss_iob_info_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Scott Smith <smithscott@meta.com>");
MODULE_DESCRIPTION("Meta SCD Info Driver");
MODULE_VERSION(BSP_VERSION);
