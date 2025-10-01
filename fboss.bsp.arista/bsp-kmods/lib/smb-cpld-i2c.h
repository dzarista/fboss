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

#ifndef _SMB_CPLD_I2C_H_
#define _SMB_CPLD_I2C_H_

#include <linux/i2c.h>
#include <linux/device.h>

#include "regbit-sysfs.h"

/* Common CPLD register definitions */
#define CPLD_REG_REV_MINOR	0x0
#define CPLD_REG_REV_MAJOR	0x1
#define CPLD_REG_CTRL_STS	0x5
#define CPLD_REG_SCD_FPGA_STA	0xA
#define CPLD_REG_JTAG_SEL	0xC
#define CPLD_REG_IDPROM_WP	0x22

/* Common regbit_sysfs_config entries */
extern const struct regbit_sysfs_config smb_cpld_common_attrs[];
extern const int smb_cpld_common_attrs_count;

/* Common function declarations */
int smb_cpld_fw_ver_read(struct i2c_client *client, char *buf, const char *device_name);
ssize_t smb_cpld_fw_ver_show(struct device *dev, struct device_attribute *attr, char *buf);
int smb_cpld_create_fw_ver_attr(struct i2c_client *client);
int smb_cpld_init_with_attrs(struct device *dev,
		const struct regbit_sysfs_config *driver_attrs,
		int driver_attrs_count);
void smb_cpld_i2c_remove(struct i2c_client *client);

/* Macro for creating a probe function */
#define SMB_CPLD_PROBE_FN(_name, _attrs)						\
static int smb_cpld_i2c_probe(struct i2c_client *client)				\
{											\
	int ret;									\
											\
	ret = smb_cpld_fw_ver_read(client, NULL, _name);				\
	if (ret < 0)									\
		return ret;								\
											\
	ret = smb_cpld_create_fw_ver_attr(client);					\
	if (ret < 0)									\
		return ret;								\
											\
	return smb_cpld_init_with_attrs(&client->dev, _attrs, ARRAY_SIZE(_attrs));	\
}

#endif /* _SMB_CPLD_I2C_H_ */
