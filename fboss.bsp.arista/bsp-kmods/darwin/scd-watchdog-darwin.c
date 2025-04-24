// SPDX-License-Identifier: GPL-2.0+
/*
 * Copyright (C) 2021 Facebook Inc.
 *
 */

#include <linux/kernel.h>
#include <linux/io.h>
#include <linux/module.h>

#include "fbiob-auxdev.h"

#define SCD_WDT_MEM_SIZE		4

/*
 * There are 2 watchdogs in Darwin SCD FPGA (@0x120 and @0x304), and we
 * decide to disable both of them to prevent unexpected x86 reboots.
 */
#define SCD_WDT_ENABLE			BIT(31)
#define SCD_WDT_ACTION_MASK		(3 << 29)
#define SCD_WDT_PRE_TIMEOUT_MASK	(0xFFF << 16)
#define SCD_WDT_TIMEOUT_MASK		0xFFFF

static void scd_wdt_disable(void __iomem *mmio_csr)
{
	u32 val;
	u32 mask = (SCD_WDT_ENABLE | SCD_WDT_ACTION_MASK |
		    SCD_WDT_PRE_TIMEOUT_MASK | SCD_WDT_TIMEOUT_MASK);

	val = ioread32(mmio_csr);
	val &= ~mask;
	iowrite32(val, mmio_csr);
}

static int scd_wdt_probe(struct auxiliary_device *auxdev,
			 const struct auxiliary_device_id *id)
{
	struct resource *res;
	void __iomem *mmio_csr;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
			(struct fbiob_aux_adapter *)container_of(auxdev,
					struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;

	res = devm_request_mem_region(dev, pdata->csr_offset,
				      SCD_WDT_MEM_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	mmio_csr = devm_ioremap(dev, pdata->csr_offset, SCD_WDT_MEM_SIZE);
	if (!mmio_csr)
		return -ENOMEM;

	scd_wdt_disable(mmio_csr);

	dev_info(dev, "disabled watchdog at address 0x%lx\n", pdata->csr_offset);
	return 0;
}

static const struct auxiliary_device_id scd_watchdog_ids[] = {
	{ .name = "scd.watchdog_darwin"},
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_watchdog_ids);

static struct auxiliary_driver scd_wdt_driver = {
	.probe = scd_wdt_probe,
	.driver = {
		.name = "scd_watchdog_darwin",
	},
	.id_table = scd_watchdog_ids,
};
module_auxiliary_driver(scd_wdt_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Driver for Arista SCD based Watchdog");
MODULE_AUTHOR("Facebook Inc.");
