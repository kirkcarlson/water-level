#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
water-input a module for inputing measurements pertaining to water levels

Copyright (c) 2016-2018 Kirk Carlson, All Rights Reserved

Portions Copyright (c) 2014 Adafruit Industries
Author: Tony DiCola

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""


#### IMPORTS ####

import sys
import random

#import logging
import time
import parse

from config import BASE_AIR_PRESSURE
from config import SWING_AIR_PRESSURE
from config import BASE_WATER_COLUMN_PRESSURE
from config import SWING_WATER_COLUMN_PRESSURE
from config import DESIRED_PERIOD
from config import CSV_FORMAT
from config import PA_TO_INCH
from config import WATER_COLUMN_OFFSET



#### GLOBALS



#### CLASSES ####

class InputChannel (object):
  """provide measurement inputs.

  attributes:
    type
    inFile

    airPressure
    waterColumnPressure
    tick

  """

  def __init__ (self, inputFileName):
    """Open an input channel that can produce measurements.

    Returns:
      InputChannel object
    """

    # probably should check if file is already open so that it may
    # be properly closed
    self.success = True
    self.airPressure = 0
    self.waterColumnPressure = 0
    self.level = 0
    self.tick = 0

    if inputFileName == '-R': #random
      self.type = "random"
      self.inFile = None
    elif inputFileName == '-S': #sensors
      self.type = "sensor"
      self.inFile = None
    elif inputFileName != '': #filename
      self.type = "file"
      try:
        self.inFile = open(inputFileName, 'r')
      except IOError:
        #logging.error("Cannot open input file " + inputFileName)
        self.success = False
      #except Exception as e:
      #  # handle any other exception
      #  print "Error '{0}' occured. Arguments {1}.".format(e.message, e.args)
      #  self.success = False
    else: #null
      # or does this default to random?
      # this should be handled by parent, because no parsing done here
      print "Bad argument to create InputChannel"
      self.success = False


  def close (self):
    """close an open input channel."""
    if self.inFile is not None:
      self.inFile.close()


  def getWaterLevel (self, tick):
    """input and process a water level measurement

    more detail on the method
  
    Args:
      tick: (float) epoch (s)
  
    Returns:
      tick: (int) epoch s of the measurement time
      rawWaterLevel: (float) inches of water level
  
    Raises:
      None
    """
    self.tick, self.airPressure, self.waterColumnPressure = \
        self.readMeasurement( tick)
    #convert pressures to instantaneous water level
    self.level = convertPascalsToInches (
      self.waterColumnPressure - self.airPressure)
    return self.tick, self.level


  def readMeasurement ( self, tick):
    """Get a measurement tuple (time, air pressure and water column presssure)
    from a previosly initialized input channel

    Args:
      tick -- (float) current time epoch in s
  
    Returns:
      tick: (float) epoch time of measurement
      airPressure: (int) air pressure in Pascals
      waterColumnPressure: (int) water column pressure in Pascals
  
    Raises:
      None
    """
    if self.type == 'random':
      airPressure = BASE_AIR_PRESSURE + random.randrange(
        SWING_AIR_PRESSURE)
      waterColumnPressure = BASE_WATER_COLUMN_PRESSURE + \
          random.randrange( SWING_WATER_COLUMN_PRESSURE)
      tick = tick + DESIRED_PERIOD
      return tick, airPressure, waterColumnPressure
  
    elif self.type == 'sensors':
      #HOLD airPressure = airPressureSensor.read_pressure()
      #HOLD waterColumnPressue = waterColumnSensor.read_pressure()
      tick = time.time()
      return tick, airPressure, waterColumnPressure
  
    elif self.type == 'file':
      # read lines until one can be parsed or end of file is reached
      while True:
        line = self.inFile.readline()
        if not line: # end of file
          self.inFile.close()
          print "\nExiting at end of input file."
          sys.exit(1)
        else:
          r = parse.parse (CSV_FORMAT, line)
          if r is not None:
            tick = time.mktime((r['year'], r['month'], r['day'],\
              r['hour'], r['minute'], 0, 0,0,-1)) + r['second']
            return tick, r['airPressure'], r['waterColumnPressure']
    else:
      print "InputChannel is not initialized"
      sys.exit(2)



#### FUNCTIONS ####


def _test():
  """tests the functions of this module

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  # do some initialization stuff

  # loop through a number of tests
  currentTick = 0
  #inChan = InputChannel("-R")
  inChan = InputChannel("../19.csv")
  for _ in range (10):
    # just some test stuff here for now
    # get an input and convert to level
    measurement = inChan.readMeasurement(currentTick)
    # convert the raw pressure inputs into an instantaneous water level
    level = convertPascalsToInches (measurement[2] -measurement[1])
    currentTick = measurement[0]
    print "Current Tick and water level are: ", currentTick, level
    level = inChan.getWaterLevel(currentTick)
    print "Current water level is: ", level

  currentTick = 0
  inChan = InputChannel("../19.csv")
  for _ in range (10):
    # just some test stuff here for now
    # get an input and convert to level
    measurement = inChan.readMeasurement(currentTick)
    # convert the raw pressure inputs into an instanteous water level
    level = convertPascalsToInches (measurement[2] -measurement[1])
    currentTick = measurement[0]
    print "Current Tick and water level are: ", currentTick, level
    level = inChan.getWaterLevel(currentTick)
    print "Current water level is: ", level
  exit()





#### INTERFACING THE PRESSURE SENSORS ####

#@import Adafruit_BMP.BMP085 as BMP085

# Default constructor will pick a default I2C bus.
#
# For the Raspberry Pi this means you should hook up to the only exposed I2C
# bus from the main GPIO header and the library will figure out the bus number
# based on the Pi's revision.
#

# You can also optionally change the BMP085 mode to one of
# BMP085_ULTRALOWPOWER, # BMP085_STANDARD, BMP085_HIGHRES, or
# BMP085_ULTRAHIGHRES.  See the BMP085 datasheet for more details on the
# meanings of each mode (accuracy and power consumption are primarily the
# differences).  The default mode is STANDARD.
#MODE=BMP085.BMP085_ULTRALOWPOWER
#@MODE=BMP085.BMP085_STANDARD
#MODE=BMP085.BMP085_HIGHRES
#MODE=BMP085.BMP085_ULTRAHIGHRES

# Optionally you can override the bus number:
#sensor = BMP085.BMP085(busnum=2)

# configure the air pressure sensor on the first I2C bus
#@airPressureSensor = BMP085.BMP085(mode=MODE)
airPressureSensor=0 #@

# configure the water column pressure sensor on the second I2C bus
#@i2cConfig() # turn on second i2c bus (bus 0)
#@waterColumnSensor = BMP085.BMP085(busnum=0, mode=MODE)
waterColumnSensor=0 #@


def convertPascalsToInches (pressurePa):
  """convert a pressure in Pascals to inches of water above a particular datum

  Args:
    input: pressure in Pascals (int)
  
  Returns:
    equivalent inches of water above a datum
  
  Raises:
    None
  """
  return pressurePa/PA_TO_INCH - WATER_COLUMN_OFFSET



if __name__ == "__main__":
  # execute only if run as a script
  _test()
