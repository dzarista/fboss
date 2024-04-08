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

#include "fbiob-auxdev.h"
#include "scd-smbus.h"

#define DRIVER_NAME	"scd-smbus"

#define master_dbg(_master, _fmt, _args...)                                    \
	dev_dbg(&(_master)->auxdev->dev, "#%d " _fmt, (_master)->id, ##_args)
#define master_notice(_master, _fmt, _args...)                                 \
	dev_notice(&(_master)->auxdev->dev, "#%d " _fmt, (_master)->id,     \
		   ##_args)
#define master_warn(_master, _fmt, _args...)                                   \
	dev_warn(&(_master)->auxdev->dev, "#%d " _fmt " (%s:%d)",           \
		 (_master)->id, ##_args, __func__, __LINE__)
#define master_err(_master, _fmt, _args...)                                    \
	dev_warn(&(_master)->auxdev->dev, "#%d " _fmt " (%s:%d)",           \
		 (_master)->id, ##_args, __func__, __LINE__)

static int smbus_master_max_retries = MASTER_DEFAULT_MAX_RETRIES;
module_param(smbus_master_max_retries, int, S_IRUSR | S_IWUSR);
MODULE_PARM_DESC(smbus_master_max_retries,
		 "Number of smbus transaction retries to perform on error");

static const struct bus_params default_smbus_params = {
	.t = 1,
	.datw = 3,
	.datr = 3,
	.ed = 0,
};

static u32 smbus_csr_read(struct scd_smbus_master *master, u32 reg_offset)
{
	return ioread32(master->mmio_csr + reg_offset);
}

static void smbus_csr_write(struct scd_smbus_master *master,
			    u32 reg_offset,
			    u32 val)
{
	iowrite32(val, master->mmio_csr + reg_offset);
}

static void smbus_master_lock(struct scd_smbus_master *master)
{
	mutex_lock(&master->mutex);
}

static void smbus_master_unlock(struct scd_smbus_master *master)
{
	mutex_unlock(&master->mutex);
}

/* SMBus functions */
static void smbus_master_write_req(struct scd_smbus_master *master,
				   union smbus_request_reg req)
{
	master_dbg(master, "wr req " REQ_FMT "\n", REQ_ARGS(req));
	smbus_csr_write(master, master->req, req.reg);
}

static void smbus_master_write_cs(struct scd_smbus_master *master,
				  union smbus_ctrl_status_reg cs)
{
	master_dbg(master, "wr cs " CS_FMT "\n", CS_ARGS(cs));
	smbus_csr_write(master, master->cs, cs.reg);
}

static union smbus_ctrl_status_reg
smbus_master_read_cs(struct scd_smbus_master *master)
{
	union smbus_ctrl_status_reg cs;
	cs.reg = smbus_csr_read(master, master->cs);
	master_dbg(master, "rd cs " CS_FMT "\n", CS_ARGS(cs));
	return cs;
}

static union smbus_response_reg
__smbus_master_read_resp(struct scd_smbus_master *master)
{
	union smbus_response_reg resp;
	resp.reg = smbus_csr_read(master, master->resp);
	master_dbg(master, "rd rsp " RSP_FMT "\n", RSP_ARGS(resp));
	return resp;
}

static s32 smbus_check_resp(union smbus_response_reg resp, u32 tid)
{
	if (resp.fe)
		return -EIO;
	if (resp.ack_error)
		return -EIO;
	if (resp.timeout_error)
		return -EIO;
	if (resp.bus_conflict_error)
		return -EIO;
	if (resp.flushed)
		return -EIO;
	if (resp.ti != (tid & 0xf))
		return -EIO;
	if (resp.foe)
		return -EIO;

	return 0;
}

static u32 scd_smbus_func(struct i2c_adapter *adapter)
{
	return I2C_FUNC_SMBUS_QUICK | I2C_FUNC_SMBUS_BYTE |
	       I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA |
	       I2C_FUNC_SMBUS_I2C_BLOCK | I2C_FUNC_SMBUS_BLOCK_DATA |
	       I2C_FUNC_I2C | I2C_FUNC_NOSTART;
}

static void smbus_master_reset(struct scd_smbus_master *master)
{
	union smbus_ctrl_status_reg cs;
	cs = smbus_master_read_cs(master);
	cs.rst = 1;
	cs.foe = 1;
	smbus_master_write_cs(master, cs);
	mdelay(50);
	cs.rst = 0;
	smbus_master_write_cs(master, cs);
	mdelay(50);
}

static const struct bus_params *get_smbus_params(struct scd_smbus *bus,
						 u16 addr)
{
	const struct bus_params *params = &default_smbus_params;
	struct bus_params *params_tmp;

	list_for_each_entry (params_tmp, &bus->params, list) {
		if (params_tmp->addr == 0x00) {
			// bus wide params found, we should still look for a more specific one
			params = params_tmp;
		}
		if (params_tmp->addr == addr) {
			params = params_tmp;
			break;
		}
	}

	return params;
}

static int scd_smbus_master_enter(struct scd_smbus_master *master, int foe,
				  union smbus_ctrl_status_reg *_cs)
{
	union smbus_ctrl_status_reg cs;
	int err;

	err = 0;

	cs = smbus_master_read_cs(master);

	if (cs.fe || cs.brb || cs.nrq || cs.nrs) {
		int i;

		cs.rst = 1;
		smbus_master_write_cs(master, cs);

		for (i = 1; i <= 8; i *= 2) {
			cs = smbus_master_read_cs(master);

			err = (cs.rst && !cs.fe && !cs.brb && !cs.nrq &&
			       !cs.nrs) ?
					    0 :
					    -EIO;
			if (!err)
				break;

			msleep(i);
		}
		if (err)
			master_dbg(master, "cs " CS_FMT " err=%d\n",
				   CS_ARGS(cs), err);
	}

	if (!err && (cs.rst || cs.foe != foe)) {
		cs.rst = 0;
		cs.foe = foe;
		smbus_master_write_cs(master, cs);

		cs = smbus_master_read_cs(master);
		err = cs.rst ? -EIO : 0;
	}

	if (!err && _cs)
		*_cs = cs;

	return err;
}

static void scd_smbus_master_leave(struct scd_smbus_master *master, int err)
{
	union smbus_ctrl_status_reg cs;

	cs = smbus_master_read_cs(master);

	if (!err && cs.nrs) {
		int i;

		/* Show data left in the response fifo.
         Unconsumed PEC codes etc. */
		master_dbg(master, "cs " CS_FMT " dropping %d rsps\n",
			   CS_ARGS(cs), cs.nrs);

		for (i = 0; i < cs.nrs; i++) {
			union smbus_response_reg rsp =
				__smbus_master_read_resp(master);
			master_dbg(master, "rsp " RSP_FMT "\n", RSP_ARGS(rsp));
		}

		cs = smbus_master_read_cs(master);
	}

	if (cs.fe || cs.brb || cs.nrq || cs.nrs) {
		cs.rst = 1;
		smbus_master_write_cs(master, cs);
	}
}

static int scd_smbus_master_wait(struct scd_smbus *bus, u16 addr)
{
	const int delay_per_byte[4] = { 110, 35, 14, 14 };
	struct scd_smbus_master *master = bus->master;
	union smbus_ctrl_status_reg cs;
	unsigned long start;

	start = jiffies;

	cs = smbus_master_read_cs(master);

	while (!cs.fe) {
		int nrq;
		unsigned long timeo;

		/* reset timeo */
		nrq = cs.nrq;
		timeo = jiffies + msecs_to_jiffies(100);

		do {
			int fsz, delay;

			fsz = scd_smbus_cs_fsz(cs);
			if (fsz > 0 && cs.nrs >= fsz) {
				/* saw req { .br=1, .sp=1, .. } reproduce this */
				master_dbg(
					master,
					"cs " CS_FMT
					" bus=%d addr=%#02x fsz=%d, overflow\n",
					CS_ARGS(cs), bus->adap.nr, addr, fsz);
				return -EOVERFLOW;
			}

			if (jiffies > timeo) {
				master_dbg(
					master,
					"cs " CS_FMT
					" timed out after %ums bus=%d addr=%#02x\n",
					CS_ARGS(cs),
					jiffies_to_msecs(jiffies - start),
					bus->adap.nr, addr);
				return -ETIMEDOUT;
			}

			delay = (nrq + 1) * delay_per_byte[cs.sp];
			master_dbg(master, "delay=%dus\n", delay);

			usleep_range(delay, 2 * delay);

			cs = smbus_master_read_cs(master);

		} while (!cs.fe && nrq == cs.nrq);
	}

	smbus_master_write_cs(master, cs); /* clear cs.fe */

	return 0;
}

static int scd_smbus_master_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs,
				 int num)
{
	struct scd_smbus *bus = i2c_get_adapdata(adap);
	struct i2c_msg *msg, *end = msgs + num;
	union smbus_ctrl_status_reg cs;
	union smbus_request_reg req;
	int ss, ti, err;

	ss = 0;
	for (msg = msgs; msg < end; msg++) {
		int br = !!(msg->flags & I2C_M_RECV_LEN);
		ss += 1;
		if (!br) {
			ss += msg->len;
		}

		master_dbg(
			bus->master,
			"bus %d msg[%ld] { .addr=%#02x .flags=%#x .len=%#x } ss=%d\n",
			adap->nr, msg - msgs, msg->addr, msg->flags, msg->len,
			ss);

		if (msg->flags & I2C_M_TEN) {
			return -EOPNOTSUPP;
		}

		if ((msg->flags & I2C_M_RECV_LEN) && msg + 1 < end) {
			return -EOPNOTSUPP;
		}
	}

	smbus_master_lock(bus->master);

	err = scd_smbus_master_enter(bus->master, 1, &cs);
	if (err)
		goto out;

	req.reg = 0;
	req.ss = ss;

	ti = 0;
	for (msg = msgs; msg < end; msg++) {
		int rd = !!(msg->flags & I2C_M_RD);
		int br = !!(msg->flags & I2C_M_RECV_LEN);
		int ns = !!(msg->flags & I2C_M_NOSTART);
		const struct bus_params *params;
		int i;

		params = get_smbus_params(bus, msg->addr);

		req.ti = ti++;
		req.sp = req.ti == ss;
		req.bs = bus->id;
		req.st = !ns;
		req.dod = 1;
		req.da = 0;
		req.br = (br ? cs.ver >= 2 : 0);
		req.d = (msg->addr << 1) | rd;
		req.t = params->t;

		smbus_master_write_req(bus->master, req);

		req.st = 0;
		req.ss = 0;
		req.dod = !rd;

		i = 0;

		for (; i < msg->len && !br; i++) {
			req.ti = ti++;
			req.sp = ti == ss;
			req.d = rd ? 0 : msg->buf[i];
			req.da = rd && !req.sp;
			req.ed = req.sp ? params->ed : 0;

			smbus_master_write_req(bus->master, req);
		}
	}

	err = scd_smbus_master_wait(bus, (--msg)->addr);
	if (err)
		goto out;

	ti = 0;
	for (msg = msgs; msg < end; msg++) {
		union smbus_response_reg rsp;
		int rd = !!(msg->flags & I2C_M_RD);
		int br = !!(msg->flags & I2C_M_RECV_LEN);
		int i;

		rsp = __smbus_master_read_resp(bus->master);
		err = smbus_check_resp(rsp, ti);
		if (err) {
			/* nak for msg[0].addr is not a protocol violation, so lower
            the log level. */
			union smbus_response_reg nak = { .ti = 0,
							 .ss = ss,
							 .ack_error = 1 };
			if (ti == 0 && rsp.reg == nak.reg) {
				master_dbg(bus->master,
					   "rsp " RSP_FMT
					   " bus=%d addr=%#02x ti=%d err=%d\n",
					   RSP_ARGS(rsp), adap->nr, msg->addr,
					   ti, err);
			} else {
				master_dbg(bus->master,
					   "rsp " RSP_FMT
					   " bus=%d addr=%#02x ti=%d err=%d\n",
					   RSP_ARGS(rsp), adap->nr, msg->addr,
					   ti, err);
			}
			goto out;
		}
		ti++;

		for (i = 0; i < msg->len; i++) {
			rsp = __smbus_master_read_resp(bus->master);
			err = smbus_check_resp(rsp, ti);
			if (err) {
				master_dbg(bus->master,
					   "rsp " RSP_FMT
					   " bus=%d addr=%#02x ti=%d err=%d\n",
					   RSP_ARGS(rsp), adap->nr, msg->addr,
					   ti, err);
				goto out;
			}
			ti++;

			if (rd)
				msg->buf[i] = rsp.d;

			if (i == 0 && br) {
				/*
              msg.len (I2C_M_RECV_LEN block transfer)

              At time of user entry

              - msg.len holds msg.buf size.
              - msg.buf[0] holds extra byte count: len [, pec..])

              Next, i2cdev_ioctl_rdwr will

              1. check msg.buf[0] >= 1, to accomodate len.
              2. check msg.len >= msg.buf[0] + I2C_SMBUS_BLOCK_MAX
              3. set msg.len := msg.buf[0]
              4. call master_xfer
              5. copy_to_user(..., msg->buf, msg->len)

              Therefore, master_xfer will

              1. receive msg.buf[0]
              2. add msg.buf[0] to to msg.len

              As with smbus block transfers:
                1 <= valid len <= I2C_SMBUS_BLOCK_MAX.
            */

				if (msg->buf[0] < 1 ||
				    msg->buf[0] > I2C_SMBUS_BLOCK_MAX) {
					err = -EPROTO;
					master_dbg(
						bus->master,
						"rsp " RSP_FMT
						" bus=%d addr=%#02x ti=%d err=%d\n",
						RSP_ARGS(rsp), adap->nr,
						msg->addr, ti, err);
					goto out;
				}

				msg->len += msg->buf[0];

				if (cs.ver < 2) {
					const struct bus_params *params;
					int j;

					params = get_smbus_params(bus,
								  msg->addr);

					ti = 0;
					ss = msg->len - 1;

					req.reg = 0;
					req.bs = bus->id;
					req.ss = ss;
					req.t = params->t;

					for (j = 0; j < ss; j++) {
						req.ti = ti++;
						req.sp = ti == ss;
						req.da = !req.sp;
						req.ed =
							req.sp ? params->ed : 0;

						smbus_master_write_req(
							bus->master, req);

						req.ss = 0;
					}

					err = scd_smbus_master_wait(bus,
								    msg->addr);
					if (err)
						goto out;

					ti = 0;
				}
			}
		}
	}

out:
	scd_smbus_master_leave(bus->master, err);

	smbus_master_unlock(bus->master);

	return err ?: num;
}

static struct i2c_algorithm scd_smbus_algorithm = {
	.master_xfer = scd_smbus_master_xfer,
	.functionality = scd_smbus_func,
};

static int scd_smbus_bus_add(struct scd_smbus_master *master, int port)
{
	int err;
	struct scd_smbus *bus;
	struct auxiliary_device *auxdev = master->auxdev;
	struct device *dev = &auxdev->dev;
	char symlink[64];

	bus = devm_kzalloc(dev, sizeof(*bus), GFP_KERNEL);
	if (!bus)
		return -ENOMEM;

	bus->master = master;
	bus->id = port;
	INIT_LIST_HEAD(&bus->params);
	bus->adap.owner = THIS_MODULE;
	bus->adap.class = 0;
	bus->adap.algo = &scd_smbus_algorithm;
	bus->adap.dev.parent = dev;

	scnprintf(bus->adap.name, sizeof(bus->adap.name),
		  "SCD %s SMBus master %d bus %d", pci_name(master->pci_dev),
		  master->id % 10, bus->id);
	i2c_set_adapdata(&bus->adap, bus);

	err = i2c_add_adapter(&bus->adap);
	if (err)
		return err;

	/*
	 * Create symlink so it's easy for userspace programs to identify
	 * the I2C bus.
	 */
	snprintf(symlink, sizeof(symlink), "channel-%d", port);
	err = sysfs_create_link(&dev->kobj, &bus->adap.dev.kobj, symlink);
	if (err)
		dev_warn(dev, "unable to create symlink for port %d, err=%d",
			port, err);

	smbus_master_lock(master);
	list_add_tail(&bus->list, &master->bus_list);
	smbus_master_unlock(master);

	return 0;
}

static void scd_smbus_remove(struct auxiliary_device *auxdev)
{
	struct scd_smbus *bus, *tmp_bus;
	struct bus_params *params, *tmp_params;
	struct scd_smbus_master *master = dev_get_drvdata(&auxdev->dev);

	/*
	 * Remove all i2c_adapter first to make sure the scd_smbus and
	 * scd_smbus_master are unused when removing them.
	 */
	list_for_each_entry (bus, &master->bus_list, list) {
		i2c_del_adapter(&bus->adap);
	}

	smbus_master_reset(master);

	list_for_each_entry_safe (bus, tmp_bus, &master->bus_list, list) {
		list_for_each_entry_safe (params, tmp_params, &bus->params,
					  list) {
			list_del(&params->list);
			kfree(params);
		}

		list_del(&bus->list);
	}

	mutex_destroy(&master->mutex);
}

static int scd_smbus_probe(struct auxiliary_device *auxdev,
			   const struct auxiliary_device_id *id)
{
	int err, port;
	struct resource *res;
	union smbus_ctrl_status_reg cs;
	struct scd_smbus_master *master;
	struct device *dev = &auxdev->dev;
	struct fbiob_aux_adapter *aux_adap =
			(struct fbiob_aux_adapter *)container_of(auxdev,
					struct fbiob_aux_adapter, auxdev);
	struct fbiob_aux_data *pdata = &aux_adap->data;

	master = devm_kzalloc(dev, sizeof(*master), GFP_KERNEL);
	if (!master)
		return -ENOMEM;
	dev_set_drvdata(dev, master);

	master->csr_bus_addr = pdata->csr_offset;
	res = devm_request_mem_region(dev, master->csr_bus_addr,
					FBIOB_I2C_BLK_SIZE, auxdev->name);
	if (!res)
		return -EBUSY;

	master->mmio_csr = devm_ioremap(dev, master->csr_bus_addr,
					FBIOB_I2C_BLK_SIZE);
	if (!master->mmio_csr)
		return -ENOMEM;

	mutex_init(&master->mutex);
	master->id = auxdev->id;
	master->req = SMBUS_REQUEST_OFFSET;
	master->cs = SMBUS_CONTROL_STATUS_OFFSET;
	master->resp = SMBUS_RESPONSE_OFFSET;
	master->max_retries = smbus_master_max_retries;
	master->auxdev = auxdev;
	master->pci_dev = to_pci_dev(dev->parent);
	INIT_LIST_HEAD(&master->bus_list);

	for (port = 0; port < pdata->i2c_data.num_channels; port++) {
		err = scd_smbus_bus_add(master, port);
		if (err)
			goto fail_bus;
	}

	smbus_master_reset(master);

	cs = smbus_master_read_cs(master);
	master_notice(master, "@%#llx version %d", res->start, cs.ver);

	return 0;

fail_bus:
	scd_smbus_remove(auxdev);
	return err;
}

static const struct auxiliary_device_id scd_smbus_ids[] = {
	{ .name = "scd.i2c_master" },
	{ .name = "scd.smbus_master" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, scd_smbus_ids);

static struct auxiliary_driver scd_smbus_driver = {
	.driver = {
		.name = DRIVER_NAME,
	},
	.probe = scd_smbus_probe,
	.remove = scd_smbus_remove,
	.id_table = scd_smbus_ids,
};

module_auxiliary_driver(scd_smbus_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("SCD SMBus driver");