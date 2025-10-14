// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef FW_SMBUS_H
#define FW_SMBUS_H

#ifdef __cplusplus
extern "C" {
#endif

#include <errno.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

/***********************************************************
 * I2C-DEV Helper functions
 **********************************************************/

#define _I2C_MIN(a, b) (((a) <= (b)) ? (a) : (b))

static inline __s32 i2c_smbus_access(int file, char read_write, __u8 command,
                                     int size, union i2c_smbus_data *data) {
  struct i2c_smbus_ioctl_data args;

  args.read_write = read_write;
  args.command = command;
  args.size = size;
  args.data = data;
  return ioctl(file, I2C_SMBUS, &args);
}

static inline __s32 i2c_smbus_write_byte(int file, __u8 value) {
  return i2c_smbus_access(file, I2C_SMBUS_WRITE, value, I2C_SMBUS_BYTE, NULL);
}

static inline __s32 i2c_smbus_read_byte_data(int file, __u8 command) {
  union i2c_smbus_data data;
  if (i2c_smbus_access(file, I2C_SMBUS_READ, command, I2C_SMBUS_BYTE_DATA,
                       &data))
    return -1;
  else
    return 0x0FF & data.byte;
}

static inline __s32 i2c_smbus_write_byte_data(int file, __u8 command,
                                              __u8 value) {
  union i2c_smbus_data data;
  data.byte = value;
  return i2c_smbus_access(file, I2C_SMBUS_WRITE, command, I2C_SMBUS_BYTE_DATA,
                          &data);
}

static inline __s32 i2c_smbus_read_word_data(int file, __u8 command) {
  union i2c_smbus_data data;
  if (i2c_smbus_access(file, I2C_SMBUS_READ, command, I2C_SMBUS_WORD_DATA,
                       &data))
    return -1;
  else
    return 0x0FFFF & data.word;
}

static inline __s32 i2c_smbus_write_word_data(int file, __u8 command,
                                              __u16 value) {
  union i2c_smbus_data data;
  data.word = value;
  return i2c_smbus_access(file, I2C_SMBUS_WRITE, command, I2C_SMBUS_WORD_DATA,
                          &data);
}

/* Returns the number of read bytes */
static inline __s32 i2c_smbus_read_block_data(int file, __u8 command,
                                              __u8 *values) {
  union i2c_smbus_data data;
  if (i2c_smbus_access(file, I2C_SMBUS_READ, command, I2C_SMBUS_BLOCK_DATA,
                       &data))
    return -1;
  else {
    memcpy(values, &data.block[1],
           _I2C_MIN(data.block[0], I2C_SMBUS_BLOCK_MAX));
    return data.block[0];
  }
}

static inline __s32 i2c_smbus_write_block_data(int file, __u8 command,
                                               __u8 length,
                                               const __u8 *values) {
  union i2c_smbus_data data;
  if (length > 32)
    length = 32;
  memcpy(&data.block[1], values, length);
  data.block[0] = length;
  return i2c_smbus_access(file, I2C_SMBUS_WRITE, command, I2C_SMBUS_BLOCK_DATA,
                          &data);
}

#undef _I2C_MIN

#ifdef __cplusplus
} // extern "C"
#endif
#endif // FW_SMBUS_H
