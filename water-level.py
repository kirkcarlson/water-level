#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8

# Overall code
# Author: Kirk Carlson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# portions Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


###DEBGUGGING CONTROL

# Can enable debug output by uncommenting:
import logging
logging.basicConfig(level=logging.WARN)
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

### IMPORTS
import Adafruit_BMP.BMP085 as BMP085 # to interface pressure/temperature sensors
from i2c_0 import i2cConfig          # to use the second I2C bus .. modified
import math                          # for calulations and constants
import time                          # for timing
#import random                        # for simulator
import urllib                        # for reporting to RESTFUL server
import urllib2                       # for reporting to RESTFUL server
from ConfigParser import SafeConfigParser # for reading configuration file
import socket                        # to detect IP address

import display                       # module to handle the display
# need to rethink this a bit...
# waterFSM is really a display module
#  it has some functions like start, processEvent and buttons
#    it should do whatever is necessary for the keypress processing and get that out of the main loop
#  it has some portals for varibles to be displayed: temperature, pressure, water level, etc.
#    these are defined in the display module and need to be referred to from here
#  it has some portals for configurable constants: TIME_TIME, etc.
#    these are defined in the display module and need to be referred to from here





#-----end of imports----

# configure the I2C buses and set up the sensors
#
# This device uses both I2C buses since it interfaces two sensors using the same address.
#
# You can also optionally change the BMP085 mode to one of BMP085_ULTRALOWPOWER, 
# BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES.  See the BMP085
# datasheet for more details on the meanings of each mode (accuracy and power
# consumption are primarily the differences).  The default mode is STANDARD.
#MODE=BMP085.BMP085_ULTRALOPOWER
MODE=BMP085.BMP085_STANDARD
#MODE=BMP085.BMP085_HIGHRES
#MODE=BMP085.BMP085_ULTRAHIGHRES

i2cConfig() # turn on second i2c bus (bus 0)
sensor = BMP085.BMP085(mode=MODE) # this is for the open air temperature/pressure using the primary bus = 1
sensor2 = BMP085.BMP085(busnum=0, mode=MODE) # this is for the pumped air temperature/pressure


# CONFIGURED CONSTANTS

# set up the default values
# [Timer]
VISIBLE_TIME = 60         # seconds for the display to remain visable
TEMPERATURE_TIME = 1      # seconds between temperature readings
PRESSURE_TIME = 1         # seconds between water pressure readings
AIR_PRESSURE_TIME = 1     # seconds between air pressure readings
TIME_TIME = 1             # seconds between time display updates
DISPLAY_TIME = 2          # seconds for each item in rotation
RESTFUL_REPORT_TIME = 60  # seconds between each RESTful report

# [Threshold]
TEMPERATURE_THRESHOLD = 200     # hundreths of degree C before reporting a difference in temperature sensors
WAVE_PERIOD_THRESHOLD = .5      # threshold in seconds for recording or reporting of waves
WAVE_PERIOD_CUTOFF = 10         # cut off in seconds for recording or reporting of waves
PEAK_THRESHOLD = 1		# threshold in inches for recording or reporting of waves

# [Other]
WATER_PRESSURE_OFFSET_DIGITS = 4    # digits in water pressure offset
WATER_PRESSURE_RATE_DIGITS = 3      # digits in water pressure rate
SHORT_AVERAGE_PERIOD = 6            # number of samples in the short average
LONG_AVERAGE_PERIOD =  20 * 60      # number of samples in the short average
LONG_AVERAGE_PERIOD =  30 * 10      # number of samples in the short average
                                    # want this to be on the order of a minute
                                    # so figuring 20 samples/second and 60 seconds/minute
NODEID = 30
CONFIG_FILE = 'water.cnf'
BASEURL = 'http://localhost/emoncms/input/post.json?node=' + str( NODEID)
APIKEY = 'YOUR API KEY'

# CONSTANTS
PEAK_LIST_TIME =   0
PEAK_LIST_P2P =    1
PEAK_LIST_PERIOD = 2
PEAK_LIST_POWER =  3

# allow override of the defaults by reading a config file
config = SafeConfigParser()
try:
  config.read(CONFIG_FILE)
except:
  logging.warn("Configuration cannot read file: " + CONFIG_FILE)

try:
  sections = config.sections()
  for section in sections:
    options = config.options(section)
    for option in options:
      try:
        option_
        #logging.debug("Configuration section: " + section + ": " + option + ": " + option_value)
        if section == 'Timers':
          if option == 'visible_time':
            VISIBLE_TIME = config.getint(section, option)
          elif option == 'temperature_time':
            TEMPERATURE_TIME = config.getint(section, option)
          elif option == 'pressure_time':
            PRESSURE_TIME = config.getint(section, option)
          elif option == 'air_pressure_time':
            AIR_PRESSURE_TIME = config.getint(section, option)
          elif option == 'time_time':
            TIME_TIME = config.getint(section, option)
          elif option == 'display_time':
            DISPLAY_TIME = config.getint(section, option)
          elif option == 'restful_report_time':
            RESTFUL_REPORT_TIME = config.getint(section, option)
        elif section == 'Thresholds':
          if option == 'temperature_threshold':
            TEMPERATURE_THRESHOLD = config.getint(section, option)
          elif option == 'wave_period_threshold':
            WAVE_PERIOD_THRESHOLD = config.getint(section, option)
          elif option == 'wave_period_cutoff':
            WAVE_PERIOD_CUTOFF = config.getint(section, option)
          elif option == 'peak_threshold':
            PEAK_THRESHOLD = config.getfloat(section, option)
        elif section == 'Other':
          if option == 'water_pressure_offset_digits':
            WATER_PRESSURE_OFFSET_DIGITS = config.getint(section, option)
          elif option == 'water_pressure_rate_digits':
            WATER_PRESSURE_RATE_DIGITS = config.getint(section, option)
          elif option == 'short_average_period':
            SHORT_AVERAGE_PERIOD = config.getint(section, option)
          elif option == 'long_average_period':
            LONG_AVERAGE_PERIOD = config.getint(section, option)
          elif option == 'baseurl':
            BASEURL = config.get(section, option)
          elif option == 'apikey':
            APIKEY = config.get(section, option)
      except:
        logging.warn("Configuration value for option '" + option + "' in section '" + section + "' isn't right")
        """
---
[Timers]
VISIBLE_TIME = 60                   ; seconds for the display to remain visable
TEMPERATURE_TIME = 1                ; seconds between temperature readings
PRESSURE_TIME = 1                   ; seconds between water pressure readings
AIR_PRESSURE_TIME = 1               ; seconds between air pressure readings
TIME_TIME = 1                       ; seconds between time display updates
DISPLAY_TIME = 2                    ; seconds for each item in rotation

[Thresholds]
TEMPERATURE_THRESHOLD = 200         ; hundreths of degree C before reporting a difference in temperature sensors

[Other]
WATER_PRESSURE_OFFSET_DIGITS = 4    ; digits in water pressure offset
WATER_PRESSURE_RATE_DIGITS = 3      ; digits in water pressure rate
#APIKEY = 0a35664e30afeb91e2b1cc2ad7df5b3d
APIKEY = 7693985fa5e696b17f0a47609fd5a3df
BASEURL = http://bonner-carlson.net/emoncms/input/post.json

WARNING:root:Configuration value for option 'temperature_time' in section 'Timers' isn't right
WARNING:root:Configuration value for option 'pressure_time' in section 'Timers' isn't right
WARNING:root:Configuration value for option 'air_pressure_time' in section 'Timers' isn't right
WARNING:root:Configuration value for option 'time_time' in section 'Timers' isn't right
WARNING:root:Configuration value for option 'display_time' in section 'Timers' isn't right

WARNING:root:Configuration value for option 'temperature_threshold' in section 'Thresholds' isn't right

WARNING:root:Configuration value for option 'water_pressure_offset_digits' in section 'Other' isn't right
WARNING:root:Configuration value for option 'water_pressure_rate_digits' in section 'Other' isn't right
WARNING:root:Configuration value for option 'apikey' in section 'Other' isn't right
WARNING:root:Configuration value for option 'baseurl' in section 'Other' isn't right
---
"""
except:
  logging.warn("Configuration cannot find any sections in " + CONFIG_FILE)

# Initialize the temperature/pressure sensors




### GLOBAL VARIABLES

air_pressure = 0
air_temperature = 0
average_air_pressure = 0
average_water_pressure = 0
pump_temperature = 0
raw_water_pressure = 0
raw_water_level = 0
temperature = 0
water_level = 0
peak_max = 0
total_power = 0
pmin_peakeak_min_period = 0
peak_max_period = 0
current_peak_to_peak = 0
current_power = 0
current_period = 0

#open file to find saved variables
# this should be more robust..
#   no config file goes to the defaults
#   errors go to the defaults
#   should have some sort of delimeter to make it human readable... xml or json
#config = open('levelvariables.conf', 'r')
#water_pressure_offset = int(config.readline()) #range? , default
water_pressure_offset = 2910 # Pa
display.water_pressure_offset = water_pressure_offset
#water_pressure_rate = int(config.readline()) #range? , default
water_pressure_rate = 214.6 # Pa/in
display.water_pressure_rate = water_pressure_rate
#display_color = int(config.readline()) # single number 1..8 , default
#config.close()





### FUNCTIONS
def internet_on():
  try:
    response=urllib2.urlopen('http://74.125.228.100',timeout=1)
    return True
  except urllib2.URLError as err: pass
  return False

def my_ip_address():
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    return s.getsockname()[0]
    s.close()
  #except urllib2.URLError as err:
  except:
    s.close()
    return "?.?.?.?"




### MAIN


# set up loop variables
#random.seed()
current_time = time.time()
last_temperature_time = current_time
next_pressure_time = current_time
last_restful_report_time = current_time
zero_crossing_time = current_time
air_pressure = sensor.read_pressure()
average_air_pressure = air_pressure
raw_water_pressure = sensor2.read_pressure()
average_water_pressure = raw_water_pressure
last_positive_trend = True
positive_peak = 0
negative_peak = 0
peak_list = []
first_time = True

# The power energy of a wave (kW/m) = (ro * g * g / 64 / Math.pi) * H * H * Te
# where
#   ro is the density of water (999.97 kg/m/m/m) (999.0 might be more reasonable 15c)
#   g is the gravitational constant (6.67385 * 10**-11 m m m/kg/s/s)
#   H is the wave height in meters
#   Te is the wave period in seconds
#     watts divide by 10**11
#     nanowatts divide by 10**2
#     .0254 m/in
Power_Constant = 999 * 6.67385 * 6.67385 / 16 / math.pi / 100 *.0254 * .0254

#print 'Press Ctrl-C to quit.'
display.start()
while display.active():
  display.activateScreenSaver()
  current_time = time.time()

  # calculate new values
#---- code for temperature/pressure sensors
  #print 'Temp = {0:0.2f} *C'.format(sensor2.read_temperature())
  #print 'Pressure = {0:0.2f} Pa'.format(sensor2.read_pressure())
  #print 'Altitude = {0:0.2f} m'.format(sensor2.read_altitude())
  #print 'Sealevel Pressure = {0:0.2f} Pa'.format(sensor2.read_sealevel_pressure())

#temperature = (sensor.read_temperature())
#pressure = (sensor.read_pressure())
#highPressure = pressure
#lowPressure = pressure
#averagePressureTotal = pressure
#shortAveragePressure = pressure
#
#temperature2 = (sensor2.read_temperature())
#pressure2 = (sensor2.read_pressure())
#highPressure2 = pressure2
#lowPressure2 = pressure2
#averagePressureTotal2 = pressure2
#shortAveragePressure2 = pressure2
#
#count = 1
#shortPeriod = 3
#while (1):
# 
#  pressure = sensor.read_pressure()
#  temperature = sensor.read_temperature()
#  if (pressure > highPressure):
#    highPressure = pressure
#  if (pressure < lowPressure):
#    lowPressure = pressure
#  averagePressureTotal = averagePressureTotal + pressure
#  count = count + 1
#  averagePressure = averagePressureTotal / count 
#  shortAveragePressure = ((shortPeriod - 1) * shortAveragePressure + pressure) / shortPeriod
#  '''
#
#  pressure2 = sensor2.read_pressure()
#  '''
#  #temperature2 = sensor2.read_temperature()
#  if (pressure2 > highPressure2):
#    highPressure2 = pressure2
#  if (pressure2 < lowPressure2):
#    lowPressure2 = pressure2
#  averagePressureTotal2 = averagePressureTotal2 + pressure2
#  averagePressure2 = averagePressureTotal2 / count 
#  shortAveragePressure2 = ((shortPeriod - 1) * shortAveragePressure2 + pressure2) / shortPeriod
# 

  if current_time - last_temperature_time > TEMPERATURE_TIME:
    air_temperature = sensor.read_temperature()
    pump_temperature = sensor2.read_temperature()
    diff = air_temperature - pump_temperature
    if diff < 0:
      diff = -diff
    if diff > TEMPERATURE_THRESHOLD:
      pass
      #do something to report temperature difference
    last_temperature_time = last_temperature_time + TEMPERATURE_TIME
    display.air_temperature = air_temperature
    display.pump_temperature = pump_temperature
  if current_time >= next_pressure_time:
    air_pressure = sensor.read_pressure()
    average_air_pressure = (average_air_pressure * (SHORT_AVERAGE_PERIOD-1) + air_pressure) /\
          SHORT_AVERAGE_PERIOD
    next_pressure_time = current_time + AIR_PRESSURE_TIME
    display.air_pressure = air_pressure
    display.average_air_pressure = average_air_pressure

  # handle reporting to RESTful server
  if current_time - last_restful_report_time > RESTFUL_REPORT_TIME:
    total = 0
    count = 0
    peak_max = 0
    peak_min = 0
    peak_max_period = 0
    peak_min_period = 0
    peak_total = 0
    peak_period_total = 0
    average_period = 0
    average_peak = 0
    total_power = 0
    if len(peak_list) > 0:
      #print 'reporting peak list: ' + str(peak_list)
      for member in peak_list:
	peak = member [PEAK_LIST_P2P]
        if peak > peak_max:
          peak_max = peak
        if peak_min == 0 or peak < peak_min:
          peak_min = peak
        peak_total = peak_total + peak
        period = member [PEAK_LIST_PERIOD]
        if period > peak_max_period:
          peak_max_period = period
        if peak_min_period == 0 or period < peak_min_period:
          peak_min_period = period
        peak_period_total = peak_period_total + period
        total_power = total_power + member [PEAK_LIST_POWER]
        count = count + 1
      if count > 0:
        average_peak = peak_total / count
        average_period = peak_period_total / count
      peak_list = []
    #print ("ave:{0:0.2f}in {1:0.2f}s min:{2:0.2f}in {3:0.2f}s max:{4:0.2f}in {5:0.2f}s power:{6:0.0f}nW".format (average_peak, average_period, peak_min, peak_min_period, peak_max, peak_max_period, total_power))
    display.average_peak = average_peak
    display.average_period = average_period
    display.peak_max = peak_max
    display.peak_max_period = peak_max_period
    display.peak_min = peak_min
    display.peak_min_period = peak_min_period
    display.total_power = total_power
    json = "{temp:" + str(int(10 * pump_temperature)) +\
           ",airPressure:" + str(average_air_pressure) +\
           ",waterPressure:" + str(average_water_pressure) +\
           ",waterLevel:" + str(long_average_water_level) +\
           ",averagePeak:" + str(average_peak) +\
           ",averagePeriod:" + str(average_period) +\
           ",minPeak:" + str(peak_min) +\
           ",minPeriod:" + str(peak_min_period) +\
           ",maxPeak:" + str(peak_max) +\
           ",maxPeriod:" + str(peak_max_period) +\
           ",powerPerMinute:" + str(total_power) +\
           "}"
    # Send data to emoncms
    node_ip_address = my_ip_address ()
    display.node_ip_address = node_ip_address
    if (node_ip_address != "?.?.?.?"):
      try:
        f = urllib2.urlopen(BASEURL + "?node=" + str(NODEID) + "&apikey=" + APIKEY + "&json=" + json)
        f.close()
      except urllib2.URLError, e:
        #print e.code
        print e.reason
        logging.error('Update error: ' + str(e.reason))
    last_restful_report_time = current_time

  # want to do several times a second, so doing it every loop
  display.measurement_count = display.measurement_count + 1
  raw_water_pressure = sensor2.read_pressure()
  display.raw_water_pressure = raw_water_pressure
  average_water_pressure = (average_water_pressure * (SHORT_AVERAGE_PERIOD-1) + raw_water_pressure) /\
          SHORT_AVERAGE_PERIOD
  raw_water_level = (average_water_pressure - average_air_pressure - water_pressure_offset) / water_pressure_rate
  display.raw_water_level = raw_water_level
  water_level = raw_water_level
  if first_time:
    # initialize the average to the raw reading
    short_average_water_level = raw_water_level
    long_average_water_level = raw_water_level
    first_time = False
  else:
    short_average_water_level = (short_average_water_level * (SHORT_AVERAGE_PERIOD-1) + raw_water_level) /\
          SHORT_AVERAGE_PERIOD
    long_average_water_level = (long_average_water_level * (LONG_AVERAGE_PERIOD-1) + raw_water_level) /\
          LONG_AVERAGE_PERIOD
    display.long_average_water_level = long_average_water_level

  peak = short_average_water_level - long_average_water_level
  if peak > 0:
    positive_trend = True
  else:
    positive_trend = False
  #print ("AWP:{0:0.0f}pa  AAP:{1:0.0f}in".format (average_water_pressure, average_air_pressure))
  #print ("RWL:{0:0.2f}in  short:{1:0.2f}in  long:{2:0.2f}in  peak:{3:0.2f}in".format (raw_water_level, short_average_water_level, long_average_water_level, peak))

  if positive_trend != last_positive_trend: # zero crossing
    #print "zero crossing: pos:" + str(positive_peak) + " neg:" + str(negative_peak)
    if positive_trend:
      negative_period = current_time - zero_crossing_time
      current_period = positive_period + negative_period
      current_peak_to_peak = positive_peak - negative_peak
      # record for periodic report
      if current_period > WAVE_PERIOD_THRESHOLD and current_period < WAVE_PERIOD_CUTOFF and \
            current_peak_to_peak > PEAK_THRESHOLD:
        current_power = Power_Constant * current_peak_to_peak * current_peak_to_peak * current_period
        peak_list.append([current_time, current_peak_to_peak, current_period, current_power])
        #logging.debug("wave time:" + str(current_time) + "  peak:" + str(current_peak_to_peak) + " period:" +\
        #print("wave time:" + str(current_time) + "  peak:" + str(current_peak_to_peak) + " period:" +\
        #     str(current_period) + " power:" + str(current_power))
        json = "{"+\
             ",negative_period:" + str(negative_period) +\
             ",positive_period:" + str(positive_period) +\
             ",negative_peak:" + str(negative_peak) +\
             ",positive_peak:" + str(positive_peak) +\
             ",current_power:" + str(current_power) +\
             "}"
        #print(json)
        # Send data to emoncms
        #try:
        #  f = urllib2.urlopen(BASEURL + "?node=" + str(NODEID) + "&apikey=" + APIKEY + "&json=" + json)
        #  f.close()
        #except urllib2.URLError, e:
        #  #print e.code
        #  print e.reason
        #  logging.error('Update error: ' + str(e.reason))
      positive_peak = peak
    else:
      positive_period = current_time - zero_crossing_time
      negative_peak = peak

    #  report current_time, current_period, current_peak_to_peak
    #  period should include postive portion and negative portion...
  
    # prepare for next wave
    zero_crossing_time = current_time
    last_positive_trend = positive_trend
#   positive_peak = 0
#   negative_peak = 0

  if positive_trend:
    if peak > positive_peak:
      positive_peak = peak
  else:
    if peak < negative_peak:
      negative_peak = peak

  # handle events
  display.processTimeoutEvent ()
  display.processKeyEvent ()

''' comments here to end
# need to be able to change the water offset value. It can have a default.
# the value should be saved between runs

# want to have a more user friendly modes:
#  one that buttons directly select important data

# could generalize the edit state:
#  load a variable and limits on entry
#  save the results on exit

# need to work in actual measurements
#  add smoothing function(s)
#  add a wave detector
#    measure peak-to-peak, period and duration (maybe a series: +3,-3,+2.5,-2.5... with times
#    period is done with a zero crossing detection. peak is max between zeros.
#    we'll have to see what is important

# should turn off LED on exit... maybe after a few second delay...
# historically this program had a dump of raw values. should it retain that capability and send such a string to the RESTful process? Let's say no for now

want to implement a zero crossing detector and peak detector

for a simple report, say every 10 seconds or so
  report the peak wave seen in that period
  report the average wave seen in that period
  recording bit:
    append peak to list
  reporting bit


want to distinguish between waves and wakes
a wake has a short total duration, period is fairly constant and peaks decrease exponentially
  can get confused if ther are multiple wakes
    it should be expressed something like: time, max p-p, period, duration

The power energy of a wave (kW/m) = (ro * g * g / 64 / Math.pi) * H * H * Te
where
 ro is the density of water (999.97 kg/m/m/m) (999.0 might be more reasonable 15c)
 g is the gravitational constant (6.67385 * 10**-11 m m m/kg/s/s)
 H is the wave height in meters
 Te is the wave period in seconds

The first part is constant, so only have to compute the second half
  this is approximately .5 kW/m/m/m/s
waves are more continuous
  periods are fairly random
  p-p are fairly random
    expressed as a range of p-p and periods


joules = 1000 kilowatt/s

# need to use degree symbol = 0xDF? done
# the configuration code  missed the goal of being able to write back the parameter that are modified on the fly
# another day
#
# want to refactor this program
#  initialization
#    set up constants
#    set up display FSM
#  configuration .. with ability to do on the fly
#  main loop
#    periodically re-configure
#    periodically update display
#    periodically dump raw data
#    periodically generate graphics
#    take measurements
#    periodically do calculations
#    handle display FSM events new state actions

# can use pipes or other interprocess communication to decouple the processes
# one for the main loop for doing the basic measurements
# one to do the display thing
# one to do calulations and graphics, etc
# one to communicate with stateless head
# one to handle dumps
#  measure | dump | display | communicate | graphics |
'''
