/*
 * Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
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
 * SCD PCI driver extension implementing reload cause functionality
 *
 * Mechanism to add reload cause functionality to SCD PCI driver
 *
 */

#include <linux/workqueue.h>
#include <linux/rtc.h>
#include <linux/mutex.h>
#include "scd-reload-cause-pci.h"

#define RTC_UPDATE_INTERVAL			(10U)
#define MILLENIUM_UNIX_TIMESTAMP		(946684800U)

/* Macros for reload cause register addresses along with their indices in the memory map database */
#define LATCHED_RELOAD_CAUSE_REG_OFFSET		(0x4f80)
#define LATCHED_RELOAD_CAUSE_REG_MAP_INDEX	(0U)
#define TIMESTAMP_FRACTIONAL_SEC_REG_OFFSET	(0x4f84)
#define TIMESTAMP_FRACTIONAL_SEC_REG_MAP_INDEX	(1U)
#define TIMESTAMP_SEC_REG_OFFSET		(0x4f88)
#define TIMESTAMP_SEC_REG_MAP_INDEX		(2U)
#define RELOAD_CAUSE_CTRL_REG_OFFSET		(0x4f98)
#define RELOAD_CAUSE_CTRL_REG_MAP_INDEX		(3U)
#define RTC_FRACTIONAL_SEC_REG_OFFSET		(0x4fa8)
#define RTC_FRACTIONAL_SEC_REG_MAP_INDEX	(4U)
#define RTC_SEC_REG_OFFSET			(0x4fac)
#define RTC_SEC_REG_MAP_INDEX			(5U)
/* Scratchpad register is not stored in the memory map database */
#define SCRATCHPAD_REG_OFFSET			(0x130)

#define DEFINE_REG_MAP(reg_offset)				\
{								\
	.offset = reg_offset					\
}

struct mapped_register reload_cause_registers[] = {
	DEFINE_REG_MAP(LATCHED_RELOAD_CAUSE_REG_OFFSET),
	DEFINE_REG_MAP(TIMESTAMP_FRACTIONAL_SEC_REG_OFFSET),
	DEFINE_REG_MAP(TIMESTAMP_SEC_REG_OFFSET),
	DEFINE_REG_MAP(RELOAD_CAUSE_CTRL_REG_OFFSET),
	DEFINE_REG_MAP(RTC_FRACTIONAL_SEC_REG_OFFSET),
	DEFINE_REG_MAP(RTC_SEC_REG_OFFSET)
};

struct encoded_reload_cause fairywren_scd_reload_causes[] = {
	DEFINE_RELOAD_CAUSE(0x01, "Overtemp"),
	DEFINE_RELOAD_CAUSE(0x08, "Requested by Software"),
	DEFINE_RELOAD_CAUSE(0x0A, "12V input voltage fault"),
	DEFINE_RELOAD_CAUSE(0x0C, "CPU fault - catastrophic error"),
	DEFINE_RELOAD_CAUSE(0x0D, "CPU sleep mode"),
	DEFINE_RELOAD_CAUSE(0x20, "P3V3_ALW fault"),
	DEFINE_RELOAD_CAUSE(0x21, "P1V2_CPLD fault"),
	DEFINE_RELOAD_CAUSE(0x22, "P5V0 fault"),
	DEFINE_RELOAD_CAUSE(0x23, "P3V3_ETH fault"),
	DEFINE_RELOAD_CAUSE(0x24, "P1V0_MSW fault"),
	DEFINE_RELOAD_CAUSE(0x28, "P3V3_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x29, "P1V8_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x2A, "P1V05_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x2B, "PVNN_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x2C, "P1V8_VCCIN_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x2D, "P1V0_PCIE_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x2E, "PVDDQ_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x31, "PCH_PWROK_CPU fault"),
	DEFINE_RELOAD_CAUSE(0x32, "RSMRST_L fault"),
	DEFINE_RELOAD_CAUSE(0x33, "BMC_PG fault"),
	DEFINE_RELOAD_CAUSE(0x34, "P1V2_BMC fault"),
	DEFINE_RELOAD_CAUSE(0x35, "P2V5_BMC fault"),
	DEFINE_RELOAD_CAUSE(0x36, "P3V3_BMC fault"),
	DEFINE_RELOAD_CAUSE(0x37, "P1V8_BMC fault"),
	DEFINE_RELOAD_CAUSE(0x38, "P3V3_RGMII fault"),
	DEFINE_RELOAD_CAUSE(0x39, "P2V5_CPLD fault"),
	DEFINE_RELOAD_CAUSE(0x3A, "P0V96_I226 fault"),
	DEFINE_RELOAD_CAUSE(0x3B, "P1V0_BMC fault"),
	DEFINE_RELOAD_CAUSE(0x3C, "Command CPU Power Off"),
	DEFINE_RELOAD_CAUSE(0x3D, "CPU Error (ERROR_N[2:0])"),
	DEFINE_RELOAD_CAUSE(0x3E, "CPU DRAM Power OK")
};

#define FAIRYWREN_SCD_FAULT_COUNT			ARRAY_SIZE(fairywren_scd_reload_causes)
#define FAIRYWREN_SCD_RELOAD_CAUSE_CONTROL_CLEAR_BITS	(0x1)

static bool periodic_task_started;
static DEFINE_MUTEX(periodic_task_mutex);

static void workqueue_func(struct work_struct *work);
static DECLARE_DELAYED_WORK(scd_delayed_work, workqueue_func);
static void workqueue_func(struct work_struct *work)
{
	time64_t cur_time;

	cur_time = ktime_get_real_seconds();
	cur_time -= MILLENIUM_UNIX_TIMESTAMP;
	schedule_delayed_work(&scd_delayed_work, RTC_UPDATE_INTERVAL*HZ);

	iowrite32(0, reload_cause_registers[RTC_FRACTIONAL_SEC_REG_MAP_INDEX].mem);
	iowrite32((u32)cur_time, reload_cause_registers[RTC_SEC_REG_MAP_INDEX].mem);
}

void start_reload_cause_periodic_task(void)
{
	bool task_running;

	mutex_lock(&periodic_task_mutex);
	task_running = periodic_task_started;
	periodic_task_started = true;
	mutex_unlock(&periodic_task_mutex);
	if (task_running == false)
		schedule_delayed_work(&scd_delayed_work, RTC_UPDATE_INTERVAL*HZ);
}

void stop_reload_cause_periodic_task(void)
{
	bool task_running;

	mutex_lock(&periodic_task_mutex);
	task_running = periodic_task_started;
	periodic_task_started = false;
	mutex_unlock(&periodic_task_mutex);
	if (task_running == true)
		cancel_delayed_work_sync(&scd_delayed_work);
	mutex_destroy(&periodic_task_mutex);
}

void get_reload_cause_register_map(struct mapped_register **reg_map, size_t *reg_count)
{
	*reg_map = reload_cause_registers;
	*reg_count = sizeof(reload_cause_registers) / sizeof(struct mapped_register);
}

u32 get_reload_cause_scratchpad_reg_offset(void)
{
	return SCRATCHPAD_REG_OFFSET;
}

int process_reload_cause(struct device *dev)
{
	u32 reg_val;
	int ret_val = 0;
	u8 fault_cause;
	size_t fault_loop;
	u32 fault_timestamp = 0;
	time64_t rtc_counter_val;
	struct rtc_time rtc_time_val;

	reg_val = ioread32(reload_cause_registers[LATCHED_RELOAD_CAUSE_REG_MAP_INDEX].mem);
	fault_cause = (u8)reg_val;
	for (fault_loop = 0; fault_loop < FAIRYWREN_SCD_FAULT_COUNT; fault_loop++) {
		if (fairywren_scd_reload_causes[fault_loop].id == fault_cause)
			break;
	}
	if (fault_loop == FAIRYWREN_SCD_FAULT_COUNT) {
		dev_info(dev, "scd fault not found in list of reload causes\n");
		ret_val = -1;
	} else {
		dev_info(dev, "scd reload cause: %s\n",
			fairywren_scd_reload_causes[fault_loop].description);
	}

	fault_timestamp = ioread32(reload_cause_registers[TIMESTAMP_SEC_REG_MAP_INDEX].mem);
	rtc_counter_val = (time64_t)fault_timestamp + MILLENIUM_UNIX_TIMESTAMP;
	rtc_time64_to_tm(rtc_counter_val, &rtc_time_val);
	dev_info(dev, "scd reload cause timestamp: %d-%d-%d, %d:%d:%d\n",
		rtc_time_val.tm_mon + 1,
		rtc_time_val.tm_mday,
		rtc_time_val.tm_year + 1900,
		rtc_time_val.tm_hour,
		rtc_time_val.tm_min,
		rtc_time_val.tm_sec);

	iowrite32(FAIRYWREN_SCD_RELOAD_CAUSE_CONTROL_CLEAR_BITS, reload_cause_registers[RELOAD_CAUSE_CTRL_REG_MAP_INDEX].mem);

	return ret_val;
}

