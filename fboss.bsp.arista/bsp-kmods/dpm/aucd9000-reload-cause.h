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

#ifndef __AUCD9000_RELOAD_CAUSE_H__
#define __AUCD9000_RELOAD_CAUSE_H__

#include <linux/types.h>

enum {
   ENCODED_GPIS = 0,
   ENCODED_RAILS = 1
};

struct encoded_reload_cause {
	u8 id;
	const char *description;
};

#define DEFINE_RELOAD_CAUSE(fault_id, fault_desc)  \
{								                           \
	.id = fault_id,						               \
	.description = fault_desc				            \
}

#endif /* __AUCD9000_RELOAD_CAUSE_H__ */