/* Copyright (c) 2023 Arista Networks, Inc.
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

#include <linux/delay.h>
#include <linux/module.h>

#include "scd-spi.h"
#include "fbiob-auxdev.h"

#define DRIVER_NAME "scd-spi"

static u32 spi_csr_read(struct scd_spi_devdata *devdata, u32 reg_offset)
{
	return ioread32(devdata->mmio_csr + reg_offset);
}

static void spi_csr_write(struct scd_spi_devdata *devdata,
			    u32 reg_offset,
			    u32 val)
{
	iowrite32(val, devdata->mmio_csr + reg_offset);
}

static int scd_spi_tx_wait(struct scd_spi_devdata *devdata, int entries,
			   int orig_entries)
{
	union scd_spi_ctrl ctrl;
	unsigned long timeout;
	timeout = jiffies + msecs_to_jiffies((10 * orig_entries) + 10);
	do {
		ctrl.reg = spi_csr_read(devdata, devdata->ctrl_addr);
		if (ctrl.write_fifo_count <= entries) {
			return 0;
		}
		usleep_range(1, 50);
	} while (!time_after(jiffies, timeout));

	dev_err(&devdata->pci_dev->dev,
		DRIVER_NAME ": write timeout, %d entries left\n",
		ctrl.write_fifo_count);

	return 1;
}

static int scd_spi_rx_wait(struct scd_spi_devdata *devdata, int entries)
{
	union scd_spi_ctrl ctrl;
	unsigned long timeout;

	timeout = jiffies + msecs_to_jiffies((10 * entries) + 10);
	do {
		ctrl.reg =
			spi_csr_read(devdata, devdata->ctrl_addr);
		if (ctrl.read_fifo_count >= entries) {
			return 0;
		}
		usleep_range(1, 50);
	} while (!time_after(jiffies, timeout));

	dev_err(&devdata->pci_dev->dev,
		DRIVER_NAME ": read timeout, %d entries expecting %d\n",
		ctrl.read_fifo_count, entries);

	return 1;
}

static int scd_spi_sanitize(struct scd_spi_devdata *devdata)
{
	union scd_spi_ctrl ctrl;
	union scd_spi_cmd_fifo cmd;
	int i;

	// Clear the overflow/underflow bits
	ctrl.reg = 0;
	ctrl.read_fifo_underflow = 1;
	ctrl.cmd_fifo_overflow = 1;
	spi_csr_write(devdata, devdata->ctrl_addr, ctrl.reg);

	// Clear out the read fifo
	ctrl.reg = spi_csr_read(devdata, devdata->ctrl_addr);
	for (i = 0; i < ctrl.read_fifo_count; i++) {
		spi_csr_read(devdata, devdata->read_fifo_addr);
	}

	// Do a single write with chip select end to put the bus back into a known state
	// and finish clearing overflow if it happened. Expect to read back 1 value to
	// verify the accelerator is working.
	cmd.reg = 0;
	cmd.record_output = 1;
	cmd.chip_select_end = 1;
	spi_csr_write(devdata, devdata->cmd_fifo_addr, cmd.reg);
	if (scd_spi_tx_wait(devdata, 0, 1)) {
		return 1;
	}
	if (scd_spi_rx_wait(devdata, 1)) {
		return 1;
	}
	spi_csr_read(devdata, devdata->read_fifo_addr);
	return 0;
}

static int scd_spi_transfer_one(struct scd_spi_devdata *devdata,
				struct spi_transfer *t, bool last_xfer)
{
	const u8 *tx_buf;
	u8 *rx_buf;
	bool read;
	bool last_entry;
	int i;
	int j;
	int fifo_count;
	union scd_spi_cmd_fifo write_val;
	union scd_spi_read_fifo read_val;

	tx_buf = t->tx_buf;
	rx_buf = t->rx_buf;
	fifo_count = 0;
	read = (rx_buf != NULL);

	for (i = 0; i < t->len; i++) {
		last_entry = (i == (t->len - 1));
		write_val.reg = 0;
		// If tx_buf is null (read-only transfer), we should write 0s
		if (tx_buf) {
			write_val.write_data = *(tx_buf++);
		}
		// cs_change inverts the expected behavior. If it's not the last xfer in a
		// message, cs_change would end chip select. If it is the last xfer in the
		// message, cs_change would *not* end chip select.
		write_val.chip_select_end =
			last_entry && (last_xfer ^ t->cs_change);
		write_val.record_output = read;

		dev_dbg(&devdata->pci_dev->dev,
			DRIVER_NAME ": FIFO write data 0x%08x\n",
			write_val.reg);
		spi_csr_write(devdata, devdata->cmd_fifo_addr,
				   write_val.reg);
		fifo_count++;

		if (last_entry || fifo_count == devdata->fifo_size) {
			// Last byte or the FIFO is full. Drain it and continue or finish.
			scd_spi_tx_wait(devdata, 0, fifo_count);

			if (read) {
				scd_spi_rx_wait(devdata, fifo_count);
				for (j = 0; j < fifo_count; j++) {
					read_val.reg = spi_csr_read(
						devdata, devdata->read_fifo_addr);
					dev_dbg(&devdata->pci_dev->dev,
						DRIVER_NAME
						": FIFO read data 0x%08x\n",
						read_val.reg);
					*(rx_buf++) = read_val.read_data;
				}
			}

			fifo_count = 0;
		}
	}

	spi_delay_exec(&t->delay, t);

	return 0;
}

static int scd_spi_transfer_one_message(struct spi_master *controller,
					struct spi_message *msg)
{
	struct scd_spi_devdata *devdata;
	struct spi_transfer *t;
	bool last_xfer;
	unsigned int total_len = 0;

	devdata = spi_master_get_devdata(controller);

	list_for_each_entry (t, &msg->transfers, transfer_list) {
		last_xfer = list_is_last(&t->transfer_list, &msg->transfers);

		scd_spi_transfer_one(devdata, t, last_xfer);
		total_len += t->len;
	}

	msg->status = 0;
	msg->actual_length = total_len;
	spi_finalize_current_message(controller);

	return 0;
}

static int scd_spi_controller_probe(struct auxiliary_device *auxdev,
			   const struct auxiliary_device_id *id)
{
	int err;
	struct resource *res;
	struct spi_master *controller;
	struct scd_spi_devdata *devdata;
	struct spi_device *device;
	struct spi_board_info info = { { 0 } };
	struct device *dev = &auxdev->dev;
    struct fbiob_aux_adapter *aux_adap =
                (struct fbiob_aux_adapter *)container_of(auxdev,
                        struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;
	struct fbiob_spi_data spi_data = pdata->spi_data;

	controller =
		spi_alloc_master(&auxdev->dev, sizeof(struct scd_spi_devdata));
	if (!controller) {
		return -ENOMEM;
	}
	devdata = spi_master_get_devdata(controller);
	dev_set_drvdata(dev, devdata);

	devdata->csr_addr = pdata->csr_offset;
	res = devm_request_mem_region(dev, devdata->csr_addr,
					FBIOB_SPI_CSR_BLK_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	devdata->mmio_csr = devm_ioremap(dev, devdata->csr_addr, FBIOB_SPI_CSR_BLK_SIZE);
	if (!devdata->mmio_csr)
		return -ENOMEM;

	devdata->pci_dev = to_pci_dev(dev->parent);
	devdata->cmd_fifo_addr = SPI_CMD_FIFO_OFFSET;
	devdata->read_fifo_addr = SPI_READ_FIFO_OFFSET;
	devdata->ctrl_addr = SPI_CTRL_OFFSET;
	devdata->fifo_size = SPI_FIFO_SIZE;

	controller->bus_num = auxdev->id;
	controller->num_chipselect = 1;
	controller->flags = SPI_MASTER_MUST_TX;
	controller->transfer_one_message = scd_spi_transfer_one_message;

	if (scd_spi_sanitize(devdata)) {
		// Sanitize failed - SCD may not have a SPI accelerator at this address
		dev_err(&devdata->pci_dev->dev,
			DRIVER_NAME ": failed to sanitize SPI accelerator. "
				    "SPI register offset may not be correct. "
				    "cmd: 0x%08x read: 0x%08x ctrl: 0x%08x\n",
			devdata->cmd_fifo_addr, devdata->read_fifo_addr,
			devdata->ctrl_addr);
		err = -ENOPROTOOPT;
		goto fail_controller;
	}

	spi_register_master(controller);

	// Update spi device configs from PM config 
	strscpy(info.modalias, spi_data.spidevs->modalias, sizeof(info.modalias));
	info.max_speed_hz = spi_data.spidevs->max_speed_hz;
  	info.chip_select = spi_data.spidevs->chip_select;
	dev_info(dev, "Modalias: %s, MaxSpeed: %d, ChipSelect: %d\n", info.modalias,
		info.max_speed_hz, info.chip_select);

	device = spi_new_device(controller, &info);

	if (!device) {
		dev_warn(&devdata->pci_dev->dev,
			 DRIVER_NAME ": could not create spi device\n");
		err = -EINVAL;
		goto fail_controller;
	}

	devdata->controller = controller;
	devdata->device = device;

	dev_info(dev, "%s @ 0x%x\n", pdata->id.name, devdata->csr_addr);
	return 0;

fail_controller:
	spi_master_put(controller);
	return err;
}

static void scd_spi_controller_remove(struct auxiliary_device *auxdev)
{
	struct scd_spi_devdata *devdata = dev_get_drvdata(&auxdev->dev);
	spi_unregister_device(devdata->device);
	spi_unregister_master(devdata->controller);
	dev_info(&auxdev->dev, "spi @ 0x%x removed\n", devdata->csr_addr);
}

static const struct auxiliary_device_id scd_spi_ids[] = {
	{ .name = "scd.spi_master" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_spi_ids);

static struct auxiliary_driver scd_spi_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_spi_controller_probe,
	.remove = scd_spi_controller_remove,
	.id_table = scd_spi_ids,
};

module_auxiliary_driver(scd_spi_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("SCD SPI driver");