#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8

# Overall code Copyright (c) 2015 Kirk Carlson
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

# Can enable debug output by uncommenting:
import logging
logging.basicConfig(level=logging.WARN)
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

import Adafruit_BMP.BMP085 as BMP085 # to interface pressure/temperature sensors
import Adafruit_CharLCD as LCD       # to interface LCD
from i2c_0 import i2cConfig          # to use the second I2C bus .. modified
import datetime                      # to display time
import math                          # for calulations and constants
import time                          # for timing
#import random                        # for simulator
import socket                        # to detect IP address
import urllib                        # for reporting to RESTFUL server
import urllib2                       # for reporting to RESTFUL server
from ConfigParser import SafeConfigParser # for reading configuration file

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
        option_value = config.get (section, option)
        #print section + ": " + option + ": " + option_value
        if section == 'Timers':
          if option == 'wake_time':
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
except:
  logging.warn("Configuration cannot find any sections in " + CONFIG_FILE)

# Initialize the LCD using the pins 
lcd = LCD.Adafruit_CharLCDPlate()

# create some custom characters
lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])      # music note
lcd.create_char(2, [0, 1, 3, 22, 28, 8, 0, 0])       # check mark
lcd.create_char(3, [0, 14, 21, 23, 17, 14, 0, 0])    # clock
lcd.create_char(4, [31, 17, 10, 4, 10, 17, 31, 0])   # hour glass
lcd.create_char(5, [8, 12, 10, 9, 10, 12, 8, 0])     # triangle point right
lcd.create_char(6, [2, 6, 10, 18, 10, 6, 2, 0])      # triangle point left
lcd.create_char(7, [31, 17, 21, 21, 21, 21, 17, 31]) # boxed bar

# Initialize the temperature/pressure sensors

# List of buttons and events
buttons = (LCD.SELECT,
            LCD.LEFT,
            LCD.UP,
            LCD.DOWN,
            LCD.RIGHT)
TIMER_EVENT = 8       # event values include LCD buttons



### GLOBAL VARIABLES

air_pressure = 0
air_temperature = 0
average_air_pressure = 0
average_water_pressure = 0
pump_temperature = 0
digit = 0
event_time = 0
raw_water_pressure = 0
raw_water_level = 0
temperature = 0
water_level = 0
measurement_count = 0
peak_max = 0
total_power = 0
peak_min_period = 0
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
#water_pressure_rate = int(config.readline()) #range? , default
water_pressure_rate = 214.6 # Pa/in
#display_color = int(config.readline()) # single number 1..8 , default
#config.close()


### UNCHANGING GLOBAL

# State Table -- define the states and transtions for the display
# 
# states [
#          [ #state n
#            [ #transition m
#              event, action, next_state
#            ]
#            ...
#          ]
#          ...
#states [n] yeilds the entire state information for state n
#states [n][m] yeilds the entire state transition m information for state n
#states [n][m][0] yeilds state n transition m event
#states [n][m][1] yeilds state n transition m actions
#states [n][m][2] yeilds state n transition m next_state

# index into state transition list
Transition_Trigger =    0
Transition_Action =     1
Transition_Next_State = 2

# state table for the various states, with transition [trigger, action, next state]
states_index = 0

def next_state():
  global states_index
  states_index = states_index + 1
  return states_index - 1

def append_state(check):
  global states
  states.append ([])
  if len(states) - 1 != check: 
    check/0 # states are not in the same order as their names

def append_transition(event, action, next_state):
  global states
  states[-1].append ([event, action, next_state])

states = [] # build the table after the functions are defined


### FUNCTIONS
def do_action(action):
  action()

def display_datetime():
    global event_time
    global measurement_count
    lcd.set_cursor (0, 0)
    lcd.message (time.strftime("%m/%d/%Y" + "\n" + time.strftime("%H:%M:%S")) + "      " + str(measurement_count))
    #print (time.strftime("%m/%d/%Y" + "\n" + time.strftime("%H:%M:%S")) + "      " + str(measurement_count))
    measurement_count = 0
    event_time = int(time.time() + TIME_TIME)

def timed_display_datetime():
    global event_time
    global measurement_count
    lcd.clear()
    lcd.message (time.strftime("%m/%d/%Y" + "\n" + time.strftime("%H:%M:%S")) + "      " + str(measurement_count))
    measurement_count = 0
    event_time = time.time() + DISPLAY_TIME 

def display_IP_address():
    lcd.message ("IP address:\n" + my_ip_address())

def display_pump_temperature():
    global pump_temperature
    global event_time
    lcd.set_cursor (0, 0)
    lcd.message ("Pump Temperature:\n{0:0.2f}\xDFF  {1:0.2f}\xDFC   ".format ((pump_temperature * 9/5 + 32), pump_temperature))
    event_time = time.time() + TEMPERATURE_TIME 

def timed_display_pump_temperature():
    global pump_temperature
    global event_time
    lcd.clear()
    lcd.message ("Pump Temperature:\n{0:0.2f}\xDFF  {1:0.2f}\xDFC   ".format ((pump_temperature * 9/5 + 32), pump_temperature))
    event_time = time.time() + DISPLAY_TIME 

def display_air_temperature():
    global air_temperature
    global event_time
    lcd.set_cursor (0, 0)
    lcd.message ("Air Temperature:\n{0:0.2f}\xDFF  {1:0.2f}\xDFC   ".format ((air_temperature * 9/5 + 32), air_temperature))
    event_time = time.time() + TEMPERATURE_TIME 

def timed_display_air_temperature():
    global air_temperature
    global event_time
    lcd.clear()
    lcd.message ("Air Temperature:\n{0:0.2f}\xDFF  {1:0.2f}\xDFC   ".format ((air_temperature * 9/5 + 32), air_temperature))
    event_time = time.time() + DISPLAY_TIME 

def display_air_pressure():
    global event_time
    global air_pressure
    lcd.set_cursor (0, 0)
    lcd.message ("Air Pressure:\n{0:0.0f} Pa    ".format(air_pressure))
    event_time = time.time() + PRESSURE_TIME 

def timed_display_air_pressure():
    global event_time
    global air_pressure
    lcd.clear()
    lcd.message ("Air Pressure:\n{0:0.0f} Pa    ".format(air_pressure))
    event_time = time.time() + DISPLAY_TIME 

def display_raw_water_pressure():
    global event_time
    global raw_water_pressure
    lcd.set_cursor (0, 0)
    lcd.message ("Raw Water Pressure:\n{0:0.0f} Pa    ".format(raw_water_pressure))
    event_time = time.time() + PRESSURE_TIME 

def display_raw_water_level():
    global event_time
    global raw_water_level
    lcd.set_cursor (0, 0)
    lcd.message ("Raw Water Level:\n{0:0.1f}in {1:0.1f}cm    ".format(raw_water_level, raw_water_level * 2.54))
    event_time = time.time() + PRESSURE_TIME 

def display_water_offset():
    global water_pressure_offset
    lcd.message ("Water Offset:\n" + str(water_pressure_offset))

def display_water_pressure_rate():
    global water_pressure_rate
    lcd.message ("Water Rate:\n" + str(water_pressure_rate))

def display_water_level():
    global event_time
    lcd.set_cursor (0, 0)
    lcd.message ("Water Level:\n{0:0.1f}in {1:0.1f}cm    ".format\
       (long_average_water_level, long_average_water_level * 2.54))
    event_time = time.time() + PRESSURE_TIME 

def timed_display_water_level():
    global event_time
    lcd.clear()
    lcd.message ("Water Level:\n{0:0.1f}in {1:0.1f}cm    ".format\
       (long_average_water_level, long_average_water_level * 2.54))
    event_time = time.time() + DISPLAY_TIME 

def display_waves():
    global event_time
    global current_peak_to_peak
    global current_power
    global current_period
    lcd.set_cursor (0, 0)
    if current_power <1000:
      power = int (current_power * 1000) # power comes in nW, change to pW
      units= "pW"
    else:
      power = int(current_power)
    if power <1000:
      units= "nW"
    elif power <1000000:
      power = power / 1000
      units= "uW"
    else:
      power = power / 1000000
      units= "mW"
    lcd.message (("Wave {0:0.1f}' {1:0d}" + units + "        \nLast Period {2:0.1f}s     ").format\
       (current_peak_to_peak/12, power, current_period)) # 1ft/12in
    event_time = time.time() + TIME_TIME # little sence in doing more often

def display_wave_average():
    global event_time
    global peak_max
    global total_power
    global peak_min_period
    global peak_max_period
    lcd.set_cursor (0, 0)
    if total_power <1000:
      power = int (total_power * 1000) # power comes in nW, change to pW
      units= "pW"
    else:
      power = int(total_power)
    if power <1000:
      units= "nW"
    elif power <1000000:
      power = power / 1000
      units= "uW"
    else:
      power = power / 1000000
      units= "mW"
    lcd.message (("Wave {0:0.1f}' {1:0d}" + units + "   \n  Ave {2:0.1f}-{3:0.1f}s   ").format\
       (peak_max/12, power, peak_min_period, peak_max_period)) # 1ft/12in
    event_time = time.time() + PRESSURE_TIME 

def display_exit():
    lcd.message ("Exit?")

def edit_water_offset():
    global digit
    global water_pressure_offset
    digit = 0
    lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)
    lcd.show_cursor(True)

def inc_water_offset():
    global digit
    global water_pressure_offset
    water_pressure_offset = water_pressure_offset + 10**digit
    lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

def dec_water_offset():
    global digit
    global water_pressure_offset
    water_pressure_offset = water_pressure_offset -  10**digit
    lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

def inc_water_offset_digit():
    global digit
    global water_pressure_offset
    if digit == WATER_PRESSURE_OFFSET_DIGITS - 1:
      digit = 0
    else:
      digit = digit + 1
    lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

def dec_water_offset_digit():
    global digit
    global water_pressure_offset
    if digit == 0:
      digit = WATER_PRESSURE_OFFSET_DIGITS - 1
    else:
      digit = digit - 1
    lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

def save_water_offset():
    global water_pressure_offset
    lcd.message ("Water Offset:\n" + str(water_pressure_offset))
    lcd.show_cursor(False)

def edit_water_pressure_rate():
    global digit
    global water_pressure_rate
    digit = 0
    lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)
    lcd.show_cursor(True)

def inc_water_pressure_rate():
    global digit
    global water_pressure_rate
    water_pressure_rate = water_pressure_rate + 10**digit
    lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

def dec_water_pressure_rate():
    global digit
    global water_pressure_rate
    water_pressure_rate = water_pressure_rate -  10**digit
    lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

def inc_water_pressure_rate_digit():
    global digit
    global water_pressure_rate
    if digit == WATER_PRESSURE_RATE_DIGITS - 1:
      digit = 0
    else:
      digit = digit + 1
    lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

def dec_water_pressure_rate_digit():
    global digit
    global water_pressure_rate
    if digit == 0:
      digit = WATER_PRESSURE_RATE_DIGITS - 1
    else:
      digit = digit - 1
    lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

def save_water_pressure_rate():
    global water_pressure_rate
    lcd.message ("Water Rate:\n" + str(water_pressure_rate))
    lcd.show_cursor(False)

def exit_now():
    lcd.message("Bye")

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


# the following are indexes into the States list so should be in the same order as the table is built
S_display_datetime = next_state ()
S_display_IP_address = next_state()
S_display_air_temperature = next_state()
S_display_pump_temperature = next_state()
S_display_air_pressure = next_state()
S_display_raw_water_pressure = next_state()
S_display_raw_water_level = next_state()
S_display_water_level = next_state()
S_display_waves = next_state()
S_display_wave_average = next_state()
S_display_water_offset = next_state()
S_display_water_pressure_rate = next_state()
S_edit_water_offset = next_state()
S_edit_water_pressure_rate = next_state()
S_timed_display_datetime = next_state()
S_timed_display_air_temperature = next_state()
S_timed_display_pump_temperature = next_state()
S_timed_display_air_pressure = next_state()
S_timed_display_water_level = next_state()
S_display_exit = next_state()
S_exit = next_state() # just a dummy

# Build the state table entries, now that the actions are defined
append_state (S_display_datetime)
append_transition (LCD.UP,      display_exit,           S_display_exit)
append_transition (LCD.DOWN,    display_IP_address,     S_display_IP_address)
append_transition (LCD.RIGHT,   timed_display_datetime, S_timed_display_datetime)
append_transition (TIMER_EVENT, display_datetime,       S_display_datetime)

append_state (S_display_IP_address)
append_transition (LCD.UP,   display_datetime, S_display_datetime)
append_transition (LCD.DOWN, display_air_temperature, S_display_air_temperature)

append_state (S_display_air_temperature)
append_transition (LCD.UP,   display_IP_address, S_display_IP_address)
append_transition (LCD.DOWN, display_pump_temperature, S_display_pump_temperature)
append_transition (LCD.RIGHT, timed_display_air_temperature, S_timed_display_air_temperature)
append_transition (TIMER_EVENT, display_air_temperature, S_display_air_temperature)

append_state (S_display_pump_temperature)
append_transition (LCD.UP,   display_air_temperature, S_display_air_temperature)
append_transition (LCD.DOWN, display_air_pressure, S_display_air_pressure)
append_transition (LCD.RIGHT, timed_display_pump_temperature, S_timed_display_pump_temperature)
append_transition (TIMER_EVENT, display_pump_temperature, S_display_pump_temperature)

append_state (S_display_air_pressure)
append_transition (LCD.UP,   display_pump_temperature, S_display_pump_temperature)
append_transition (LCD.DOWN, display_raw_water_pressure, S_display_raw_water_pressure)
append_transition (LCD.RIGHT, timed_display_air_pressure, S_timed_display_air_pressure)
append_transition (TIMER_EVENT, display_air_pressure, S_display_air_pressure)

append_state (S_display_raw_water_pressure)
append_transition (LCD.UP,   display_air_pressure, S_display_air_pressure)
append_transition (LCD.DOWN, display_raw_water_level, S_display_raw_water_level)
append_transition (TIMER_EVENT, display_raw_water_pressure, S_display_raw_water_pressure)

append_state (S_display_raw_water_level)
append_transition (LCD.UP,   display_raw_water_pressure, S_display_raw_water_pressure)
append_transition (LCD.DOWN, display_water_level, S_display_water_level)
append_transition (TIMER_EVENT, display_raw_water_level, S_display_raw_water_level)

append_state (S_display_water_level)
append_transition (LCD.UP,   display_raw_water_level, S_display_raw_water_level)
append_transition (LCD.DOWN, display_waves, S_display_waves)
append_transition (LCD.RIGHT, timed_display_water_level, S_timed_display_water_level)
append_transition (TIMER_EVENT, display_water_level, S_display_water_level)

append_state (S_display_waves)
append_transition (LCD.UP,   display_water_level, S_display_water_level)
append_transition (LCD.DOWN, display_wave_average, S_display_wave_average)
append_transition (TIMER_EVENT, display_waves, S_display_waves)

append_state (S_display_wave_average)
append_transition (LCD.UP,   display_waves, S_display_waves)
append_transition (LCD.DOWN, display_water_offset, S_display_water_offset)
append_transition (TIMER_EVENT, display_wave_average, S_display_wave_average)

append_state (S_display_water_offset)
append_transition (LCD.UP,   display_wave_average, S_display_wave_average)
append_transition (LCD.DOWN, display_water_pressure_rate, S_display_water_pressure_rate)
append_transition (LCD.SELECT, edit_water_offset, S_edit_water_offset)

append_state (S_display_water_pressure_rate)
append_transition (LCD.UP,   display_water_offset, S_display_water_offset)
append_transition (LCD.DOWN, display_exit, S_display_exit)
append_transition (LCD.SELECT, edit_water_pressure_rate, S_edit_water_pressure_rate)

append_state (S_edit_water_offset)
append_transition (LCD.DOWN,   dec_water_offset, S_edit_water_offset)
append_transition (LCD.UP,     inc_water_offset, S_edit_water_offset)
append_transition (LCD.RIGHT,  dec_water_offset_digit, S_edit_water_offset)
append_transition (LCD.LEFT,   inc_water_offset_digit, S_edit_water_offset)
append_transition (LCD.SELECT, save_water_offset, S_display_water_offset)

append_state (S_edit_water_pressure_rate)
append_transition (LCD.DOWN,   dec_water_pressure_rate, S_edit_water_pressure_rate)
append_transition (LCD.UP,     inc_water_pressure_rate, S_edit_water_pressure_rate)
append_transition (LCD.RIGHT,  dec_water_pressure_rate_digit, S_edit_water_pressure_rate)
append_transition (LCD.LEFT,   inc_water_pressure_rate_digit, S_edit_water_pressure_rate)
append_transition (LCD.SELECT, save_water_pressure_rate, S_display_water_pressure_rate)

append_state (S_timed_display_datetime)
append_transition (LCD.UP,   display_exit, S_display_exit)
append_transition (LCD.DOWN, display_IP_address, S_display_IP_address)
append_transition (LCD.LEFT, display_datetime, S_display_datetime)
append_transition (TIMER_EVENT, timed_display_datetime, S_timed_display_air_temperature)

append_state (S_timed_display_air_temperature)
append_transition (LCD.UP,   display_IP_address, S_display_IP_address)
append_transition (LCD.DOWN, display_air_pressure, S_display_air_pressure)
append_transition (LCD.LEFT, display_air_temperature, S_display_air_temperature)
append_transition (TIMER_EVENT, timed_display_air_temperature, S_timed_display_pump_temperature)

append_state (S_timed_display_pump_temperature)
append_transition (LCD.UP,   display_IP_address, S_display_air_temperature)
append_transition (LCD.DOWN, display_air_pressure, S_display_air_pressure)
append_transition (LCD.LEFT, display_air_temperature, S_display_pump_temperature)
append_transition (TIMER_EVENT, timed_display_pump_temperature, S_timed_display_air_pressure)

append_state (S_timed_display_air_pressure)
append_transition (LCD.UP,   display_pump_temperature, S_display_pump_temperature)
append_transition (LCD.DOWN, display_raw_water_pressure, S_display_raw_water_pressure)
append_transition (LCD.LEFT, display_air_pressure, S_display_air_pressure)
append_transition (TIMER_EVENT, timed_display_air_pressure, S_timed_display_water_level)

append_state (S_timed_display_water_level)
append_transition (LCD.UP,   display_raw_water_level, S_display_raw_water_level)
append_transition (LCD.DOWN, display_water_offset, S_display_water_offset)
append_transition (LCD.LEFT, display_water_level, S_display_water_level)
append_transition (TIMER_EVENT, timed_display_water_level, S_timed_display_datetime)

append_state (S_display_exit)
append_transition (LCD.UP,   display_water_pressure_rate, S_display_water_pressure_rate)
append_transition (LCD.DOWN, display_datetime, S_display_datetime)
append_transition (LCD.SELECT, exit_now, S_exit)

append_state (S_exit) # just a dummy


### MAIN


# set up loop variables
#random.seed()
armed = True    # single action per keypress arming
lcd.clear()
lcd.set_color(0,0,1)
current_time = time.time()
last_pressed_time = current_time
last_temperature_time = current_time
next_pressure_time = current_time
last_restful_report_time = current_time
zero_crossing_time = current_time
current_state = S_display_datetime
action = display_datetime
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
armed = True
lcd.clear()
display_datetime() 
while current_state != S_exit:
  current_time = time.time()
  if VISIBLE_TIME >0 and current_time - last_pressed_time > VISIBLE_TIME:
    lcd.enable_display(False)
    armed = False # force waking keypress to not be processed
    lcd.set_color(0,0,0) # turn off backlight

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
  if current_time >= next_pressure_time:
    air_pressure = sensor.read_pressure()
    average_air_pressure = (average_air_pressure * (SHORT_AVERAGE_PERIOD-1) + air_pressure) /\
          SHORT_AVERAGE_PERIOD
    next_pressure_time = current_time + AIR_PRESSURE_TIME

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
    #print ("My IP address is " + my_ip_address())
    #print ("The base URL is " + BASEURL)
    #print ("node is " + str(NODEID))
    #print ("json is " + json)
    if (my_ip_address() != "?.?.?.?"):
      try:
        f = urllib2.urlopen(BASEURL + "?node=" + str(NODEID) + "&apikey=" + APIKEY + "&json=" + json)
        f.close()
      except urllib2.URLError, e:
        #print e.code
        print e.reason
        logging.error('Update error: ' + str(e.reason))
    last_restful_report_time = current_time

  # want to do several times a second, so doing it every loop
  measurement_count = measurement_count + 1
  raw_water_pressure = sensor2.read_pressure()
  average_water_pressure = (average_water_pressure * (SHORT_AVERAGE_PERIOD-1) + raw_water_pressure) /\
          SHORT_AVERAGE_PERIOD
  raw_water_level = (average_water_pressure - average_air_pressure - water_pressure_offset) / water_pressure_rate
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


  # handle timer event
  if event_time != 0 and current_time - event_time > 0:
    state = states [current_state]
    for transition in state:
      if transition [Transition_Trigger] == TIMER_EVENT:
        action = transition [Transition_Action]
        event_time = 0 # default to no event timer
        do_action (action)
        current_state = transition [Transition_Next_State]
    
  # wait for event (keypress)
  keypressed = False
  for button in buttons:
    if lcd.is_pressed(button): # this would be faster if all buttons were read once
      if current_time - last_pressed_time > VISIBLE_TIME:
        lcd.enable_display(True)
        lcd.set_color(0,0,1) # turn on backlight
      last_pressed_time = current_time
      state = states [current_state]
      for transition in state:
        if transition [Transition_Trigger] == button:   
          if armed:
            action = transition [Transition_Action]
            lcd.clear()
            event_time = 0 # default to no event timer and cancel existing timer
            do_action (action)
            current_state = transition [Transition_Next_State]
            armed = False
      keypressed = True
  if not keypressed: 
    armed = True


'''
comments follow here to end

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

# should turn off LED on exit... maybe after a few second delay... DONE
   may want a programmable/settable leave it on command
# historically this program had a dump of raw values. should it retain that capability and send such a string to the RESTful process? Let's say no for now

want to implement a zero crossing detector and peak detector... DONE

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
'''

# need to use degree symbol = 0xDF?  DONE
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
# one for the main loop
# one to do the display thing
# one to do calulations and graphics, etc
# one to communicate with stateless head
# one to handle dumps
#  measure | dump | display | communicate | graphics |
