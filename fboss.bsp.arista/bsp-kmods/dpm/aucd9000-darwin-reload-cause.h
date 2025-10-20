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

#ifndef __AUCD9000_DARWIN_RELOAD_CAUSE_H__
#define __AUCD9000_DARWIN_RELOAD_CAUSE_H__

#include "aucd9000-reload-cause.h"

/*
 * Encoded reload causes for DARWIN CPU UCD90160.
 */
const struct encoded_reload_cause darwin_aucd90160_encoded_gpis[] = {
	DEFINE_RELOAD_CAUSE(2, "CPU Reset"),
	DEFINE_RELOAD_CAUSE(3, "Over-Temperature"),
	DEFINE_RELOAD_CAUSE(4, "CPU CATERR"),
	DEFINE_RELOAD_CAUSE(5, "Fans Missing")
};

const struct encoded_reload_cause darwin_aucd90160_encoded_rails[] = {
	DEFINE_RELOAD_CAUSE(1, "P1V7VCCIN_VRRDY"),
	DEFINE_RELOAD_CAUSE(2, "P0V6VTT"),
	DEFINE_RELOAD_CAUSE(3, "P1V2VDDQ"),
	DEFINE_RELOAD_CAUSE(4, "P2V5VPP"),
	DEFINE_RELOAD_CAUSE(5, "P1V5PCH"),
	DEFINE_RELOAD_CAUSE(6, "P1V05COM"),
	DEFINE_RELOAD_CAUSE(7, "P1V3KRHV"),
	DEFINE_RELOAD_CAUSE(8, "P1V7SCFUSE"),
	DEFINE_RELOAD_CAUSE(9, "P3V3"),
	DEFINE_RELOAD_CAUSE(10, "P5V"),
	DEFINE_RELOAD_CAUSE(11, "P1V2ALW"),
	DEFINE_RELOAD_CAUSE(12, "P3V3ALW"),
	DEFINE_RELOAD_CAUSE(13, "P12V"),
	DEFINE_RELOAD_CAUSE(14, "P1V2LAN1"),
	DEFINE_RELOAD_CAUSE(15, "P1V2LAN2")
};

/*
 * Encoded reload causes for DARWIN SMB UCD90320.
 */
const struct encoded_reload_cause darwin_aucd90320_encoded_gpis[] = {
	DEFINE_RELOAD_CAUSE(1, "Over-Temperature"),
	DEFINE_RELOAD_CAUSE(2, "SCD CRC"),
	DEFINE_RELOAD_CAUSE(3, "PSU AC Loss"),
	DEFINE_RELOAD_CAUSE(4, "PSU DC Fault"),
	DEFINE_RELOAD_CAUSE(5, "SCD Watchdog Timeout"),
	DEFINE_RELOAD_CAUSE(6, "Requested by Software"),
	DEFINE_RELOAD_CAUSE(7, "Requested by Software"),
	DEFINE_RELOAD_CAUSE(8, "CPU Fault")
};

const struct encoded_reload_cause darwin_aucd90320_encoded_rails[] = {
	DEFINE_RELOAD_CAUSE(1, "P12V_TH3_A"),
	DEFINE_RELOAD_CAUSE(2, "P12V_TH3_B"),
	DEFINE_RELOAD_CAUSE(3, "P12V_STDBY"),
	DEFINE_RELOAD_CAUSE(4, "P5V0"),
	DEFINE_RELOAD_CAUSE(5, "P3V3"),
	DEFINE_RELOAD_CAUSE(6, "P3V3_OSFP_A"),
	DEFINE_RELOAD_CAUSE(7, "P3V3_OSFP_B"),
	DEFINE_RELOAD_CAUSE(8, "P3V3_STDBY"),
	DEFINE_RELOAD_CAUSE(9, "P2V5_LT"),
	DEFINE_RELOAD_CAUSE(10, "P2V5_RT"),
	DEFINE_RELOAD_CAUSE(11, "P1V8"),
	DEFINE_RELOAD_CAUSE(12, "P1V5_A"),
	DEFINE_RELOAD_CAUSE(13, "P1V5_B"),
	DEFINE_RELOAD_CAUSE(14, "P1V2"),
	DEFINE_RELOAD_CAUSE(15, "P0V8_AVDD"),
	DEFINE_RELOAD_CAUSE(16, "P0V9_VDD")
};

#endif /* __AUCD9000_DARWIN_RELOAD_CAUSE_H__ */