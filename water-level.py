#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8

import math
import time
import random
import datetime
import Adafruit_CharLCD as LCD
import socket


# CONSTANTS

WAKE_TIME = 60         # seconds for the display to remain visable
TEMPERATURE_TIME = 1  # seconds between temperature readings
PRESSURE_TIME = 1     # seconds between air pressure readings
TIME_TIME = 1         # seconds between time display updates
DISPLAY_TIME = 2      # seconds for each item in rotation
WATER_PRESSURE_OFFSET_DIGITS = 4    # digits in water pressure offset
WATER_PRESSURE_RATE_DIGITS = 3      # digits in water pressure rate
TIMER_EVENT = 8       # event values include LCD buttons


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


# List of buttons
buttons = ( LCD.SELECT,
            LCD.LEFT,
            LCD.UP,
            LCD.DOWN,
            LCD.RIGHT)

# display states
S_display_datetime =           0
S_display_IP_address =         1
S_display_temperature =        2
S_display_air_pressure =       3
S_display_raw_water_pressure = 4
S_display_raw_water_level =    5
S_display_water_level =        6
S_display_water_offset =       7
S_display_water_rate =         8
S_edit_water_offset =          9
S_edit_water_rate =            10
S_timed_display_datetime =     11
S_timed_display_temperature =  12
S_timed_display_air_pressure = 13
S_timed_display_water_level =  14
S_display_exit =               15
S_exit =                       16

# actions
dec_water_offset =           0
dec_water_offset_digit =     1
dec_water_rate =             2
dec_water_rate_digit =       3
display_air_pressure =       4
display_datetime =           5
display_IP_address =         6
display_raw_water_level =    7
display_raw_water_pressure = 8
display_temperature =        9
display_water_level =        10
display_water_offset =       11
display_water_rate =         12
edit_water_offset =          13
edit_water_rate =            14
inc_water_offset =           15
inc_water_offset_digit =     16
inc_water_rate =             17
inc_water_rate_digit =       18
save_water_offset =          19
save_water_rate =            20
timed_display_air_pressure = 21
timed_display_datetime =     22
timed_display_temperature =  23
timed_display_water_level =  24
exit =                       25
display_exit =               26

# State Table -- define the states and transtions for the display
# 
#states [n] yeilds the entire state information
#states [n][1] yeilds the entire state transition information
#states [n][1][0] yeilds the first state transition information
#states [n][1][0][0] yeilds the first state transition trigger
#states [n][1][0][1] yeilds the first state transition actions
#states [n][1][0][2] yeilds the first state transition next state

# index into state
State_Transitions = 1

# index into state transition list
Transition_Trigger =    0
Transition_Action =     1
Transition_Next_State = 2

# state table for the various states, with transition [trigger, action, next state]
states = [
  [S_display_datetime, [
             [LCD.UP,   display_exit, S_display_exit],
             [LCD.DOWN, display_IP_address, S_display_IP_address],
             [LCD.RIGHT, timed_display_datetime, S_timed_display_datetime],
             [TIMER_EVENT, display_datetime, S_display_datetime],
           ]],
  [S_display_IP_address, [
             [LCD.UP,   display_datetime, S_display_datetime],
             [LCD.DOWN, display_temperature, S_display_temperature],
           ]],
  [S_display_temperature, [
             [LCD.UP,   display_IP_address, S_display_IP_address],
             [LCD.DOWN, display_air_pressure, S_display_air_pressure],
             [LCD.RIGHT, timed_display_temperature, S_timed_display_temperature],
             [TIMER_EVENT, display_temperature, S_display_temperature],
           ]],
  [S_display_air_pressure, [
             [LCD.UP,   display_temperature, S_display_temperature],
             [LCD.DOWN, display_raw_water_pressure, S_display_raw_water_pressure],
             [LCD.RIGHT, timed_display_air_pressure, S_timed_display_air_pressure],
             [TIMER_EVENT, display_air_pressure, S_display_air_pressure],
           ]],
  [S_display_raw_water_pressure, [
             [LCD.UP,   display_air_pressure, S_display_air_pressure],
             [LCD.DOWN, display_raw_water_level, S_display_raw_water_level],
             [TIMER_EVENT, display_raw_water_pressure, S_display_raw_water_pressure],
           ]],
  [S_display_raw_water_level, [
             [LCD.UP,   display_raw_water_pressure, S_display_raw_water_pressure],
             [LCD.DOWN, display_water_level, S_display_water_level],
             [TIMER_EVENT, display_raw_water_level, S_display_raw_water_level],
           ]],
  [S_display_water_level, [
             [LCD.UP,   display_raw_water_level, S_display_raw_water_level],
             [LCD.DOWN, display_water_offset, S_display_water_offset],
             [LCD.RIGHT, timed_display_water_level, S_timed_display_water_level],
             [TIMER_EVENT, display_water_level, S_display_water_level],
           ]],
  [S_display_water_offset, [
             [LCD.UP,   display_water_level, S_display_water_level],
             [LCD.DOWN, display_water_rate, S_display_water_rate],
             [LCD.SELECT, edit_water_offset, S_edit_water_offset],
           ]],
  [S_display_water_rate, [
             [LCD.UP,   display_water_offset, S_display_water_offset],
             [LCD.DOWN, display_exit, S_display_exit],
             [LCD.SELECT, edit_water_rate, S_edit_water_rate],
           ]],
  [S_edit_water_offset, [
             [LCD.DOWN,   dec_water_offset, S_edit_water_offset],
             [LCD.UP,     inc_water_offset, S_edit_water_offset],
             [LCD.RIGHT,  dec_water_offset_digit, S_edit_water_offset],
             [LCD.LEFT,   inc_water_offset_digit, S_edit_water_offset],
             [LCD.SELECT, save_water_offset, S_display_water_offset],
           ]],
  [S_edit_water_rate, [
             [LCD.DOWN,   dec_water_rate, S_edit_water_rate],
             [LCD.UP,     inc_water_rate, S_edit_water_rate],
             [LCD.RIGHT,  dec_water_rate_digit, S_edit_water_rate],
             [LCD.LEFT,   inc_water_rate_digit, S_edit_water_rate],
             [LCD.SELECT, save_water_rate, S_display_water_rate],
           ]],
  [S_timed_display_datetime, [
             [LCD.UP,   display_exit, S_display_exit],
             [LCD.DOWN, display_IP_address, S_display_IP_address],
             [LCD.LEFT, display_datetime, S_display_datetime],
             [TIMER_EVENT, timed_display_datetime, S_timed_display_temperature],
           ]],
  [S_timed_display_temperature, [
             [LCD.UP,   display_IP_address, S_display_IP_address],
             [LCD.DOWN, display_air_pressure, S_display_air_pressure],
             [LCD.LEFT, display_temperature, S_display_temperature],
             [TIMER_EVENT, timed_display_temperature, S_timed_display_air_pressure],
           ]],
  [S_timed_display_air_pressure, [
             [LCD.UP,   display_temperature, S_display_temperature],
             [LCD.DOWN, display_raw_water_pressure, S_display_raw_water_pressure],
             [LCD.LEFT, display_air_pressure, S_display_air_pressure],
             [TIMER_EVENT, timed_display_air_pressure, S_timed_display_water_level],
           ]],
  [S_timed_display_water_level, [
             [LCD.UP,   display_raw_water_level, S_display_raw_water_level],
             [LCD.DOWN, display_water_offset, S_display_water_offset],
             [LCD.LEFT, display_water_level, S_display_water_level],
             [TIMER_EVENT, timed_display_water_level, S_timed_display_datetime],
           ]],
  [S_display_exit, [
             [LCD.UP,   display_water_rate, S_display_water_rate],
             [LCD.DOWN, display_datetime, S_display_datetime],
             [LCD.SELECT, exit, S_exit],
           ]],
  [S_exit,[[]]] # just a dummy
]


### GLOBAL VARIABLES

air_pressure = 0
digit = 0
event_time = 0
raw_water_pressure = 0
raw_water_level = 0
temperature = 0
water_pressure_offset = 0
water_pressure_rate = 0
water_offset_index = 0
water_rate = 0
water_level = 0

### FUNCTIONS
def do_action(action):
  global air_pressure
  global digit
  global event_time
  global raw_water_level
  global raw_water_pressure
  global temperature
  global water_pressure_offset
  global water_pressure_rate
  global water_rate
  global water_level

  if action == display_datetime:
    lcd.set_cursor (0, 0)
    lcd.message (time.strftime("%m/%d/%Y" + "\n" + time.strftime("%H:%M:%S")))
    event_time = time.time() + TIME_TIME 

  if action == timed_display_datetime:
    lcd.clear()
    lcd.message (time.strftime("%m/%d/%Y" + "\n" + time.strftime("%H:%M:%S")))
    event_time = time.time() + DISPLAY_TIME 

  elif action == display_IP_address:
    s.connect(("8.8.8.8",80))
    lcd.message ("IP address:\n" + s.getsockname()[0])

  elif action == display_temperature:
    lcd.set_cursor (0, 0)
    lcd.message ("Air Temperature:\n" + str( temperature) + 'F  ' + str((temperature - 32) * 5/9) + 'C')
    event_time = time.time() + TEMPERATURE_TIME 

  elif action == timed_display_temperature:
    lcd.clear()
    lcd.message ("Air Temperature:\n" + str( temperature) + 'F  ' + str((temperature - 32) * 5/9) + 'C')
    event_time = time.time() + DISPLAY_TIME 

  elif action == display_air_pressure:
    lcd.set_cursor (0, 0)
    lcd.message ("Air Pressure:\n" + str( air_pressure))
    event_time = time.time() + PRESSURE_TIME 

  elif action == timed_display_air_pressure:
    lcd.clear()
    lcd.message ("Air Pressure:\n" + str( air_pressure))
    event_time = time.time() + DISPLAY_TIME 

  elif action == display_raw_water_pressure:
    lcd.set_cursor (0, 0)
    lcd.message ("Raw Water Pressure:\n" + str( raw_water_pressure))
    event_time = time.time() + PRESSURE_TIME 

  elif action == display_raw_water_level:
    lcd.set_cursor (0, 0)
    lcd.message ("Raw Water Level:\n" + str( raw_water_level))
    event_time = time.time() + PRESSURE_TIME 

  elif action == display_water_offset:
    lcd.message ("Water Offset:\n" + str( water_pressure_offset))

  elif action == display_water_rate:
    lcd.message ("Water Rate:\n" + str( water_pressure_rate))

  elif action == display_water_level:
    lcd.set_cursor (0, 0)
    lcd.message ("Water Level:\n" + str( water_level))
    event_time = time.time() + PRESSURE_TIME 

  elif action == timed_display_water_level:
    lcd.clear()
    lcd.message ("Water Level:\n" + str( water_level))
    event_time = time.time() + DISPLAY_TIME 

  elif action == display_exit:
    lcd.message ("Exit?")

  elif action == edit_water_offset:
    digit = 0
    lcd.message ("Edit Water Offset:\n" + str( water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)
    lcd.show_cursor(True)

  elif action == inc_water_offset:
    water_pressure_offset = water_pressure_offset + 10**digit
    lcd.message ("Edit Water Offset:\n" + str( water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

  elif action == dec_water_offset:
    water_pressure_offset = water_pressure_offset -  10**digit
    lcd.message ("Edit Water Offset:\n" + str( water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

  elif action == inc_water_offset_digit:
    if digit == WATER_PRESSURE_OFFSET_DIGITS - 1:
      digit = 0
    else:
      digit = digit + 1
    lcd.message ("Edit Water Offset:\n" + str( water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

  elif action == dec_water_offset_digit:
    if digit == 0:
      digit = WATER_PRESSURE_OFFSET_DIGITS - 1
    else:
      digit = digit - 1
    lcd.message ("Edit Water Offset:\n" + str( water_pressure_offset))
    lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)

  elif action == save_water_offset:
    lcd.message ("Water Offset:\n" + str( water_pressure_offset))
    lcd.show_cursor(False)

  elif action == edit_water_rate:
    digit = 0
    lcd.message ("Edit Water Rate:\n" + str( water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)
    lcd.show_cursor(True)

  elif action == inc_water_rate:
    water_pressure_rate = water_pressure_rate + 10**digit
    lcd.message ("Edit Water Rate:\n" + str( water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

  elif action == dec_water_rate:
    water_pressure_rate = water_pressure_rate -  10**digit
    lcd.message ("Edit Water Rate:\n" + str( water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

  elif action == inc_water_rate_digit:
    if digit == WATER_PRESSURE_RATE_DIGITS - 1:
      digit = 0
    else:
      digit = digit + 1
    lcd.message ("Edit Water Rate:\n" + str( water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

  elif action == dec_water_rate_digit:
    if digit == 0:
      digit = WATER_PRESSURE_RATE_DIGITS - 1
    else:
      digit = digit - 1
    lcd.message ("Edit Water Rate:\n" + str( water_pressure_rate))
    lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)

  elif action == save_water_rate:
    lcd.message ("Water Rate:\n" + str( water_pressure_rate))
    lcd.show_cursor(False)

  elif action == exit:
    lcd.message("Bye")

  else:
    pass


### MAIN
#open file to find saved variables
# this should be more robust..
#   no config file goes to the defaults
#   errors go to the defaults
#   should have some sort of delimeter to make it human readable... xml or json
#config = open('levelvariables.conf', 'r')
#water_pressure_offset = int(config.readline()) #range? , default
water_pressure_offset = 3000
#water_pressure_rate = int(config.readline()) #range? , default
water_pressure_rate = 300
#display_color = int(config.readline()) # single number 1..8 , default
#config.close()

#open socket to find IP address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# set up loop variables
random.seed()
armed = True    # single action per keypress arming
lcd.clear()
lcd.set_color(0,0,1)
current_time = time.time()
last_pressed_time = current_time
last_temperature_time = current_time
last_pressure_time = current_time
event_time = 0
current_state = S_display_datetime
action = display_datetime


print 'Press Ctrl-C to quit.'
armed = True
lcd.clear()
do_action (display_datetime) 
while current_state != S_exit:
  current_time = time.time()
  if current_time - last_pressed_time > WAKE_TIME:
    lcd.enable_display( False)
    armed = False # force waking keypress to not be processed
    lcd.set_color(0,0,0) # turn off backlight

  # calculate new values
  if current_time - last_temperature_time > TEMPERATURE_TIME:
    temperature = 72 + random.randrange (10)
    last_temperature_time = last_temperature_time + TEMPERATURE_TIME
  if current_time - last_pressure_time > PRESSURE_TIME:
    air_pressure = 10300 + random.randrange (10)
    last_pressure_time = last_pressure_time + PRESSURE_TIME

  # want to do several times a second
  raw_water_pressure = 10600 + random.randrange (10)
  raw_water_level = 240 + random.randrange (10)
  water_level = 240 + random.randrange (10)

  # handle timer event
  if event_time != 0 and current_time - event_time > 0:
    state = states [current_state]
    for transition in state [State_Transitions]:
      if transition [Transition_Trigger] == TIMER_EVENT:
        action = transition [Transition_Action]
        event_time = 0 # default to no event timer
        do_action (action)
        current_state = transition [Transition_Next_State]
    
  # wait for event (keypress)
  keypressed = False
  for button in buttons:
    if lcd.is_pressed(button): # this would be faster if all buttons were read once
      if current_time - last_pressed_time > WAKE_TIME:
        lcd.enable_display(True)
        lcd.set_color(0,0,1) # turn on backlight
      last_pressed_time = current_time
      state = states [current_state]
      for transition in state [State_Transitions]:
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

s.close()

# need to be able to change the water offset value. It can have a default.
# the value should be saved between runs
#  nice if this used JSON as there might be quite a few configuration parameters

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
