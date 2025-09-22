/*
 * Copyright (c) 2006-2024 Arista Networks, Inc.  All rights reserved.
 * Arista Networks, Inc. Confidential and Proprietary.
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

/*
 * SCD driver.
 *
 * The driver is designed for SCD FPGAs and CPU CPLDs.
 *
 * When SCD or CPU CPLD is detected, the driver initializes the device and
 * maps its memory region 0 into virtual memory.
 *
 */

#include <linux/bits.h>
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/version.h>

#include "fbiob-auxdev.h"
#include "fbiob-cdev.h"
#include "scratchpad-bits.h"
#include "scd-reload-cause-pci.h"

#define REG_BLK_SIZE			4
#define REG_MAX_BITSIZE			32
#define MAX_NUM_REGS			10

#define SCD_PCI_VENDOR_ID		0x3475
#define SCD_PCI_DEVICE_ID		0x0001
#define DARWIN_SCD_PCI_SUBDEVICE_ID	0x0002
#define VIPER_SCD_PCI_SUBDEVICE_ID	0x0003
#define BLACKCOMB_SCD0_PCI_SUBDEVICE_ID	0x0004
#define BLACKCOMB_SCD1_PCI_SUBDEVICE_ID	0x0005
#define BLACKCOMB_SCD2_PCI_SUBDEVICE_ID	0x0006
#define BLACKCOMB_SCD3_PCI_SUBDEVICE_ID	0x0007
#define FAIRYWREN_SCD_PCI_SUBDEVICE_ID	0x0008
#define QUICKSILVER_SCD_PCI_SUBDEVICE_ID	0x0009
#define SCD_BAR_REGS			0
#define SCD_BAR_1			1
#define SCD_MAGIC			0xdeadbeef
#define SCD_FPGA_REV_MASK		0xffff0000
#define SCD_BOARD_REV_MASK		0xfff

#define RECONFIG_PCI_SUBSYSTEM_ID	0x14
#define RECONFIG_STATE_BAR_VALUE	0xdeadface


#define FPGA_VER_REG 0x100
#define FPGA_VER_OFFSET 16
#define FPGA_VER_NUM_BITS 16

#define FPGA_SUB_VER_REG 0x100
#define FPGA_SUB_VER_OFFSET 0
#define FPGA_SUB_VER_NUM_BITS 8

#define ASSERT(expr)                                                           \
	do {                                                                   \
		if (unlikely(!(expr)))                                         \
			printk(KERN_ERR                                        \
			       "Assertion failed! %s,%s,%s,line=%d (%s:%d)\n", \
			       #expr, __FILE__, __FUNCTION__, __LINE__,        \
			       current->comm, current->pid);                   \
	} while (0)

struct scd_driver_cb {
	int (*enable)(struct pci_dev *dev);
	void (*disable)(struct pci_dev *dev);
};

struct scd_reg {
	u32 offset;
	bool valid;
	void __iomem *mem;
};

struct regbit_sysfs_entry {
	const char *prefix;
	const char *name;
	u32 reg_offset;
	u32 bit_offset;
	u32 bit_len;
};

struct scd_dev_priv {
	struct pci_dev *pdev;
	resource_size_t csr_bus_addr;
	size_t mem_len;
	void __iomem *localbus;
	unsigned int magic;
	struct scd_reg sysfs_reg_table[MAX_NUM_REGS];
	struct scd_reg *sysfs_reg_end;
	struct attribute_group *sysfs_attr_group;
	struct regbit_sysfs_entry *regbit_sysfs_table;
	u32 scd_revision;
	bool is_reconfig;

	const struct scd_driver_cb *driver_cb;

	u32 auxbus_initialized:1;
	u32 cdev_initialized:1;
	u32 sysfs_initialized:1;

	u32 version_reg;

	/* Container of all the child auxiliary devices. */
	struct fbiob_aux_bus aux_bus;

	/* Character device for auxdev handling from user space. */
	struct fbiob_cdev_desc cdev_desc;
};

/*
 * XXX Special settings for the ROOK CPU CPLD on Darwin:
 *   - ROOK CPLD is a LPC device, and the driver uses the LPC-ISA bridge
 *     available in the AMD-Kabini chip as a PCI device.
 *   - The PCI vid:pid (8086:6f76) is "borrowed" from Intel.
 *   - DO NOT include 8086:6f76 in the driver's static ID table, because
 *     the driver may claim Intel 8086:6f76 devices on some Xeon platforms
 *     unexpectedly.
 *     To manually bind the driver to ROOK CPU CPLD, please run:
 *       echo "8086 6f76" > /sys/bus/pci/drivers/scd/new_id
 *   - The memory and irq resources are pre-allocated in Darwin, and below
 *     module parameters are just for debugging purposes.
 *       > scd.lpc_res_addr - beginning of the LPC physical memory
 *       > scd.lpc_res_size - size of the LPC block, in 4K increments
 *       > scd.lpc_irq - assigned interrupt number
 */

static struct pci_device_id scd_lpc_table[] = {
	{ PCI_DEVICE(PCI_VENDOR_ID_INTEL, 0x6f76) },
	{ 0 },
};

static unsigned long lpc_res_addr = 0xb0000000;
module_param(lpc_res_addr, long, 0);
MODULE_PARM_DESC(lpc_res_addr, "physical address of LPC resource");

static int lpc_res_size = 0x10000;
module_param(lpc_res_size, int, 0);
MODULE_PARM_DESC(lpc_res_size, "size of LPC resource");

static int lpc_irq = 7;
module_param(lpc_irq, int, 0);
MODULE_PARM_DESC(lpc_irq, "interrupt of LPC SCD");

/* Lock to protect CPLD scratchpad register. Each register bit acts as a flag -
   hence the register might be updated at different places */
static DEFINE_MUTEX(scratchpad_mutex);

/* fpga_major_rev_show() and fpga_minor_rev_show() reads the version register value
   cached in pci private data structure instead of directly accessing the registers.
   The revision register is managed by scd_info driver and scd driver reads the
   register only once during probe. */
static ssize_t fpga_major_rev_show(struct device *dev,
				   struct device_attribute *attr, char *buf)
{
	struct scd_dev_priv *priv = dev_get_drvdata(dev);
	u32 version_reg = priv->version_reg;
	u16 major_rev;
	u32 major_rev_mask;

	major_rev_mask = GENMASK(FPGA_VER_NUM_BITS - 1, 0);
	major_rev = (u16)((version_reg >> FPGA_VER_OFFSET) & major_rev_mask);
	return sprintf(buf, "%u\n", major_rev);
}

static ssize_t fpga_minor_rev_show(struct device *dev,
				   struct device_attribute *attr, char *buf)
{
	struct scd_dev_priv *priv = dev_get_drvdata(dev);
	u32 version_reg = priv->version_reg;
	u8 minor_rev;
	u32 minor_rev_mask;

	minor_rev_mask = GENMASK(FPGA_SUB_VER_NUM_BITS - 1, 0);
	minor_rev = (u8)((version_reg >> FPGA_SUB_VER_OFFSET) & minor_rev_mask);
	return sprintf(buf, "%u\n", minor_rev);
}

static
u32 scd_read_register(struct pci_dev *pdev, struct scd_reg *reg)
{
	u32 res = 0;
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);

	ASSERT(priv);
	ASSERT(reg->mem);
	ASSERT(reg->offset < priv->mem_len);
	if (priv) {
		res = ioread32(reg->mem);
	}
	dev_dbg(&pdev->dev, "io:read 0x%04x => 0x%08x", reg->offset, res);
	return res;
}

static
void scd_write_register(struct pci_dev *pdev, struct scd_reg *reg, u32 val)
{
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);

	ASSERT(priv);
	ASSERT(reg->mem);
	ASSERT(reg->offset < priv->mem_len);
	dev_dbg(&pdev->dev, "io:write 0x%04x <= 0x%08x", reg->offset, val);
	if (priv) {
		iowrite32(val, reg->mem);
	}
}

static int scd_sysfs_regs_init(struct scd_dev_priv *priv)
{
	struct regbit_sysfs_entry *sysfs;
	struct scd_reg *reg;
	bool reg_exists;
	struct resource *res;
	struct device *dev = &priv->pdev->dev;

	priv->sysfs_reg_end = priv->sysfs_reg_table + MAX_NUM_REGS;

	// Populate register information based on defined sysfs attrs.
	for (sysfs = priv->regbit_sysfs_table; sysfs->name != NULL; sysfs++) {
		reg_exists = false;
		for (reg = priv->sysfs_reg_table;
		     reg < priv->sysfs_reg_end && reg->valid;
		     reg++) {
			if (reg->offset == sysfs->reg_offset) {
				reg_exists = true;
				break;
			}
		}
		if (reg == priv->sysfs_reg_end) {
			dev_err(dev, "defined registers exceed max\n");
			return -ENXIO;
		}
		if (!reg_exists) {
			reg->offset = sysfs->reg_offset;
			reg->valid = true;
		}
	}

	// Map memory for all registers managed by this device.
	for (reg = priv->sysfs_reg_table;
	     reg < priv->sysfs_reg_end && reg->valid;
	     reg++) {
		res = devm_request_mem_region(
			dev, priv->csr_bus_addr + reg->offset,
			REG_BLK_SIZE, SCD_MODULE_NAME);
		if (!res) {
			dev_err(dev, "cannot request PCI memory region\n");
			return -EBUSY;
		}

		reg->mem = devm_ioremap(
			dev, priv->csr_bus_addr + reg->offset,
			REG_BLK_SIZE);
		if (!reg->mem) {
			dev_err(dev, "cannot remap PCI memory region\n");
			return -ENOMEM;
		}
	}

	return 0;
}

static void scd_sysfs_regs_destroy(struct scd_dev_priv *priv)
{
	struct scd_reg *reg;

	for (reg = priv->sysfs_reg_table; reg < priv->sysfs_reg_end; reg++) {
		reg->offset = 0;
		reg->valid = 0;
		reg->mem = NULL;
	}

	priv->sysfs_reg_end = NULL;
}

static struct scd_reg *scd_reg_at_offset(struct scd_dev_priv *priv, u32 offset)
{
	struct scd_reg *reg;

	for (reg = priv->sysfs_reg_table;
	     reg < priv->sysfs_reg_end && reg->valid;
	     reg++) {
		if (reg->offset == offset) {
			return reg;
		}
	}

	return NULL;
}

static int scd_read_regbit(struct device *dev,
						   u32 reg_offset,
						   u32 bit_len,
						   u32 bit_offset,
						   u32 *data)
{
	u32 mask;
	struct scd_reg *reg;
	struct scd_dev_priv *priv = dev_get_drvdata(dev);
	reg = scd_reg_at_offset(priv, reg_offset);
	if (!reg)
		return -ENODEV;

	*data = scd_read_register(priv->pdev, reg);
	mask = GENMASK(bit_len - 1, 0);
	*data = (*data >> bit_offset) & mask;
	return 0;
}

static ssize_t regbit_sysfs_read(struct device *dev,
				 struct device_attribute *dattr, bool updatebuf,
				 char *buf, u32 *regval)
{
	int ret;
	u32 data;
	struct attribute *attr = &dattr->attr;
	struct scd_dev_priv *priv = dev_get_drvdata(dev);
	struct regbit_sysfs_entry *entry = priv->regbit_sysfs_table;

	if (entry == NULL)
		return -ENOENT;

	for (; entry->name != NULL; entry++) {
		if (strcmp(entry->name, attr->name) == 0) {
			ret = scd_read_regbit(dev, entry->reg_offset,
				entry->bit_len, entry->bit_offset, &data);
			if (ret)
				continue;
			if (updatebuf) {
				if (entry->bit_len == 1)
					return sprintf(buf, "%d\n", data);
				return sprintf(buf, "0x%x\n", data);
			} else {
				*regval = data;
				return 0;
			}
		}
	}

	return -ENOENT;
}

static ssize_t sat_cpld_fw_ver_show(struct device *dev,
				 struct device_attribute *dattr, char *buf)
{
	ssize_t ret;
	u32 data;
	u32 fw_ver;
	u32 fw_sub_ver;

	ret = regbit_sysfs_read(dev, dattr, false, NULL, &data);
	if (ret) {
		return ret;
	} else {
		fw_ver = (data & 0xFF00) >> 8;
		fw_sub_ver = data & 0xFF;
		return sprintf(buf, "%u.%u\n", fw_ver, fw_sub_ver);
	}
}

static ssize_t regbit_sysfs_show(struct device *dev,
				 struct device_attribute *dattr, char *buf)
{
	return regbit_sysfs_read(dev, dattr, true, buf, NULL);
}

static ssize_t regbit_sysfs_store(struct device *dev,
				  struct device_attribute *dattr,
				  const char *buf, size_t count)
{
	u32 data, mask, input;
	struct attribute *attr = &dattr->attr;
	struct scd_dev_priv *priv = dev_get_drvdata(dev);
	struct regbit_sysfs_entry *entry = priv->regbit_sysfs_table;
	struct scd_reg *reg;

	if (entry == NULL)
		return -ENOENT;

	for (; entry->name != NULL; entry++) {
		if (strcmp(entry->name, attr->name))
			continue;

		reg = scd_reg_at_offset(priv, entry->reg_offset);
		if (!reg)
			continue;

		input = (u32)simple_strtoul(buf, NULL, 0);
		mask = GENMASK(entry->bit_len - 1, 0);
		if (input & ~mask)
			return -EINVAL;

		/* If we're writing all register bits then there's no need to read the
		 * current register value first.
		 */
		if (entry->bit_len != REG_MAX_BITSIZE) {
			data = scd_read_register(priv->pdev, reg);
			data &= ~(mask << entry->bit_offset);
			data |= (input << entry->bit_offset);
		} else {
			data = input;
		}
		scd_write_register(priv->pdev, reg, data);
		return count;
	}

	return -ENOENT;
}

static void scratchpad_lock(void)
{
	mutex_lock(&scratchpad_mutex);
}

static void scratchpad_unlock(void)
{
	mutex_unlock(&scratchpad_mutex);
}

static void print_reload_cause_info(struct scd_dev_priv *priv)
{
	struct mapped_register *reload_cause_reg_map;
	size_t reload_cause_reg_count;
	size_t reload_cause_reg_loop;
	void __iomem *scratchpad_map;
	struct resource *res;
	u32 scratchpad_val;
	bool power_cycle_detected = false;
	int op_status;

	get_reload_cause_register_map(&reload_cause_reg_map, &reload_cause_reg_count);
	for (reload_cause_reg_loop = 0; reload_cause_reg_loop < reload_cause_reg_count; reload_cause_reg_loop++) {
		res = NULL;
		res = devm_request_mem_region(
			&(priv->pdev->dev),
			priv->csr_bus_addr + reload_cause_reg_map[reload_cause_reg_loop].offset,
			REG_BLK_SIZE,
			SCD_MODULE_NAME);
		if (!res) {
			dev_err(&(priv->pdev->dev), "cannot request PCI memory region - "
			"relaod cause functionality disabled\n");
			break;
		}
		reload_cause_reg_map[reload_cause_reg_loop].mem = devm_ioremap(
			&(priv->pdev->dev),
			priv->csr_bus_addr + reload_cause_reg_map[reload_cause_reg_loop].offset,
			REG_BLK_SIZE);
		if (!reload_cause_reg_map[reload_cause_reg_loop].mem) {
			dev_err(&(priv->pdev->dev), "cannot remap reload cause PCI registers - "
			"relaod cause functionality disabled\n");
			break;
		}
	}
	if (reload_cause_reg_loop == reload_cause_reg_count) {
		scratchpad_map = devm_ioremap(
				&(priv->pdev->dev), priv->csr_bus_addr + get_reload_cause_scratchpad_reg_offset(),
				REG_BLK_SIZE);
		if (!scratchpad_map) {
			dev_err(&(priv->pdev->dev), "cannot remap scratchpad register - "
			"not processing relaod cause\n");
		} else {
			scratchpad_lock();
			scratchpad_val = ioread32(scratchpad_map);
			if ((scratchpad_val & FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_MASK) == 0) {
				iowrite32((1 << FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_BITPOS), scratchpad_map);
				power_cycle_detected = true;
			}
			scratchpad_unlock();
			devm_iounmap(&(priv->pdev->dev), scratchpad_map);
		}
		if (power_cycle_detected == true) {
			op_status = process_reload_cause(&(priv->pdev->dev));
			if (op_status < 0) {
				dev_info(&(priv->pdev->dev), "error in processing reload cause\n");
			}
		} else {
			dev_info(&(priv->pdev->dev), "didn't detect a system power cycle - "
			"not processing relaod cause");
		}
		start_reload_cause_periodic_task();
	}
}

static void release_reload_cause_resources(struct scd_dev_priv *priv)
{
	struct mapped_register *reload_cause_reg_map;
	size_t reload_cause_reg_count;
	size_t reload_cause_reg_loop;

	get_reload_cause_register_map(&reload_cause_reg_map, &reload_cause_reg_count);
	for (reload_cause_reg_loop = 0; reload_cause_reg_loop < reload_cause_reg_count; reload_cause_reg_loop++) {
		devm_iounmap(&(priv->pdev->dev), reload_cause_reg_map[reload_cause_reg_loop].mem);
		devm_release_mem_region(
			&(priv->pdev->dev),
			priv->csr_bus_addr + reload_cause_reg_map[reload_cause_reg_loop].offset,
			REG_BLK_SIZE);
	}
}

static void read_revision_reg(struct scd_dev_priv *priv)
{
	struct resource *res;
	void __iomem *mem;

	res = devm_request_mem_region(
		&(priv->pdev->dev),
		priv->csr_bus_addr + FPGA_VER_REG,
		REG_BLK_SIZE,
		SCD_MODULE_NAME);
	if (!res) {
		dev_err(&(priv->pdev->dev), "error requesting PCI memory region - "
			"cannot print FPGA version\n");
		return;
	}
	mem = devm_ioremap(
		&(priv->pdev->dev),
		priv->csr_bus_addr + FPGA_VER_REG,
		REG_BLK_SIZE);
	if (!mem) {
		dev_err(&(priv->pdev->dev), "error remaping FPGA version register - "
			"cannot print FPGA version\n");
		return;
	}
	priv->version_reg = ioread32(mem);
	devm_iounmap(&(priv->pdev->dev), mem);
	devm_release_mem_region(
		&(priv->pdev->dev),
		priv->csr_bus_addr + FPGA_VER_REG,
		REG_BLK_SIZE);
}

/*
 * Below macros define a set of sysfs files, and each file is mapped to
 * a specific bit field in SCD/CPU_CPLD registers.
 */
#define FMODE_RO	(S_IRUGO)
#define FMODE_RW	(S_IRUGO | S_IWUSR | S_IWGRP)

#define DARWIN_REGBIT_FPGA_FILES							\
	REGBIT_FILE(darwin, sat0_cpld_sub_ver, 0x400, 0, 8, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, sat0_cpld_ver, 0x400, 8, 8, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, sat1_cpld_sub_ver, 0x400, 16, 8, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, sat1_cpld_ver, 0x400, 24, 8, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, sat0_cpld_fw_ver, 0x400, 0, 16, FMODE_RO,				\
		    sat_cpld_fw_ver_show, NULL)						\
	REGBIT_FILE(darwin, sat1_cpld_fw_ver, 0x400, 16, 16, FMODE_RO,				\
		    sat_cpld_fw_ver_show, NULL)						\
	REGBIT_FILE(darwin, pem_present, 0x5000, 0, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, rackmon_present, 0x5000, 1, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, pem_status, 0x5000, 8, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, pem_input_ok, 0x5000, 10, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(darwin, sec_chip_reset_enter, 0x4000, 0, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, th3_pci_reset_enter, 0x4000, 1, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, th3_sys_reset_enter, 0x4000, 2, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, sat0_cpld_reset_enter, 0x4000, 3, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, sat1_cpld_reset_enter, 0x4000, 4, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, sec_chip_reset_clear, 0x4010, 0, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, th3_pci_reset_clear, 0x4010, 1, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, th3_sys_reset_clear, 0x4010, 2, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, sat0_cpld_reset_clear, 0x4010, 3, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(darwin, sat1_cpld_reset_clear, 0x4010, 4, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)

#define FAIRYWREN_REGBIT_FPGA_FILES							\
	REGBIT_FILE(fairywren, bmc_mode, 0x8, 30, 1, FMODE_RO, regbit_sysfs_show, NULL)		\
	REGBIT_FILE(fairywren, bmc_aboot_grab, 0x2e00, 2, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(fairywren, bmc_state, 0x2e00, 1, 1, FMODE_RO, regbit_sysfs_show, NULL)		\
	REGBIT_FILE(fairywren, bmc_not_reset, 0x2e00, 0, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(fairywren, swap_uart, 0x2e30, 0, 8, FMODE_RW,					\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(fairywren, spi_eeprom_intf, 0x2f30, 1, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(fairywren, mgmt_switch_reset, 0x2f30, 0, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)                              \
	REGBIT_FILE(fairywren, opmode_override, 0x2f30, 5, 3, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)                              \
	REGBIT_FILE(fairywren, switch_jtag_enable, 0x2f40, 0, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(fairywren, oob_eeprom_cmd, 0x7f00, 0, 32, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(fairywren, oob_eeprom_resp, 0x7f10, 0, 32, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)

#define VIPER_REGBIT_FPGA_FILES								\
	REGBIT_FILE(viper, psu1_present, 0x5000, 0, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, psu2_present, 0x5000, 1, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, psu1_output_ok, 0x5000, 8, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, psu2_output_ok, 0x5000, 9, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, psu1_input_ok, 0x5000, 10, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, psu2_input_ok, 0x5000, 11, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(viper, j3_sys_reset_set, 0x4000, 0, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(viper, j3_pcie_reset_set, 0x4000, 1, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(viper, tpm_reset_set, 0x4000, 2, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(viper, j3_sys_reset_clear, 0x4010, 0, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(viper, j3_pcie_reset_clear, 0x4010, 1, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(viper, tpm_reset_clear, 0x4010, 2, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)

#define BLACKCOMB0_REGBIT_FPGA_FILES							\
	REGBIT_FILE(blackcomb, ramon3_0_sys_reset_set, 0x4000, 0, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_0_pcie_reset_set, 0x4000, 1, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_1_sys_reset_set, 0x4000, 2, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_1_pcie_reset_set, 0x4000, 3, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_0_sys_reset_clear, 0x4010, 0, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_0_pcie_reset_clear, 0x4010, 1, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_1_sys_reset_clear, 0x4010, 2, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, ramon3_1_pcie_reset_clear, 0x4010, 3, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(blackcomb, psu1_present, 0x5000, 0, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu2_present, 0x5000, 1, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu3_present, 0x5000, 2, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu4_present, 0x5000, 3, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu1_input_ok, 0x5000, 4, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu2_input_ok, 0x5000, 5, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu3_input_ok, 0x5000, 6, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu4_input_ok, 0x5000, 7, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu1_output_ok, 0x5000, 8, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu2_output_ok, 0x5000, 9, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu3_output_ok, 0x5000, 10, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(blackcomb, psu4_output_ok, 0x5000, 11, 1, FMODE_RO, regbit_sysfs_show, NULL)

#define QUICKSILVER_REGBIT_FPGA_FILES								\
	REGBIT_FILE(quicksilver, th5_sys_reset_set, 0x4000, 2, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(quicksilver, th5_pcie_reset_set, 0x4000, 3, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(quicksilver, th5_sys_reset_clear, 0x4010, 2, 1, FMODE_RW,				\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(quicksilver, th5_pcie_reset_clear, 0x4010, 3, 1, FMODE_RW,			\
		    regbit_sysfs_show, regbit_sysfs_store)				\
	REGBIT_FILE(quicksilver, psu1_present, 0x5000, 0, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(quicksilver, psu2_present, 0x5000, 1, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(quicksilver, psu1_output_ok, 0x5000, 8, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(quicksilver, psu2_output_ok, 0x5000, 9, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(quicksilver, psu1_input_ok, 0x5000, 10, 1, FMODE_RO, regbit_sysfs_show, NULL)	\
	REGBIT_FILE(quicksilver, psu2_input_ok, 0x5000, 11, 1, FMODE_RO, regbit_sysfs_show, NULL)

/* ROOK_SCD_REVISION_REGBIT_FPGA_FILES is not a part of any regbit_sysfs_tables
   since they use fpga_major_rev_show() and fpga_minor_rev_show()
   instead of regbit_sysfs_show(). */
#define ROOK_SCD_REVISION_REGBIT_FPGA_FILES							\
	REGBIT_FILE(rook, fpga_ver, 0x100, 16, 16, FMODE_RO, fpga_major_rev_show, NULL)		\
	REGBIT_FILE(rook, fpga_sub_ver, 0x100, 0, 8, FMODE_RO, fpga_minor_rev_show, NULL)

/* DARWIN_SCD_REVISION_REGBIT_FPGA_FILES is not a part of any regbit_sysfs_tables
   since they use fpga_major_rev_show() and fpga_minor_rev_show()
   instead of regbit_sysfs_show(). */
#define DARWIN_SCD_REVISION_REGBIT_FPGA_FILES							\
	REGBIT_FILE(darwin, fpga_ver, 0x100, 16, 16, FMODE_RO, fpga_major_rev_show, NULL)	\
	REGBIT_FILE(darwin, fpga_sub_ver, 0x100, 0, 8, FMODE_RO, fpga_minor_rev_show, NULL)

#define REGBIT_FILE(_prefix, _name, _reg, _bitops, _bitlen, _mode, _show, _store)	\
	{										\
		.prefix = #_prefix,							\
		.name = #_name,								\
		.reg_offset = _reg,							\
		.bit_offset = _bitops,							\
		.bit_len = _bitlen,							\
	},

struct regbit_sysfs_entry scd_regbit_sysfs[] = {
	/* Always the last entry */
	{
		.name = NULL,
	},
};

struct regbit_sysfs_entry darwin_scd_regbit_sysfs[] = {
	DARWIN_REGBIT_FPGA_FILES

	/* Always the last entry */
	{
		.name = NULL,
	},
};

struct regbit_sysfs_entry fairywren_scd_regbit_sysfs[] = {
	FAIRYWREN_REGBIT_FPGA_FILES

	/* Always the last entry */
	{
		.name = NULL,
	},
};

struct regbit_sysfs_entry viper_scd_regbit_sysfs[] = {
	VIPER_REGBIT_FPGA_FILES

	/* Always the last entry */
	{
		.name = NULL,
	},
};

struct regbit_sysfs_entry blackcomb_scd0_regbit_sysfs[] = {
	BLACKCOMB0_REGBIT_FPGA_FILES

	/* Always the last entry */
	{
		.name = NULL,
	},
};

/* Blackcomb SCDs 1-3 are the same */
#define BLACKCOMB_REGBIT_SYSFS(_id)					\
struct regbit_sysfs_entry blackcomb_scd##_id##_regbit_sysfs[] = {	\
	/* Always the last entry */					\
	{								\
		.name = NULL,						\
	},								\
};
BLACKCOMB_REGBIT_SYSFS(1)
BLACKCOMB_REGBIT_SYSFS(2)
BLACKCOMB_REGBIT_SYSFS(3)

struct regbit_sysfs_entry quicksilver_scd_regbit_sysfs[] = {
	QUICKSILVER_REGBIT_FPGA_FILES

	/* Always the last entry */
	{
		.name = NULL,
	},
};
#undef REGBIT_FILE

#define REGBIT_FILE(_prefix, _name, _reg, _bitops, _bitlen, _mode, _show, _store)	\
static struct device_attribute dev_attr_##_prefix##_##_name = \
	__ATTR(_name, _mode, _show, _store);
DARWIN_REGBIT_FPGA_FILES
FAIRYWREN_REGBIT_FPGA_FILES
VIPER_REGBIT_FPGA_FILES
BLACKCOMB0_REGBIT_FPGA_FILES
QUICKSILVER_REGBIT_FPGA_FILES
ROOK_SCD_REVISION_REGBIT_FPGA_FILES
DARWIN_SCD_REVISION_REGBIT_FPGA_FILES
#undef REGBIT_FILE

#define REGBIT_FILE(_prefix, _name, _reg, _bitops, _bitlen, _mode, _show, _store)	\
	&dev_attr_##_prefix##_##_name.attr,

static struct attribute *scd_attrs[] = {
	NULL,
};

static struct attribute_group scd_attr_group = {
	.attrs = scd_attrs,
};

static struct attribute *darwin_scd_attrs[] = {
	DARWIN_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group darwin_scd_attr_group = {
	.attrs = darwin_scd_attrs,
};

static struct attribute *fairywren_scd_attrs[] = {
	FAIRYWREN_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group fairywren_scd_attr_group = {
	.attrs = fairywren_scd_attrs,
};

static struct attribute *viper_scd_attrs[] = {
	VIPER_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group viper_scd_attr_group = {
	.attrs = viper_scd_attrs,
};

static struct attribute *blackcomb_scd0_attrs[] = {
	BLACKCOMB0_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group blackcomb_scd0_attr_group = {
	.attrs = blackcomb_scd0_attrs,
};

/* Blackcomb SCDs 1-3 are the same */
#define BLACKCOMB_SCD_ATTRS(_id)					\
static struct attribute *blackcomb_scd##_id##_attrs[] = {		\
	NULL,								\
};									\
									\
static struct attribute_group blackcomb_scd##_id##_attr_group = {	\
	.attrs = blackcomb_scd##_id##_attrs,				\
};
BLACKCOMB_SCD_ATTRS(1)
BLACKCOMB_SCD_ATTRS(2)
BLACKCOMB_SCD_ATTRS(3)

static struct attribute *quicksilver_scd_attrs[] = {
	QUICKSILVER_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group quicksilver_scd_attr_group = {
	.attrs = quicksilver_scd_attrs,
};

static struct attribute *rook_scd_revision_attrs[] = {
	ROOK_SCD_REVISION_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group rook_scd_revision_attr_group = {
	.attrs = rook_scd_revision_attrs,
};

static struct attribute *darwin_scd_revision_attrs[] = {
	DARWIN_SCD_REVISION_REGBIT_FPGA_FILES
	NULL,
};

static struct attribute_group darwin_scd_revision_attr_group = {
	.attrs = darwin_scd_revision_attrs,
};
#undef REGBIT_FILE

/*
 * XXX LPC callback for the ROOK CPLD on Darwin.
 */
static int scd_lpc_enable(struct pci_dev *pdev)
{
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);

	priv->csr_bus_addr = lpc_res_addr;
	priv->mem_len = lpc_res_size;
	return 0;
}

static const struct scd_driver_cb scd_lpc_cb = {
	.enable = scd_lpc_enable,
};

static void scd_pci_disable(struct pci_dev *pdev)
{
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);

	if (priv->localbus) {
		pci_iounmap(pdev, priv->localbus);
		pci_release_region(pdev, SCD_BAR_1);
		priv->localbus = NULL;
	}


	pci_disable_device(pdev);
}

static int scd_pci_enable(struct pci_dev *pdev)
{
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);
	int err;
	u16 ssid;
	struct device *dev = &pdev->dev;

	err = pci_enable_device(pdev);
	if (err) {
		dev_err(dev, "cannot enable PCI device (%d)\n", err);
		return err;
	}

	priv->csr_bus_addr = pci_resource_start(pdev, SCD_BAR_REGS);
	priv->mem_len = pci_resource_len(pdev, SCD_BAR_REGS);

	/*
	 * check if this device uses partial reconfiguration to load the
	 * scd image.
	 */
	pci_read_config_word(pdev, PCI_SUBSYSTEM_ID, &ssid);
	if (ssid == RECONFIG_PCI_SUBSYSTEM_ID) {
		priv->is_reconfig = true;
	} else {
		if (pci_resource_flags(pdev, SCD_BAR_1) & IORESOURCE_MEM) {
			err = pci_request_region(pdev, SCD_BAR_1,
						 SCD_MODULE_NAME);
			if (err) {
				dev_err(dev,
					"cannot obtain PCI memory region 1 (%d)\n",
					err);
				goto err_exit;
			}
			priv->localbus = pci_iomap(pdev, SCD_BAR_1, 0);
			if (!priv->localbus) {
				dev_err(dev,
					"cannot remap memory region 1\n");
				err = -ENXIO;
				goto err_iomap_bar1;
			}
		}
	}

	return 0;

err_iomap_bar1:
	pci_release_region(pdev, SCD_BAR_1);

err_exit:
	pci_disable_device(pdev);
	return err;
}

static const struct scd_driver_cb scd_pci_cb = {
	.enable = scd_pci_enable,
	.disable = scd_pci_disable,
};

static void scd_remove(struct pci_dev *pdev)
{
	struct scd_dev_priv *priv = pci_get_drvdata(pdev);

	dev_info(&pdev->dev, "scd removed\n");

	if (priv == NULL)
		return;

	if (pdev->subsystem_device == FAIRYWREN_SCD_PCI_SUBDEVICE_ID) {
		stop_reload_cause_periodic_task();
		release_reload_cause_resources(priv);
	}
	mutex_destroy(&scratchpad_mutex);

	priv->magic = 0;

	if (priv->cdev_initialized)
		fbiob_cdev_destroy(&priv->cdev_desc);
	if (priv->auxbus_initialized)
		fbiob_auxbus_destroy(&priv->aux_bus);
	if (priv->sysfs_initialized)
		sysfs_remove_group(&pdev->dev.kobj, priv->sysfs_attr_group);
	if (pci_match_id(scd_lpc_table, pdev)) {
		sysfs_remove_group(&pdev->dev.kobj, &rook_scd_revision_attr_group);
	}
	if (pdev->subsystem_device == DARWIN_SCD_PCI_SUBDEVICE_ID) {
		sysfs_remove_group(&pdev->dev.kobj, &darwin_scd_revision_attr_group);
	}

	scd_sysfs_regs_destroy(priv);

	if (priv->driver_cb->disable)
		priv->driver_cb->disable(pdev);

	ASSERT(!priv->localbus);

	pci_set_drvdata(pdev, NULL);
	memset(priv, 0, sizeof(*priv));

	kfree(priv);
}

static int scd_probe(struct pci_dev *pdev, const struct pci_device_id *ent)
{
	struct scd_dev_priv *priv;
	int err;
	const struct scd_driver_cb *scd_cb;
	struct attribute_group *sysfs_attr_group = NULL;
	struct regbit_sysfs_entry *regbit_sysfs_table = NULL;

	if (pci_match_id(scd_lpc_table, pdev)) {
		dev_info(&pdev->dev, "apply scd_lpc settings\n");
		scd_cb = &scd_lpc_cb;
	} else {
		scd_cb = &scd_pci_cb;
	}

	switch (ent->subdevice) {
	case DARWIN_SCD_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &darwin_scd_attr_group;
		regbit_sysfs_table = darwin_scd_regbit_sysfs;
		break;
	case FAIRYWREN_SCD_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &fairywren_scd_attr_group;
		regbit_sysfs_table = fairywren_scd_regbit_sysfs;
		break;
	case VIPER_SCD_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &viper_scd_attr_group;
		regbit_sysfs_table = viper_scd_regbit_sysfs;
		break;
	case BLACKCOMB_SCD0_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &blackcomb_scd0_attr_group;
		regbit_sysfs_table = blackcomb_scd0_regbit_sysfs;
		break;
	case BLACKCOMB_SCD1_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &blackcomb_scd1_attr_group;
		regbit_sysfs_table = blackcomb_scd1_regbit_sysfs;
		break;
	case BLACKCOMB_SCD2_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &blackcomb_scd2_attr_group;
		regbit_sysfs_table = blackcomb_scd2_regbit_sysfs;
		break;
	case BLACKCOMB_SCD3_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &blackcomb_scd3_attr_group;
		regbit_sysfs_table = blackcomb_scd3_regbit_sysfs;
		break;
	case QUICKSILVER_SCD_PCI_SUBDEVICE_ID:
		sysfs_attr_group = &quicksilver_scd_attr_group;
		regbit_sysfs_table = quicksilver_scd_regbit_sysfs;
		break;
	default:
		sysfs_attr_group = &scd_attr_group;
		regbit_sysfs_table = scd_regbit_sysfs;
	}

	if (pci_get_drvdata(pdev)) {
		dev_warn(&pdev->dev, "private data already attached %p",
			 pci_get_drvdata(pdev));
	}

	priv = kmalloc(sizeof(*priv), GFP_KERNEL);
	if (priv == NULL) {
		dev_err(&pdev->dev, "cannot allocate private data, aborting\n");
		err = -ENOMEM;
		goto fail;
	}

	memset(priv, 0, sizeof(struct scd_dev_priv));
	priv->pdev = pdev;
	priv->magic = SCD_MAGIC;
	priv->localbus = NULL;
	priv->driver_cb = scd_cb;
	priv->regbit_sysfs_table = regbit_sysfs_table;
	priv->sysfs_attr_group = sysfs_attr_group;

	pci_set_drvdata(pdev, priv);

	err = scd_cb->enable(pdev);
	if (err) {
		goto fail;
	}

	err = scd_sysfs_regs_init(priv);
	if (err) {
		goto fail;
	}

	if (ent->subdevice == FAIRYWREN_SCD_PCI_SUBDEVICE_ID) {
		print_reload_cause_info(priv);
	}

	if (pci_match_id(scd_lpc_table, pdev)) {
		read_revision_reg(priv);
		err = sysfs_create_group(&pdev->dev.kobj, &rook_scd_revision_attr_group);
		if (err) {
			dev_err(&pdev->dev, "sysfs_create_group() error %d for rook scd revision reg\n", err);
		}
	}

	if (ent->subdevice == DARWIN_SCD_PCI_SUBDEVICE_ID) {
		read_revision_reg(priv);
		err = sysfs_create_group(&pdev->dev.kobj, &darwin_scd_revision_attr_group);
		if (err) {
			dev_err(&pdev->dev, "sysfs_create_group() error %d for darwin scd revision reg\n", err);
		}
	}

	if (priv->sysfs_attr_group->attrs[0]) {
		err = sysfs_create_group(&pdev->dev.kobj, priv->sysfs_attr_group);
		if (err) {
			dev_err(&pdev->dev, "sysfs_create_group() error %d\n", err);
			goto fail;
		}
		priv->sysfs_initialized = 1;
	}

	err = fbiob_auxbus_init(&priv->aux_bus, &pdev->dev);
	if (err) {
		dev_err(&pdev->dev, "aux_bus init error %d\n", err);
		goto fail;
	}
	priv->auxbus_initialized = 1;

	err = fbiob_cdev_init(&priv->cdev_desc, pdev, &priv->aux_bus,
				priv->csr_bus_addr, priv->mem_len);
	if (err) {
		dev_err(&pdev->dev, "cdev init error %d\n", err);
		goto fail;
	}
	priv->cdev_initialized = 1;

	if (priv->is_reconfig &&
	    (priv->scd_revision == RECONFIG_STATE_BAR_VALUE))
		dev_info(&pdev->dev,
			 "scd detected: FPGA in reconfig state\n");
	else
		dev_info(&pdev->dev, "scd initialized successfully\n");

	return 0;

fail:
	scd_remove(pdev);

	return err;
}


static void scd_shutdown(struct pci_dev *pdev)
{
	dev_info(&pdev->dev, "scd shutdown\n");
}

/*
 * XXX Please DO NOT add darwin IDs into the table until platform_manager
 * is enabled on darwin: this is to prevent potential conflict in FBOSS
 * provisioning (ramdisk) kernel, when both legacy scd (mfd-style) and
 * new scd (auxdev-style) drivers want to claim the SCD FPGA.
 */
static struct pci_device_id scd_pci_table[] = {
#if 0
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			SCD_PCI_VENDOR_ID, DARWIN_SCD_PCI_SUBDEVICE_ID) },
#endif
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, FAIRYWREN_SCD_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, VIPER_SCD_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, BLACKCOMB_SCD0_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, BLACKCOMB_SCD1_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, BLACKCOMB_SCD2_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, BLACKCOMB_SCD3_PCI_SUBDEVICE_ID) },
	{ PCI_DEVICE_SUB(SCD_PCI_VENDOR_ID, SCD_PCI_DEVICE_ID,
			 SCD_PCI_VENDOR_ID, QUICKSILVER_SCD_PCI_SUBDEVICE_ID) },
	{
		0,
	},
};
MODULE_DEVICE_TABLE(pci, scd_pci_table);

static pci_ers_result_t scd_error_detected(struct pci_dev *pdev,
					   pci_channel_state_t state)
{
	dev_err(&pdev->dev, "error detected (state=%d)\n", state);
	return PCI_ERS_RESULT_DISCONNECT;
}

static struct pci_error_handlers scd_error_handlers = {
	.error_detected = scd_error_detected,
};

static struct pci_driver scd_driver = {
	.name = SCD_MODULE_NAME,
	.id_table = scd_pci_table,
	.probe = scd_probe,
	.remove = scd_remove,
	.err_handler = &scd_error_handlers,
	.shutdown = &scd_shutdown,
};

module_pci_driver(scd_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Hugh Holbrook and James Lingard");
MODULE_DESCRIPTION("scd driver");
MODULE_VERSION(BSP_VERSION);
