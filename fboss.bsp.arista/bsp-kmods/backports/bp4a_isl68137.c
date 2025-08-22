// SPDX-License-Identifier: GPL-2.0+
/*
 * Hardware monitoring driver for Renesas Digital Multiphase Voltage Regulators
 *
 * Copyright (c) 2017 Google Inc
 * Copyright (c) 2020 Renesas Electronics America
 *
 */

#include <linux/err.h>
#include <linux/hwmon-sysfs.h>
#include <linux/i2c.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/string.h>
#include <linux/sysfs.h>

#include "pmbus.h"

#define ISL68137_VOUT_AVS	0x30
#define RAA_DMPVR2_READ_VMON	0xc8

enum chips {
	isl68137,
	isl68220,
	isl68221,
	isl68222,
	isl68223,
	isl68224,
	isl68225,
	isl68226,
	isl68227,
	isl68229,
	isl68233,
	isl68239,
	isl69222,
	isl69223,
	isl69224,
	isl69225,
	isl69227,
	isl69228,
	isl69234,
	isl69236,
	isl69239,
	isl69242,
	isl69243,
	isl69247,
	isl69248,
	isl69254,
	isl69255,
	isl69256,
	isl69259,
	isl69260,
	isl69268,
	isl69269,
	isl69298,
	raa228000,
	raa228004,
	raa228006,
	raa228228,
	raa229001,
	raa229004,
};

enum variants {
	raa_dmpvr1_2rail,
	raa_dmpvr2_1rail,
	raa_dmpvr2_2rail,
	raa_dmpvr2_2rail_nontc,
	raa_dmpvr2_3rail,
	raa_dmpvr2_hv,
};

#define ISL_INFO_STR_MAX_LEN	256
#define to_isl68137_priv(x) container_of(x, struct isl68137_priv, driver_info)
#define ISL68226_MFR_MODEL_CMD_CODE	0x9a
#define ISL68226_MFR_MODEL_PMBUS_BLOCK_LEN	4
#define ISL68226_CONFIG_DMA_ADDR_CMD_CODE	0xc7
#define ISL68226_CONFIG_DMA_DATA_CMD_CODE	0xc5
#define ISL68226_CONFIG_DMA_FINALIZE_CMD_CODE	0xe7
#define ISL68226_CONFIG_DMA_I2C_DATA_LEN	5
#define ISL68226_MERU800BFA_OSFP_D_FW_REV_05	"5"
#define ISL68226_MERU800BFA_OSFP_D_MFR_MODEL	"0x200101"

struct isl68137_priv {
	struct pmbus_driver_info driver_info;
	char fw_ver[ISL_INFO_STR_MAX_LEN];
	char mfr_model[ISL_INFO_STR_MAX_LEN];
};
struct isl68226_inductor_config_reg {
	u32 addr;
	u8 val[ISL68226_CONFIG_DMA_I2C_DATA_LEN];
};

static const struct i2c_device_id bp4a_raa_dmpvr_id[];

static ssize_t isl68137_avs_enable_show_page(struct i2c_client *client,
					     int page,
					     char *buf)
{
	int val = pmbus_read_byte_data(client, page, PMBUS_OPERATION);

	return sprintf(buf, "%d\n",
		       (val & ISL68137_VOUT_AVS) == ISL68137_VOUT_AVS ? 1 : 0);
}

static ssize_t isl68137_avs_enable_store_page(struct i2c_client *client,
					      int page,
					      const char *buf, size_t count)
{
	int rc, op_val;
	bool result;

	rc = kstrtobool(buf, &result);
	if (rc)
		return rc;

	op_val = result ? ISL68137_VOUT_AVS : 0;

	/*
	 * Writes to VOUT setpoint over AVSBus will persist after the VRM is
	 * switched to PMBus control. Switching back to AVSBus control
	 * restores this persisted setpoint rather than re-initializing to
	 * PMBus VOUT_COMMAND. Writing VOUT_COMMAND first over PMBus before
	 * enabling AVS control is the workaround.
	 */
	if (op_val == ISL68137_VOUT_AVS) {
		rc = pmbus_read_word_data(client, page, 0xff,
					  PMBUS_VOUT_COMMAND);
		if (rc < 0)
			return rc;

		rc = pmbus_write_word_data(client, page, PMBUS_VOUT_COMMAND,
					   rc);
		if (rc < 0)
			return rc;
	}

	rc = pmbus_update_byte_data(client, page, PMBUS_OPERATION,
				    ISL68137_VOUT_AVS, op_val);

	return (rc < 0) ? rc : count;
}

static ssize_t isl68137_avs_enable_show(struct device *dev,
					struct device_attribute *devattr,
					char *buf)
{
	struct i2c_client *client = to_i2c_client(dev->parent);
	struct sensor_device_attribute *attr = to_sensor_dev_attr(devattr);

	return isl68137_avs_enable_show_page(client, attr->index, buf);
}

static ssize_t isl68137_avs_enable_store(struct device *dev,
				struct device_attribute *devattr,
				const char *buf, size_t count)
{
	struct i2c_client *client = to_i2c_client(dev->parent);
	struct sensor_device_attribute *attr = to_sensor_dev_attr(devattr);

	return isl68137_avs_enable_store_page(client, attr->index, buf, count);
}

static ssize_t isl68226_mfr_model_show(struct device *dev,
				    struct device_attribute *devattr,
				    char *buf)
{
	struct i2c_client *client = to_i2c_client(dev->parent);
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct isl68137_priv *priv = to_isl68137_priv(info);

	return sprintf(buf, "%s\n", priv->mfr_model);
}

static ssize_t isl68226_fw_ver_show(struct device *dev,
				    struct device_attribute *devattr,
				    char *buf)
{
	struct i2c_client *client = to_i2c_client(dev->parent);
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct isl68137_priv *priv = to_isl68137_priv(info);

	return sprintf(buf, "%s\n", priv->fw_ver);
}

static SENSOR_DEVICE_ATTR_RW(avs0_enable, isl68137_avs_enable, 0);
static SENSOR_DEVICE_ATTR_RW(avs1_enable, isl68137_avs_enable, 1);
static SENSOR_DEVICE_ATTR_RO(fw_ver, isl68226_fw_ver, 0);
static SENSOR_DEVICE_ATTR_RO(mfr_model, isl68226_mfr_model, 0);

static struct attribute *enable_attrs[] = {
	&sensor_dev_attr_avs0_enable.dev_attr.attr,
	&sensor_dev_attr_avs1_enable.dev_attr.attr,
	NULL,
};

static const struct attribute_group enable_group = {
	.attrs = enable_attrs,
};

static const struct attribute_group *isl68137_attribute_groups[] = {
	&enable_group,
	NULL,
};

static struct attribute *fw_ver_attrs[] = {
	&sensor_dev_attr_fw_ver.dev_attr.attr,
	NULL,
};

static const struct attribute_group fw_ver_group = {
	.attrs = fw_ver_attrs,
};

static struct attribute *mfr_model_attrs[] = {
	&sensor_dev_attr_mfr_model.dev_attr.attr,
	NULL,
};

static const struct attribute_group mfr_model_group = {
	.attrs = mfr_model_attrs,
};

static const struct attribute_group *isl68226_attribute_groups[] = {
	&fw_ver_group,
	&mfr_model_group,
	NULL,
};

static int raa_dmpvr2_read_word_data(struct i2c_client *client, int page,
				     int phase, int reg)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_READ_VMON:
		ret = pmbus_read_word_data(client, page, phase,
					   RAA_DMPVR2_READ_VMON);
		break;
	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static struct pmbus_driver_info raa_dmpvr_info = {
	.pages = 3,
	.format[PSC_VOLTAGE_IN] = direct,
	.format[PSC_VOLTAGE_OUT] = direct,
	.format[PSC_CURRENT_IN] = direct,
	.format[PSC_CURRENT_OUT] = direct,
	.format[PSC_POWER] = direct,
	.format[PSC_TEMPERATURE] = direct,
	.m[PSC_VOLTAGE_IN] = 1,
	.b[PSC_VOLTAGE_IN] = 0,
	.R[PSC_VOLTAGE_IN] = 2,
	.m[PSC_VOLTAGE_OUT] = 1,
	.b[PSC_VOLTAGE_OUT] = 0,
	.R[PSC_VOLTAGE_OUT] = 3,
	.m[PSC_CURRENT_IN] = 1,
	.b[PSC_CURRENT_IN] = 0,
	.R[PSC_CURRENT_IN] = 2,
	.m[PSC_CURRENT_OUT] = 1,
	.b[PSC_CURRENT_OUT] = 0,
	.R[PSC_CURRENT_OUT] = 1,
	.m[PSC_POWER] = 1,
	.b[PSC_POWER] = 0,
	.R[PSC_POWER] = 0,
	.m[PSC_TEMPERATURE] = 1,
	.b[PSC_TEMPERATURE] = 0,
	.R[PSC_TEMPERATURE] = 0,
	.func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_IIN | PMBUS_HAVE_PIN
	    | PMBUS_HAVE_STATUS_INPUT | PMBUS_HAVE_TEMP | PMBUS_HAVE_TEMP2
	    | PMBUS_HAVE_TEMP3 | PMBUS_HAVE_STATUS_TEMP
	    | PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT
	    | PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT | PMBUS_HAVE_POUT
		| PMBUS_HAVE_VMON,
	.func[1] = PMBUS_HAVE_IIN | PMBUS_HAVE_PIN | PMBUS_HAVE_STATUS_INPUT
	    | PMBUS_HAVE_TEMP | PMBUS_HAVE_TEMP3 | PMBUS_HAVE_STATUS_TEMP
	    | PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT | PMBUS_HAVE_IOUT
	    | PMBUS_HAVE_STATUS_IOUT | PMBUS_HAVE_POUT,
	.func[2] = PMBUS_HAVE_IIN | PMBUS_HAVE_PIN | PMBUS_HAVE_STATUS_INPUT
	    | PMBUS_HAVE_TEMP | PMBUS_HAVE_TEMP3 | PMBUS_HAVE_STATUS_TEMP
	    | PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT | PMBUS_HAVE_IOUT
	    | PMBUS_HAVE_STATUS_IOUT | PMBUS_HAVE_POUT,
};

static int isl68226_cache_fw_ver(struct i2c_client *client,
				 struct isl68137_priv *priv)
{
	int ret;

	u8 fw_ver;

	u8 fw_ver_block[I2C_SMBUS_BLOCK_MAX + 1];

	ret = i2c_smbus_read_block_data(client, 0x9B, fw_ver_block);
	if (ret < 0) {
		dev_err(&client->dev, "Failed to read ISL firmware version block");
		return ret;
	}

	fw_ver = fw_ver_block[0];
	snprintf(priv->fw_ver, ISL_INFO_STR_MAX_LEN, "%d", fw_ver);

	return 0;
}

static int isl68226_cache_mfr_model(struct i2c_client *client,
				struct isl68137_priv *priv)
{
	u8 mfr_model_block[I2C_SMBUS_BLOCK_MAX];
	u32 mfr_model_val;
	int ret;

	ret = i2c_smbus_read_block_data(client, ISL68226_MFR_MODEL_CMD_CODE, mfr_model_block);
	if (ret < 0) {
		dev_err(&client->dev, "Failed to read ISL model number");
		return ret;
	}
	if (ret != ISL68226_MFR_MODEL_PMBUS_BLOCK_LEN) {
		dev_err(&client->dev, "Unexpected length for ISL model number");
		return -EINVAL;
	}
	memcpy(&mfr_model_val, mfr_model_block, sizeof(u32));
	snprintf(priv->mfr_model, ISL_INFO_STR_MAX_LEN, "0x%x", mfr_model_val);

	return 0;
}

static int isl68226_meru800bfa_osfp_d_ver_05_quirk(struct i2c_client *client,
						struct isl68137_priv *priv)
{
	int ret;
	static const struct isl68226_inductor_config_reg isl68226_inductor_config_ver_06_regs[] = {
		/* DMA register 0xea20 has value 0x4d930f83 in 06 config */
		{0xea20, {ISL68226_CONFIG_DMA_DATA_CMD_CODE, 0x83, 0x0f, 0x93, 0x4d}},
		/* DMA register 0xea1f has value 0x031a04a7 in 06 config */
		{0xea1f, {ISL68226_CONFIG_DMA_DATA_CMD_CODE, 0xa7, 0x04, 0x1a, 0x03}},
		/* DMA register 0xea21 has value 0x08000122 in 06 config */
		{0xea21, {ISL68226_CONFIG_DMA_DATA_CMD_CODE, 0x22, 0x01, 0x00, 0x08}}};

	dev_info(&client->dev, "Applying inductor config ver 06 to meru800bfa OSFP D ISL68226\n");
	for (size_t i = 0; i < sizeof(isl68226_inductor_config_ver_06_regs) / sizeof(struct isl68226_inductor_config_reg); i++) {
		ret = i2c_smbus_write_word_data(client, ISL68226_CONFIG_DMA_ADDR_CMD_CODE, isl68226_inductor_config_ver_06_regs[i].addr);
		if (ret < 0) {
			dev_err(&client->dev, "Failed to write DMA address: error %d\n", ret);
			return ret;
		}
		ret = i2c_master_send(client, isl68226_inductor_config_ver_06_regs[i].val, ISL68226_CONFIG_DMA_I2C_DATA_LEN);
		if (ret < 0) {
			dev_err(&client->dev, "Failed to write DMA data: error %d\n", ret);
			return ret;
		}
		ret = i2c_smbus_write_word_data(client, ISL68226_CONFIG_DMA_FINALIZE_CMD_CODE, 0x0001);
		if (ret < 0) {
			dev_err(&client->dev, "Failed to finalize DMA procedure: error %d\n", ret);
			return ret;
		}
	}

	return 0;
}

static int isl68137_probe(struct i2c_client *client)
{
	struct pmbus_driver_info *info;
	struct isl68137_priv *priv;
	int ret;

	priv = devm_kzalloc(&client->dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	info = &priv->driver_info;
	memcpy(info, &raa_dmpvr_info, sizeof(*info));

	switch (i2c_match_id(bp4a_raa_dmpvr_id, client)->driver_data) {
	case raa_dmpvr1_2rail:
		info->pages = 2;
		info->R[PSC_VOLTAGE_IN] = 3;
		info->func[0] &= ~PMBUS_HAVE_VMON;
		info->func[1] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT
		    | PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT
		    | PMBUS_HAVE_POUT;
		info->groups = isl68137_attribute_groups;
		break;
	case raa_dmpvr2_1rail:
		info->pages = 1;
		info->read_word_data = raa_dmpvr2_read_word_data;
		break;
	case raa_dmpvr2_2rail_nontc:
		info->func[0] &= ~PMBUS_HAVE_TEMP3;
		info->func[1] &= ~PMBUS_HAVE_TEMP3;
		fallthrough;
	case raa_dmpvr2_2rail:
		info->pages = 2;
		info->read_word_data = raa_dmpvr2_read_word_data;
		break;
	case raa_dmpvr2_3rail:
		info->read_word_data = raa_dmpvr2_read_word_data;
		break;
	case raa_dmpvr2_hv:
		info->pages = 1;
		info->R[PSC_VOLTAGE_IN] = 1;
		info->m[PSC_VOLTAGE_OUT] = 2;
		info->R[PSC_VOLTAGE_OUT] = 2;
		info->m[PSC_CURRENT_IN] = 2;
		info->m[PSC_POWER] = 2;
		info->R[PSC_POWER] = -1;
		info->read_word_data = raa_dmpvr2_read_word_data;
		break;
	default:
		return -ENODEV;
	}

	/*
	 * Cache DPM firmware version, for Meta DC environment only.
	 */
	if (!strcmp(client->name, "bp4a_isl68226")) {
		isl68226_cache_fw_ver(client, priv);
		isl68226_cache_mfr_model(client, priv);
		info->groups = isl68226_attribute_groups;
		/* ISL68226 model and FW version are stored as strings in priv->fw_ver */
		if (strcmp(priv->mfr_model, ISL68226_MERU800BFA_OSFP_D_MFR_MODEL) == 0) {
			if (strcmp(priv->fw_ver, ISL68226_MERU800BFA_OSFP_D_FW_REV_05) == 0) {
				ret = isl68226_meru800bfa_osfp_d_ver_05_quirk(client, priv);
				if (ret < 0) {
					dev_err(&client->dev, "Failed to update ISL68226 inductor config");
					return ret;
				}
			}
		}
	}

	return pmbus_do_probe(client, info);
}

static const struct i2c_device_id bp4a_raa_dmpvr_id[] = {
	{"bp4a_isl68226", raa_dmpvr2_3rail},
	{}
};

MODULE_DEVICE_TABLE(i2c, bp4a_raa_dmpvr_id);

/* This is the driver that will be inserted */
static struct i2c_driver bp4a_isl68137_driver = {
	.driver = {
		   .name = "bp4a_isl68137",
		   },
	.probe = isl68137_probe,
	.id_table = bp4a_raa_dmpvr_id,
};

module_i2c_driver(bp4a_isl68137_driver);

MODULE_AUTHOR("Maxim Sloyko <maxims@google.com>");
MODULE_DESCRIPTION("PMBus driver for Renesas digital multiphase voltage regulators");
MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
