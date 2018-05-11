#!/usr/bin python
#
# W. Greathouse 13-Feb-2013
# S. Ludwig 26-Oct-2014
# K. Carlson 3-Feb-2015
#
# Inspired by bcm2835 source - http://www.airspayce.com/mikem/bcm2835/
# bgreat source - http://www.raspberrypi.org/forums/viewtopic.php?f=44&t=33092#
# 
#   Enable I2C on P1 and P5 (Rev 2 boards only)
#

# #######
# For I2C configuration test
import os
import mmap
import time

## Constants
BLOCK_SIZE = 4096
BCM2708_PERI_BASE = 0x20000000 # Base address of peripheral registers
GPIO_BASE = (BCM2708_PERI_BASE + 0x00200000)  # Address of GPIO registers
GPFSEL0 = 0x0000 # Function select 0, for registers 0-9
GPFSEL2 = 0x0008 # Function select 2, for registers 20-29

    # GPFSEL0 bits --> x[20] SCL1[3] SDA1[3] 
    #                        GPIO3   GPIO2   GPIO1   GPIO0
REG_SIZE = 3
REG_MASK = 0b111
REG_GPIO_MASK00 = REG_MASK << 0 * REG_SIZE
REG_GPIO_MASK01 = REG_MASK << 1 * REG_SIZE
REG_GPIO_MASK02 = REG_MASK << 2 * REG_SIZE
REG_GPIO_MASK03 = REG_MASK << 3 * REG_SIZE
REG0_MASK = REG_GPIO_MASK00 | REG_GPIO_MASK01 | REG_GPIO_MASK02 | REG_GPIO_MASK03

REG_GPIO_OPT00 = 0b000 << 0 * REG_SIZE
REG_GPIO_OPT01 = 0b000 << 1 * REG_SIZE
REG_GPIO_OPT02 = 0b100 << 2 * REG_SIZE
REG_GPIO_OPT03 = 0b100 << 3 * REG_SIZE
REG0_CONF = REG_GPIO_OPT00 | REG_GPIO_OPT01 | REG_GPIO_OPT02 | REG_GPIO_OPT03

REG_GPIO_MASK28 = REG_MASK << 8 * REG_SIZE
REG_GPIO_MASK29 = REG_MASK << 9 * REG_SIZE
REG2_MASK = REG_GPIO_MASK28 | REG_GPIO_MASK29

REG_GPIO_OPT28 = 0b100 << 8 * REG_SIZE
REG_GPIO_OPT29 = 0b100 << 9 * REG_SIZE
REG2_CONF = REG_GPIO_OPT28 | REG_GPIO_OPT29

# BCM2708 pull-up resistor control
GPPUDCLK0 = 0x0098 # GPIO Pin Pull-up Enable Clock 0
GPPUD = 0x0094 # GPIO Pin Pull-up Enable
GPIO_PUD_OFF = 0b00   # Off - disable pull-up
GPIO_PUD_ON = 0b10    # On - enable pull-up

## functions
def _strTo32bit_(str):
    return ((ord(str[3])<<24) + (ord(str[2])<<16) + (ord(str[1])<<8) + ord(str[0]))

def _32bitToStr_(val):
    return chr(val&0xff) + chr((val>>8)&0xff) + chr((val>>16)&0xff) + chr((val>>24)&0xff)

def get_revision():
    with open('/proc/cpuinfo') as lines:
        for line in lines:
            if line.startswith('Revision'):
                return int(line.strip()[-4:],16)
    raise RuntimeError('No revision found.')

def i2cConfig():
    if get_revision() <= 3:
        print("Rev 2 or greater Raspberry Pi required.")
        return

    # Use /dev/mem to gain access to peripheral registers
    mf = os.open("/dev/mem", os.O_RDWR|os.O_SYNC)
    memory = mmap.mmap(mf, BLOCK_SIZE, mmap.MAP_SHARED, 
                mmap.PROT_READ|mmap.PROT_WRITE, offset=GPIO_BASE)
    # can close the file after we have mmap
    os.close(mf)

    # each 32 bit register controls the functions of 10 pins, each 3 bit, starting at the LSB
    # 000 = input
    # 100 = alt function 0

    # Read function select registers
    # GPFSEL0 -- GPIO 0,1 I2C0   GPIO 2,3 I2C1
    memory.seek(GPFSEL0)
    reg0 = _strTo32bit_(memory.read(4))

    # GPFSEL0 bits --> x[20] SCL1[3] SDA1[3] 
    #                        GPIO3   GPIO2   GPIO1   GPIO0
    if reg0 & REG0_MASK != REG0_CONF:
        print("register 0 configuration of I2C1 not correct. Updating.")
        reg0 = (reg0 & ~REG0_MASK) | REG0_CONF
        memory.seek(GPFSEL0)
	memory.write(_32bitToStr_(reg0))


    # GPFSEL2 -- GPIO 28,29 I2C0
    memory.seek(GPFSEL2)
    reg2 = _strTo32bit_(memory.read(4))

    # GPFSEL2 bits --> x[2] SCL0[3] SDA0[3] x[24]
    #                       GPIO29  GPIO28
    if reg2 & REG2_MASK != REG2_CONF:
        print("register 2 configuration of I2C0 not correct. Updating.")
        reg2 = (reg2 & ~REG2_MASK) | REG2_CONF
        memory.seek(GPFSEL2)
	memory.write(_32bitToStr_(reg2))

    # Configure pull up resistors for GPIO28 and GPIO29
    def configure_pull_up(pin):
        memory.seek(GPPUD)
	memory.write(_32bitToStr_(GPIO_PUD_ON))
        time.sleep(10e-6)

        memory.seek(GPPUDCLK0)
	memory.write(_32bitToStr_(1 << pin))
        time.sleep(10e-6)

        memory.seek(GPPUD)
	memory.write(_32bitToStr_(GPIO_PUD_OFF))

        memory.seek(GPPUDCLK0)
	memory.write(_32bitToStr_(0 << pin))

    configure_pull_up(28)
    configure_pull_up(29)

    # No longer need the mmap
    memory.close()


if __name__ == '__main__':
    i2cConfig()
