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

#include <linux/device.h>
#include <linux/errno.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/sysfs.h>

#include "smb-cpld-i2c.h"

/* Common SMB CPLD attributes */
const struct regbit_sysfs_config smb_cpld_common_attrs[] = {
    /*
     * FW version @ address/offset 0x1 (major) and 0x0 (minor).
     */
    {
        .name = "cpld_sub_ver",
        .mode = REGBIT_FMODE_RO,
        .reg_addr = CPLD_REG_REV_MINOR,
        .bit_offset = 0,
        .num_bits = 8,
    },
    {
        .name = "cpld_ver",
        .mode = REGBIT_FMODE_RO,
        .reg_addr = CPLD_REG_REV_MAJOR,
        .bit_offset = 0,
        .num_bits = 8,
    },

    /*
     * Power Ctrl/Stat register @ address/offset 0x5.
     */
    {
        .name = "switch_card_pwr_status",
        .mode = REGBIT_FMODE_RO,
        .reg_addr = CPLD_REG_CTRL_STS,
        .bit_offset = 0,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: switch card power bad\n"
                    "1: switch card power good",
    },

    /*
     * IDPROM_WP @ address/offset 0x22.
     */
    {
        .name = "idprom_wp",
        .mode = REGBIT_FMODE_RW,
        .reg_addr = CPLD_REG_IDPROM_WP,
        .bit_offset = 0,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: IDPROM write-protect disabled\n"
                    "1: IDPROM write-protect enabled (default)",
    },

    /*
     * SCD_FPGA_STA @ address/offset 0xA.
     */
    {
        .name = "scd_config_done",
        .mode = REGBIT_FMODE_RO,
        .reg_addr = CPLD_REG_SCD_FPGA_STA,
        .bit_offset = 0,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: SCD FPGA configuration not done yet\n"
                    "1: SCD FPGA configuration done",
    },
    {
        .name = "scd_config",
        .mode = REGBIT_FMODE_RW,
        .reg_addr = CPLD_REG_SCD_FPGA_STA,
        .bit_offset = 3,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: normal operation. Default\n"
                    "1: initiate SCD FPGA re-configuration",
    },
    {
        .name = "scd_hold",
        .mode = REGBIT_FMODE_RW,
        .reg_addr = CPLD_REG_SCD_FPGA_STA,
        .bit_offset = 4,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: normal operation. Default\n"
                    "1: hold SCD output for SCD hitless update",
    },
    {
        .name = "scd_reset",
        .mode = REGBIT_FMODE_RW,
        .reg_addr = CPLD_REG_SCD_FPGA_STA,
        .bit_offset = 5,
        .num_bits = 1,
        .flags = RBS_FLAG_SHOW_NOTES,
        .help_str = "0: normal operation. Default\n"
                    "1: reset SCD",
    },
};

const int smb_cpld_common_attrs_count = ARRAY_SIZE(smb_cpld_common_attrs);

int smb_cpld_fw_ver_read(struct i2c_client *client, char *buf,
                         const char *device_name) {
  int ret;
  u8 major_rev, minor_rev;

  ret = i2c_smbus_read_byte_data(client, CPLD_REG_REV_MAJOR);
  if (ret < 0)
    return ret;
  major_rev = (u8)ret;

  ret = i2c_smbus_read_byte_data(client, CPLD_REG_REV_MINOR);
  if (ret < 0)
    return ret;
  minor_rev = (u8)ret;

  if (buf) {
    return sprintf(buf, "%u.%u\n", major_rev, minor_rev);
  } else {
    dev_info(&client->dev, "%s cpld revision: %02x.%02x\n", device_name,
             major_rev, minor_rev);
    return 0;
  }
}

ssize_t smb_cpld_fw_ver_show(struct device *dev, struct device_attribute *attr,
                             char *buf) {
  struct i2c_client *client = to_i2c_client(dev);
  return smb_cpld_fw_ver_read(client, buf, NULL);
}

static DEVICE_ATTR(fw_ver, 0444, smb_cpld_fw_ver_show, NULL);

int smb_cpld_create_fw_ver_attr(struct i2c_client *client) {
  int ret;

  ret = sysfs_create_file(&client->dev.kobj, &dev_attr_fw_ver.attr);
  if (ret < 0) {
    dev_err(&client->dev, "could not create %s attribute for cpld: %d",
            dev_attr_fw_ver.attr.name, ret);
  }
  return ret;
}

int smb_cpld_init_with_attrs(struct device *dev,
                             const struct regbit_sysfs_config *driver_attrs,
                             int driver_attrs_count) {
  struct regbit_sysfs_config *combined_attrs;
  int total_count = smb_cpld_common_attrs_count + driver_attrs_count;
  int ret;

  combined_attrs = devm_kzalloc(
      dev, total_count * sizeof(struct regbit_sysfs_config), GFP_KERNEL);
  if (!combined_attrs)
    return -ENOMEM;

  /* Copy common attributes first */
  memcpy(combined_attrs, smb_cpld_common_attrs,
         smb_cpld_common_attrs_count * sizeof(struct regbit_sysfs_config));

  /* Copy driver-specific attributes */
  memcpy(combined_attrs + smb_cpld_common_attrs_count, driver_attrs,
         driver_attrs_count * sizeof(struct regbit_sysfs_config));

  ret = regbit_sysfs_init_i2c(dev, combined_attrs, total_count);
  return ret;
}

void smb_cpld_i2c_remove(struct i2c_client *client) {
  /* Must clean up fw_ver */
  sysfs_remove_file(&client->dev.kobj, &dev_attr_fw_ver.attr);
}

MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("SMB CPLD I2C Common Functions");
MODULE_LICENSE("GPL");
