/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
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
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

#include <unistd.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>

/*
 * "fbiob-ioctl.h" is located in "kmods" directory, being shared by both
 * kernel drivers and user space programs.
 */
#include "fbiob-ioctl.h"

#define DFT_CDEV_PATH	"/dev/fbiob_3475.0001.3475.0003"

/*
 * Default controller settings.
 */
static struct fbiob_spi_data dft_spi_data = {
	.num_spidevs = 1,
	.spidevs = {
		{
			.modalias = "spi-nor",
			.max_speed_hz = 25000000,
			.chip_select = 0,
		},
	},
};

static struct fbiob_i2c_data dft_i2c_data = {
	.bus_freq_hz = 0,
	.num_channels = 0,
};

static struct fbiob_led_data dft_led_data = {
	.port_num = 1,
	.led_idx = 1,
};

static struct fbiob_xcvr_data dft_xcvr_data = {
	.port_num = 1,
};

static void usage(const char *prog_name)
{
	int i;
	struct {
		const char *opt;
		const char *desc;
	} options[] = {
		{"-h|--help", "print this help message"},
		{"-p|--cdev-path", "character device path"},
		{"-c|--csr-offset", "control/status registers offset"},
		{"-d|--iobuf-offset", "controller IO buffer offset"},
		{"-n|--i2c-chan-num", "number of I2C controller's channels"},
		{"-i|--port-number", "port number associated with device (1-based)"},
		{"-l|--led-idx", "support multiple LED instances per port/type (1-based)"},
		{NULL, NULL},
	};

	printf("Usage: %s [options] <add|remove> <device-name> <inst-id>\n",
		prog_name);

	printf("\nAvailable options:\n");
	for (i = 0; options[i].opt != NULL; i++) {
		printf("    %-12s - %s\n", options[i].opt, options[i].desc);
	}
}

static void aux_data_init(struct fbiob_aux_data *aux_data,
			  const char *name,
			  __u32 inst_id,
			  __u32 csr_offset,
			  __u32 iobuf_offset)
{

	memset(aux_data, 0, sizeof(*aux_data));
	snprintf(aux_data->id.name, sizeof(aux_data->id.name), "%s", name);
	aux_data->id.id = inst_id;
	aux_data->csr_offset = csr_offset;
	aux_data->iobuf_offset = iobuf_offset;

	/*
	 * FIXME: need to improve controller specific settings
	 */
	if (strstr(name, "spi"))
		memcpy(&aux_data->spi_data, &dft_spi_data,
			sizeof(aux_data->spi_data));
	else if (strstr(name, "i2c"))
		memcpy(&aux_data->i2c_data, &dft_i2c_data,
			sizeof(aux_data->i2c_data));
	else if (strstr(name, "led"))
		memcpy(&aux_data->led_data, &dft_led_data,
			sizeof(aux_data->led_data));
	else if (strstr(name, "xcvr"))
		memcpy(&aux_data->xcvr_data, &dft_xcvr_data,
			sizeof(aux_data->xcvr_data));
}

int main(int argc, char **argv)
{
	int fd, ret;
	__u32 inst_id;
	unsigned long cmd;
	const char *action, *dev_name;
	struct fbiob_aux_data aux_data;
	const char *cdev_path = DFT_CDEV_PATH;
	__u32 csr_offset = FBIOB_INVALID_OFFSET;
	__u32 iobuf_offset = FBIOB_INVALID_OFFSET;
	struct option long_opts[] = {
		{"help",		no_argument,		NULL,	'h'},
		{"cdev-path",		required_argument,	NULL,	'p'},
		{"csr-offset",		required_argument,	NULL,	'c'},
		{"iobuf-offset",	required_argument,	NULL,	'd'},
		{"i2c-chan-num",	required_argument,	NULL,	'n'},
		{"port-number",		required_argument,	NULL,	'i'},
		{"led-idx",			required_argument,	NULL,	'l'},
		{NULL,			0,			NULL,	0},
	};

	while (1) {
		int ret;
		int opt_index = 0;

		ret = getopt_long(argc, argv, "hp:c:d:n:i:l:", long_opts, &opt_index);
		if (ret == -1)
			break;	/* end of arguments */

		switch (ret) {
		case 'h':
			usage(argv[0]);
			return 0;

		case 'p':
			cdev_path = optarg;
			break;

		case 'c':
			csr_offset = (__u32)strtol(optarg, NULL, 0);
			break;

		case 'd':
			iobuf_offset = (__u32)strtol(optarg, NULL, 0);
			break;

		case 'n':
			dft_i2c_data.num_channels = (__u32)strtol(optarg, NULL, 0);
			break;

		case 'i':
			dft_led_data.port_num = (__u32)strtol(optarg, NULL, 0);
			dft_xcvr_data.port_num = (__u32)strtol(optarg, NULL, 0);
			break;

		case 'l':
			dft_led_data.led_idx = (__u32)strtol(optarg, NULL, 0);
			break;

		default:
			return EINVAL;
		}
	} /* while */

	if ((optind + 3) > argc) {
		fprintf(stderr, "Error: missing command line argument!\n\n");
		usage(argv[0]);
		return EINVAL;
	}
	action = argv[optind++];
	dev_name = argv[optind++];
	inst_id = (__u32)strtol(argv[optind++], NULL, 0);

	if (!strcmp(action, "add")) {
		if (csr_offset == FBIOB_INVALID_OFFSET) {
			fprintf(stderr, "Error: csr-offset is invalid/missing!\n");
			return EINVAL;
		}
		cmd = FBIOB_IOC_NEW_DEVICE;
	} else if (!strcmp(action, "remove")) {
		cmd = FBIOB_IOC_DEL_DEVICE;
	} else {
		fprintf(stderr, "Error: unknown action <%s>!\n", action);
		fprintf(stderr, "Supported actions: add, remove\n");
		return EINVAL;
	}

	/*
	 * Dump command line arguments (for debugging purposes).
	 */
	printf("%s %s.%u, csr=0x%x, iobuf=0x%x\n",
		action, dev_name, inst_id, csr_offset, iobuf_offset);

	fd = open(cdev_path, O_RDWR);
	if (fd < 0) {
		fprintf(stderr, "failed to open %s: %s\n",
			cdev_path, strerror(errno));
		return errno;
	}

	aux_data_init(&aux_data, dev_name, inst_id, csr_offset, iobuf_offset);
	ret = ioctl(fd, cmd, &aux_data);
	if (ret < 0) {
		fprintf(stderr, "ioctl (%s %s %d) failed: %s\n",
			action, dev_name, inst_id, strerror(errno));
		close(fd);
		return errno;
	}

	close(fd);
	return 0;
}
