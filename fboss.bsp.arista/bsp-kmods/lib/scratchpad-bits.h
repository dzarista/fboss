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

#ifndef __SCRATCHPAD_BITS_H__
#define __SCRATCHPAD_BITS_H__

#define MERU_VCPLD_RELOAD_CAUSE_COOKIE_BITPOS   (0U)
#define MERU_VCPLD_RELOAD_CAUSE_COOKIE_LEN      (1U)
#define MERU_VCPLD_RELOAD_CAUSE_COOKIE_MASK \
		(((1U << MERU_VCPLD_RELOAD_CAUSE_COOKIE_LEN) - 1) << \
		MERU_VCPLD_RELOAD_CAUSE_COOKIE_BITPOS)

#define FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_BITPOS   (0U)
#define FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_LEN      (1U)
#define FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_MASK \
		(((1U << FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_LEN) - 1) << \
		FAIRYWREN_SCD_RELOAD_CAUSE_COOKIE_BITPOS)

#endif /* __SCRATCHPAD_BITS_H__ */
