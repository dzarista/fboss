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

#ifndef __AUCD9000_MERU800BFA_RELOAD_CAUSE_H__
#define __AUCD9000_MERU800BFA_RELOAD_CAUSE_H__

#include "aucd9000-reload-cause.h"

/*
 * Encoded reload causes for MERU800BFA SMB UCD90320.
 */
const struct encoded_reload_cause meru800bfa_aucd90320_encoded_gpis[] = {
	DEFINE_RELOAD_CAUSE(1, "SUP Unseated"),
	DEFINE_RELOAD_CAUSE(2, "CPU Fault"),
	DEFINE_RELOAD_CAUSE(3, "SCD Watchdog Timeout"),
	DEFINE_RELOAD_CAUSE(4, "Power Loss"),
	DEFINE_RELOAD_CAUSE(5, "Reset Button"),
	DEFINE_RELOAD_CAUSE(6, "Over-Temperature"),
	DEFINE_RELOAD_CAUSE(7, "SCD CRC"),
	DEFINE_RELOAD_CAUSE(8, "POS3V3_OSFP_A_PGOOD"),
	DEFINE_RELOAD_CAUSE(9, "POS3V3_OSFP_B_PGOOD"),
	DEFINE_RELOAD_CAUSE(10, "POS3V3_OSFP_C_PGOOD"),
	DEFINE_RELOAD_CAUSE(11, "POS3V3_OSFP_D_PGOOD"),
	DEFINE_RELOAD_CAUSE(12, "CPU_PWR"),
	DEFINE_RELOAD_CAUSE(13, "SW_PWR")
};

const struct encoded_reload_cause meru800bfa_aucd90320_encoded_rails[] = {
	DEFINE_RELOAD_CAUSE(1, "POS12V"),
	DEFINE_RELOAD_CAUSE(2, "POS3V3_DKR"),
	DEFINE_RELOAD_CAUSE(3, "POS1V8_DKR"),
	DEFINE_RELOAD_CAUSE(4, "POS1V2_DKR"),
	DEFINE_RELOAD_CAUSE(5, "POS12V_LEFT"),
	DEFINE_RELOAD_CAUSE(6, "POS12V_RIGHT"),
	DEFINE_RELOAD_CAUSE(7, "POS3V3"),
	DEFINE_RELOAD_CAUSE(8, "POS5V0"),
	DEFINE_RELOAD_CAUSE(9, "POS0V75_R0_CORE"),
	DEFINE_RELOAD_CAUSE(10, "POS0V9_R0_ANLG_0"),
	DEFINE_RELOAD_CAUSE(11, "OS0V75_R0_ANLG_0"),
	DEFINE_RELOAD_CAUSE(12, "POS1V2_R0"),
	DEFINE_RELOAD_CAUSE(13, "POS0V9_R0_ANLG_1"),
	DEFINE_RELOAD_CAUSE(14, "POS0V75_R0_ANLG_1"),
	DEFINE_RELOAD_CAUSE(15, "POS1V8_R0"),
	DEFINE_RELOAD_CAUSE(16, "POS0V75_R1_CORE"),
	DEFINE_RELOAD_CAUSE(17, "POS0V9_R1_ANLG_0"),
	DEFINE_RELOAD_CAUSE(18, "POS0V75_R1_ANLG_0"),
	DEFINE_RELOAD_CAUSE(19, "POS1V2_R1"),
	DEFINE_RELOAD_CAUSE(20, "POS0V9_R1_ANLG_1"),
	DEFINE_RELOAD_CAUSE(21, "POS0V75_R1_ANLG_1"),
	DEFINE_RELOAD_CAUSE(22, "POS1V8_R1"),
	DEFINE_RELOAD_CAUSE(23, "POS3V3_OSFP_ABCD")
};

#endif /* __AUCD9000_MERU800BFA_RELOAD_CAUSE_H__ */