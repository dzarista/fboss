/* Copyright (c) 2024 Arista Networks, Inc.
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

#ifndef __SCD_RELOAD_CAUSE_PCI_H__
#define __SCD_RELOAD_CAUSE_PCI_H__

#include "scd-reload-cause.h"
#include "reg-access-pci.h"
#include <linux/device.h>

void start_reload_cause_periodic_task(void);
void stop_reload_cause_periodic_task(void);
void get_reload_cause_register_map(struct mapped_register **reg_map, size_t *reg_count);
u32 get_reload_cause_scratchpad_reg_offset(void);
int process_reload_cause(struct device *dev);

#endif /* __SCD_RELOAD_CAUSE_PCI_H__ */

