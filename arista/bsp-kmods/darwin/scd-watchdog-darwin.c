// SPDX-License-Identifier: GPL-2.0+
/*
 * Copyright (C) 2021 Facebook Inc.
 *
 */

#include <linux/kernel.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/watchdog.h>

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

static int scd_wdt_start(struct watchdog_device *wdd)
{
	return 0;
}

static int scd_wdt_stop(struct watchdog_device *wdd)
{
	return 0;
}

static int scd_wdt_ping(struct watchdog_device *wdd)
{
	return 0;
}

static const struct watchdog_ops scd_wdt_ops = {
	.start = scd_wdt_start,
	.stop = scd_wdt_stop,
	.ping = scd_wdt_ping,
	.owner = THIS_MODULE,
};

static const struct watchdog_info scd_wdt_info = {
	.options = WDIOF_KEEPALIVEPING | WDIOF_MAGICCLOSE | WDIOF_SETTIMEOUT,
	.identity = KBUILD_MODNAME,
};

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
	int err;
	struct resource *res;
	void __iomem *mmio_csr;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
			(struct fbiob_aux_adapter *)container_of(auxdev,
					struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;
	struct watchdog_device *wdd;

	wdd = devm_kzalloc(dev, sizeof(*wdd), GFP_KERNEL);

	res = devm_request_mem_region(dev, pdata->csr_offset,
					  SCD_WDT_MEM_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	mmio_csr = devm_ioremap(dev, pdata->csr_offset, SCD_WDT_MEM_SIZE);
	if (!mmio_csr)
		return -ENOMEM;

	scd_wdt_disable(mmio_csr);
	dev_info(dev, "disabled watchdog at address 0x%lx\n", pdata->csr_offset);

	// Create dummy /dev endpoints to support PM
	wdd->info = &scd_wdt_info;
	wdd->ops = &scd_wdt_ops;
	wdd->parent = dev;
	wdd->timeout = SCD_WDT_TIMEOUT_MASK;
	wdd->max_timeout = SCD_WDT_TIMEOUT_MASK;

	err = devm_watchdog_register_device(dev, wdd);
	if (err) {
		dev_err(dev, "watchdog_register_device failed, ret=%d\n", err);
		return err;
	}

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
