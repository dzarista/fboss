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
 */

#ifndef __AUCD9000_GLATH06A_64O_RELOAD_CAUSE_H__
#define __AUCD9000_GLATH06A_64O_RELOAD_CAUSE_H__

#include "aucd9000-reload-cause.h"

/*
 * Encoded reload causes for GLATH06A-64O SMB UCD90320.
 */
const struct encoded_reload_cause glath06a_aucd90320_encoded_gpis[] = {
	DEFINE_RELOAD_CAUSE(1, "SUP Unseated"),
	DEFINE_RELOAD_CAUSE(2, "CPU Fault"),
	DEFINE_RELOAD_CAUSE(3, "SCD Watchdog Timeout"),
	DEFINE_RELOAD_CAUSE(4, "Power Loss"),
	DEFINE_RELOAD_CAUSE(5, "Over-Temperature"),
	DEFINE_RELOAD_CAUSE(6, "SCD CRC"),
};

const struct encoded_reload_cause glath06a_aucd90320_encoded_rails[] = {
	DEFINE_RELOAD_CAUSE(1, "POS12V"),
	DEFINE_RELOAD_CAUSE(2, "POS3V3"),
	DEFINE_RELOAD_CAUSE(3, "POS1V8_0"),
	DEFINE_RELOAD_CAUSE(4, "POS0V75_TRVDD_0"),
	DEFINE_RELOAD_CAUSE(5, "POS0V75_TRVDD_1"),
	DEFINE_RELOAD_CAUSE(6, "POS0V9_TRVDD_0"),
	DEFINE_RELOAD_CAUSE(7, "POS0V9_TRVDD_1"),
	DEFINE_RELOAD_CAUSE(8, "POS1V5_RVDD_0"),
	DEFINE_RELOAD_CAUSE(9, "POS1V5_RVDD_1"),
	DEFINE_RELOAD_CAUSE(10, "POS3V3_OSFP_LEFT"),
	DEFINE_RELOAD_CAUSE(11, "POS3V3_OSFP_RIGHT"),
	DEFINE_RELOAD_CAUSE(12, "POS5V0"),
	DEFINE_RELOAD_CAUSE(13, "POS0V75_CORE"),
	DEFINE_RELOAD_CAUSE(14, "POS0V75_PHYCORE_0"),
	DEFINE_RELOAD_CAUSE(15, "POS0V72_TRVDD_7"),
	DEFINE_RELOAD_CAUSE(16, "POS3V3_RUNDLE"),
	DEFINE_RELOAD_CAUSE(17, "POS5V0_SNOW_FRONT"),
	DEFINE_RELOAD_CAUSE(18, "POS3V3_SNOW_FRONT"),
	DEFINE_RELOAD_CAUSE(19, "POS5V0_SUNDANCE"),
	DEFINE_RELOAD_CAUSE(20, "POS3V3_SUNDANCE"),
	DEFINE_RELOAD_CAUSE(21, "POS5V0_SUNSHINE_LEFT"),
	DEFINE_RELOAD_CAUSE(22, "POS3V3_SUNSHINE_LEFT"),
	DEFINE_RELOAD_CAUSE(23, "POS5VO_SUNSHINE_RIGHT"),
	DEFINE_RELOAD_CAUSE(24, "POS3V3_SUNSHINE_RIGHT"),
};

#endif /* __AUCD9000_GLATH06A_64O_RELOAD_CAUSE_H__ */