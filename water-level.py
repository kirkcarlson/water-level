#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8

import math
import time
import random
import datetime
import Adafruit_CharLCD as LCD
import socket


# Initialize the LCD using the pins 
lcd = LCD.Adafruit_CharLCDPlate()
random.seed()

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

WAKE_TIME = 5         # seconds for the display to remain visable
TEMPERATURE_TIME = 10 # seconds between temperature readings
PRESSURE_TIME = 10    # seconds between air pressure readings

# display states
S_display_datetime =           0
S_display_IP_address =         1
S_display_temperature =        2
S_display_air_pressure =       3
S_display_raw_water_pressure = 4
S_display_raw_water_depth =    5
S_display_water_depth =        6
S_display_water_offset =       7
S_display_water_rate =         8
S_edit_water_offset =          9
S_edit_water_rate =            10
S_display_exit =               11
S_exit =                       12

# actions
dec_water_offset =           0
dec_water_offset_index =     1
dec_water_rate =             2
display_air_pressure =       3
display_datetime =           4
display_IP_address =         5
display_raw_water_depth =    6
display_raw_water_pressure = 7
display_temperature =        8
display_water_depth =        9
display_water_offset =       10
display_water_rate =         11
edit_water_offset =          12
edit_water_rate =            13
inc_water_offset =           14
inc_water_offset_index =     15
inc_water_rate =             16
save_water_offset_index =    17
save_water_rate_index =      18
exit =                       19
display_exit =               20

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
           ]],
  [S_display_IP_address, [
             [LCD.UP,   display_datetime, S_display_datetime],
             [LCD.DOWN, display_temperature, S_display_temperature],
           ]],
  [S_display_temperature, [
             [LCD.UP,   display_IP_address, S_display_IP_address],
             [LCD.DOWN, display_air_pressure, S_display_air_pressure],
           ]],
  [S_display_air_pressure, [
             [LCD.UP,   display_temperature, S_display_temperature],
             [LCD.DOWN, display_raw_water_pressure, S_display_raw_water_pressure],
           ]],
  [S_display_raw_water_pressure, [
             [LCD.UP,   display_air_pressure, S_display_air_pressure],
             [LCD.DOWN, display_raw_water_depth, S_display_raw_water_depth],
           ]],
  [S_display_raw_water_depth, [
             [LCD.UP,   display_raw_water_pressure, S_display_raw_water_pressure],
             [LCD.DOWN, display_water_depth, S_display_water_depth],
           ]],
  [S_display_water_depth, [
             [LCD.UP,   display_raw_water_depth, S_display_raw_water_depth],
             [LCD.DOWN, display_water_offset, S_display_water_offset],
           ]],
  [S_display_water_offset, [
             [LCD.UP,   display_water_depth, S_display_water_depth],
             [LCD.DOWN, display_water_rate, S_display_water_rate],
             [LCD.SELECT, edit_water_offset, S_edit_water_offset],
           ]],
  [S_display_water_rate, [
             [LCD.UP,   display_water_offset, S_display_water_offset],
             [LCD.DOWN, display_exit, S_display_exit],
             [LCD.SELECT, edit_water_rate, S_edit_water_rate],
           ]],
  [S_display_exit, [
             [LCD.UP,   display_water_rate, S_display_water_rate],
             [LCD.DOWN, display_datetime, S_display_datetime],
             [LCD.SELECT, exit, S_exit],
           ]],

  [S_edit_water_offset, [
             [LCD.DOWN,   inc_water_offset, S_edit_water_offset],
             [LCD.UP,     dec_water_offset, S_edit_water_offset],
             [LCD.RIGHT,  dec_water_offset_index, S_edit_water_offset],
             [LCD.LEFT,   inc_water_offset_index, S_edit_water_offset],
             [LCD.SELECT, save_water_offset_index, S_display_water_offset],
           ]],
  [S_edit_water_rate, [ [LCD.DOWN,   inc_water_rate, S_edit_water_rate],
             [LCD.UP,     dec_water_rate, S_edit_water_rate],
             [LCD.RIGHT,  dec_water_rate, S_edit_water_rate],
             [LCD.LEFT,   inc_water_rate, S_edit_water_rate],
             [LCD.SELECT, save_water_rate_index, S_display_water_rate],
           ]],
  [S_exit,[[]]] # just a dummy
]

### CONSTANTS
MIN_WATER_OFFSET_INDEX = 1
MAX_WATER_OFFSET_INDEX = 1000


### GLOBAL VARIABLES

temperature = 0
air_pressure = 0
raw_water_pressure = 0
raw_water_depth = 0
water_offset = 0
water_offset_index = 0
water_rate = 0
water_depth = 0

### FUNCTIONS
def do_action(action):
  global temperature
  global air_pressure
  global raw_water_pressure
  global raw_water_depth
  global water_offset
  global water_offset_index
  global water_rate
  global water_depth

  if action == display_datetime:
    lcd.clear()
    lcd.message (time.strftime("%H:%M:%S") + '\n' + time.strftime("%m/%d/%Y"))

  elif action == display_IP_address:
    s.connect(("8.8.8.8",80))
    lcd.clear()
    lcd.message ("IP address:\n" + s.getsockname()[0])

  elif action == display_temperature:
    lcd.clear()
    lcd.message ("Air Temperature:\n" + str( temperature) + '*F  ' + str( 5/9 * (temperature - 32)) + '*C')

  elif action == display_air_pressure:
    lcd.clear()
    lcd.message ("Air Pressure:\n" + str( air_pressure))

  elif action == display_raw_water_pressure:
    lcd.clear()
    lcd.message ("Raw Water Pressure:\n" + str( raw_water_pressure))

  elif action == display_raw_water_depth:
    lcd.clear()
    lcd.message ("Raw Water Depth:\n" + str( raw_water_depth))

  elif action == display_water_offset:
    lcd.clear()
    lcd.message ("Water Offset:\n" + str( water_offset))

  elif action == display_water_rate:
    lcd.clear()
    lcd.message ("Water Rate:\n" + str( water_rate))

  elif action == display_water_depth:
    lcd.clear()
    lcd.message ("Water Depth:\n" + str( water_depth))

  elif action == display_exit:
    lcd.clear()
    lcd.message ("Exit?")

  elif action == edit_water_offset:
    water_offset_index = MIN_WATER_OFFSET_INDEX
    lcd.cursorposition (2,3)
    lcd.cursor(True)

  elif action == inc_water_offset:
    water_offset = water_offset + water_offset_index

  elif action == dec_water_offset:
    water_offset = water_offset - water_offset_index

  elif action == inc_water_offset_index:
    if water_offset_index == MAX_WATER_OFFSET_INDEX:
      water_offset_index = MIN_WATER_OFFSET_INDEX
    else:
      water_offset_index = water_offset_index * 10

  elif action == dec_water_offset_index:
    if water_offset_index == MIN_WATER_OFFSET_INDEX:
      water_offset_index = MAX_WATER_OFFSET_INDEX
    else:
      water_offset_index = water_offset_index / 10

  elif action == exit:
    lcd.clear()
    lcd.message("Bye Bye")


### MAIN
#open file to find saved variables
# this should be more robust..
#   no config file goes to the defaults
#   errors go to the defaults
#   should have some sort of delimeter to make it human readable... xml or json
#config = open('levelvariables.conf', 'r')
#water_pressure_offset = int(config.readline()) #range? , default
#water_pressure_rate = int(config.readline()) #range? , default
#display_color = int(config.readline()) # single number 1..8 , default
#config.close()

#open socket to find IP address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# set up loop variables
armed = True
pressed = False
lcd.clear()
lcd.set_color(0,0,1)
last_pressed_time = time.time()
last_temperature_time = last_pressed_time
last_pressure_time = last_pressed_time
lcd.message(str(last_pressed_time))


print 'Press Ctrl-C to quit.'
current_state = S_display_datetime
do_action (display_datetime) 
while current_state != S_exit:
  current_time = time.time()
  if current_time - last_pressed_time > WAKE_TIME:
    lcd.enable_display( False)
    armed = False
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
  raw_water_depth = 240 + random.randrange (10)
  water_depth = 240 + random.randrange (10)

  # wait for event (keypress
  for button in buttons:
    if lcd.is_pressed(button): # this would be faster if all buttons were read once
      last_pressed_time = current_time
      state = states [current_state]
      for transition in state [State_Transitions]:
        if transition [Transition_Trigger] == button:   
          action = transition [Transition_Action]
          do_action (action)
          current_state = transition [Transition_Next_State]
#need to detect button up before next state.

s.close()
# need to be able to change the water offset value. It can have a default.
# the value should be saved between runs
# backlight should time out. any button will wake without change
#   need to compute time from last button press to the present



