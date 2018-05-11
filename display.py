'''
display -- define the finite state machine for the display

This definition is in two parts. First the actions are defined and then the states and
and transistions are defined using a state table.
'''
### IMPORTS
import Adafruit_CharLCD as LCD       # to interface LCD
lcd = LCD.Adafruit_CharLCDPlate()
import time


# create some custom characters for the LCD Plate
#  characters are 5x8 matrices, formed as 8 rows of 5 right justified bits
lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])      # music note
lcd.create_char(2, [0, 1, 3, 22, 28, 8, 0, 0])       # check mark
# 0000 0000
# 0000 0001
# 0000 0011
# 0001 0110
# 0001 1100
# 0000 1000
# 0000 0000
# 0000 0000
lcd.create_char(3, [0, 14, 21, 23, 17, 14, 0, 0])    # clock
# 0000 0000
# 0000 1110
# 0001 0101
# 0001 0111
# 0001 0001
# 0000 1110
# 0000 0000
# 0000 0000
lcd.create_char(4, [31, 17, 10, 4, 10, 17, 31, 0])   # hour glass
lcd.create_char(5, [8, 12, 10, 9, 10, 12, 8, 0])     # triangle point right
lcd.create_char(6, [2, 6, 10, 18, 10, 6, 2, 0])      # triangle point left
lcd.create_char(7, [31, 17, 21, 21, 21, 21, 17, 31]) # boxed bar
# 0001 1111
# 0001 0001
# 0001 0101
# 0001 0101
# 0001 0101
# 0001 0101
# 0001 0001
# 0001 1111


####GLOBALS THAT CAN BE EXTERNAL
# this includes parameters for display purposes
air_temperature = 0
air_pressure = 0
current_peak_to_peak = 0
current_period = 0
current_power = 0
current_state = ''
long_average_water_level = 0
measurement_count = 0
node_ip_address = "?.?.?.?"
peak_min_period = 0
peak_max = 0
peak_max_period = 0
pump_temperature = 0
raw_water_level = 0
raw_water_pressure = 0
total_power = 0
water_pressure_offset = 0
water_pressure_rate = 0


####INTERNAL GLOBALS
# this includes state variables saved between transitions
# these should not be referenced externally
armed = True	# lock for keypresses
digit = 0
event_time = 0
last_pressed_time = 0



####CONFIGURABLE CONSTANTS
VISIBLE_TIME = 60         # seconds for the display to remain visable
DISPLAY_TIME = 2          # seconds for each item in rotation
RESTFUL_REPORT_TIME = 60  # seconds between each RESTful report
TIME_TIME = 1             # seconds between time display updates
TEMPERATURE_TIME = 1      # seconds between temperature readings
PRESSURE_TIME = 1         # seconds between water pressure readings
AIR_PRESSURE_TIME = 1     # seconds between air pressure readings
WATER_PRESSURE_OFFSET_DIGITS = 4 # number of digits in water pressure offset
WATER_PRESSURE_RATE_DIGITS  = 3 # number of digits in water pressure rate

####EVENTS

buttons = (LCD.SELECT,
           LCD.LEFT,
           LCD.UP,
           LCD.DOWN,
           LCD.RIGHT)
TIMEOUT = 8       # event values include LCD buttons

####FUNCTIONS
def do_action(action):
  action()

def start():
  global current_state
  global TIMEOUT
  global last_pressed_time

  last_pressed_time = time.time()
  lcd.clear()
  current_state = 'S_display_datetime'
  processEvent (TIMEOUT)

def turnOnLCD():
  lcd.enable_display(True)
  lcd.set_color(0,0,1) # turn on backlight

def turnOffLCD():
  lcd.enable_display(False)
  lcd.set_color(0,0,0) # turn off backlight

def active():
  global current_state
  return current_state != 'S_exit'

def CtoF(degreeCelcius):
  return degreeCelcius * 9/5 + 32


####ACTIONS
# Hints:
#  Use lcd.clear when changing between displays
#  use lcd.set_cursor(0,0) for updating same information on display to reduce flashing
#  put lcd.clear into appropriate transition action

def display_datetime():
  global event_time
  global measurement_count

  lcd.set_cursor(0,0)
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
  lcd.clear()
  lcd.message ("IP address:\n" + node_ip_address)

def display_pump_temperature():
  global pump_temperature
  global event_time

  lcd.set_cursor(0,0)
  lcd.message ("Pump Temperature:\n{0:0.1f}\xDFF  {1:0.1f}\xDFC   ".format (CtoF(pump_temperature), pump_temperature))
  event_time = time.time() + TEMPERATURE_TIME

def timed_display_pump_temperature():
  global pump_temperature
  global event_time

  lcd.clear()
  lcd.message ("Pump Temperature:\n{0:0.1f}\xDFF  {1:0.1f}\xDFC   ".format (CtoF(pump_temperature), pump_temperature))
  event_time = time.time() + DISPLAY_TIME

def display_air_temperature():
  global air_temperature
  global event_time

  lcd.set_cursor(0,0)
  lcd.message ("Air Temperature:\n{0:0.1f}\xDFF  {1:0.1f}\xDFC   ".format (CtoF(pump_temperature), air_temperature))
  event_time = time.time() + TEMPERATURE_TIME

def timed_display_air_temperature():
  global air_temperature
  global event_time

  lcd.clear()
  lcd.message ("Air Temperature:\n{0:0.1f}\xDFF  {1:0.1f}\xDFC   ".format (CtoF(pump_temperature), air_temperature))
  event_time = time.time() + DISPLAY_TIME

def display_air_pressure():
  global event_time
  global air_pressure

  lcd.set_cursor(0,0)
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

  lcd.set_cursor(0,0)
  lcd.message ("Raw Water Pressure:\n{0:0.0f} Pa    ".format(raw_water_pressure))
  event_time = time.time() + PRESSURE_TIME

def display_raw_water_level():
  global event_time
  global raw_water_level

  lcd.set_cursor(0,0)
  lcd.message ("Raw Water Level:\n{0:0.1f}in {1:0.1f}cm    ".format(raw_water_level, raw_water_level * 2.54))
  event_time = time.time() + PRESSURE_TIME

def display_water_offset():
  global water_pressure_offset

  lcd.clear()
  lcd.message ("Water Offset:\n" + str(water_pressure_offset))

def display_water_pressure_rate():
  global water_pressure_rate

  lcd.clear()
  lcd.message ("Water Rate:\n" + str(water_pressure_rate))

def display_water_level():
  global event_time

  lcd.set_cursor(0,0)
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

  lcd.set_cursor(0,0)
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

  lcd.set_cursor(0,0)
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
  lcd.clear()
  lcd.message ("Exit?")

def edit_water_offset2():
  global digit
  global water_pressure_offset

  digit = 0
  lcd.clear()
  lcd.message ("Edit Water Offset:\n" + str(water_pressure_offset))
  lcd.set_cursor (WATER_PRESSURE_OFFSET_DIGITS - 1 - digit, 1)
  lcd.show_cursor(True)

def display_editData():
  global editData
  global editDigit
  global editMaxDigits
  global editName

  lcd.set_cursor(0,0)
  lcd.message (editName + ":\n" + str(editData))
  lcd.set_cursor (editMaxDigits - 1 - editDigit, 1) # move cursor to digit being changed

def edit_water_offset():
  global editData
  global editDigit
  global editMaxDigits
  global editName

  editData = water_pressure_offset
  editDigit = 0
  editMaxDigits = WATER_PRESSURE_OFFSET_DIGITS
  editName = "Edit Water Offset"
  lcd.clear()
  display_editData()
  lcd.show_cursor(True)

def inc_editData():
  global editData
  global editDigit

  editData = editData + 10**editDigit
  display_editData()

def dec_editData():
  global editData
  global editDigit

  editData = editData - 10**editDigit
  display_editData()

def inc_editDigit():
  global editDigit
  global editMaxDigits

  if editDigit == editMaxDigits - 1:
    editDigit = 0
  else:
    editDigit = editDigit + 1
  display_editData()

def dec_editDigit():
  global editDigit
  global editMaxDigits

  if editDigit == 0:
    editDigit = editMaxDigits - 1
  else:
    editDigit = editDigit - 1
  display_editData()

def inc_water_offset():
  global digit
  global water_pressure_offset

  # editData = editData + 10**digit
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


def save_water_offset2():
  global water_pressure_offset

  lcd.message ("Water Offset:\n" + str(water_pressure_offset))
  lcd.show_cursor(False)

def save_water_offset():
  global editData
  global water_pressure_offset

  water_pressure_offset = editData
  display_editData()
  lcd.show_cursor(False)

def edit_water_pressure_rate2():
  global digit
  global water_pressure_rate

  digit = 0
  lcd.message ("Edit Water Rate:\n" + str(water_pressure_rate))
  lcd.set_cursor (WATER_PRESSURE_RATE_DIGITS - 1 - digit, 1)
  lcd.show_cursor(True)

def edit_water_pressure_rate():
  global editData
  global editDigit
  global editMaxDigits
  global editName

  editData = water_pressure_rate
  editDigit = 0
  editMaxDigits = WATER_PRESSURE_RATE_DIGITS
  editName = "Edit Water Rate"
  lcd.clear()
  display_editData()
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

  global editData
  global editDigit
  global editMaxDigits
  global editName

def save_water_pressure_rate():
  global editData
  global water_pressure_rate

  water_pressure_rate = editData
  display_editData()
  lcd.show_cursor(False)

def save_water_pressure_rate2():
  global water_pressure_rate

  lcd.clear()
  lcd.message ("Water Rate:\n" + str(water_pressure_rate))
  lcd.show_cursor(False)

def exit_now():
  lcd.clear()
  lcd.message("Bye")

#maybe should just go into screen saver immediately to allow recovery


'''
The state table is implemented as a dictionary with the state name as the key.
All state names begin with 'S_'. The value of the state dictionary is an object
defining an optional entry action and a list of transasitions. Each transition
is an object consisting of a triggering event, an optional action, and a next
state.

Triggering events can be any of the keys or a time out.
Actions are functions and are optional.



states = {
  'state_name': {
    'entryAction': function (),
    'transitions': [
      { 'event': event; 'action': function (),
                        'nextState': 'state_name' }
      ...
    ]
  },
  ...

'''


states = {

  'S_display_datetime': {
    'entryAction': display_datetime,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_exit'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_IP_address'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_datetime'},
      { 'event': TIMEOUT,    'nextState': 'S_display_datetime'}
    ]
  },

  'S_display_IP_address':  {
    'entryAction' : display_IP_address,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_datetime'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_air_temperature'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_air_temperature'}
    ]
  },

  'S_display_air_temperature': {
    'entryAction': display_air_temperature,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_IP_address'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_pump_temperature'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_air_temperature'},
      { 'event': TIMEOUT,    'nextState': 'S_display_air_temperature'}
    ]
  },

  'S_display_pump_temperature': {
    'entryAction': display_pump_temperature,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_air_temperature'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_air_pressure'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_pump_temperature'},
      { 'event': TIMEOUT,    'nextState': 'S_display_pump_temperature'}
    ]
  },

  'S_display_air_pressure': {
    'entryAction': display_air_pressure,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_pump_temperature'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_pressure'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_air_pressure'},
      { 'event': TIMEOUT,    'nextState': 'S_display_air_pressure'}
    ]
  },

  'S_display_raw_water_pressure': {
    'entryAction': display_raw_water_pressure,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_air_pressure'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_level'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': TIMEOUT,    'nextState': 'S_display_raw_water_pressure'}
    ]
  },

  'S_display_raw_water_level': {
    'entryAction': display_raw_water_level,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_pressure'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_water_level'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': TIMEOUT,    'nextState': 'S_display_raw_water_level'}
    ]
  },

  'S_display_water_level': {
    'entryAction': display_water_level,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_level'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_waves'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': TIMEOUT,    'nextState': 'S_display_water_level'}
    ]
  },

  'S_display_waves': {
    'entryAction': display_waves,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_water_level'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_wave_average'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': TIMEOUT,
                             'nextState': 'S_display_waves'}
    ]
  },

  'S_display_wave_average': {
    'entryAction': display_wave_average,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_waves'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_water_offset'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': TIMEOUT,    'nextState': 'S_display_wave_average'}
    ]
  },

  'S_display_water_offset': {
    'entryAction': display_water_offset,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_wave_average'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_water_pressure_rate'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': LCD.SELECT, 'action': edit_water_offset,
                             'nextState': 'S_edit_water_offset'}
    ]
  },

  'S_display_water_pressure_rate': {
    'entryAction': display_water_pressure_rate,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_water_offset'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_exit'},
      { 'event': LCD.RIGHT,  'nextState': 'S_timed_display_water_level'},
      { 'event': LCD.SELECT, 'action': edit_water_pressure_rate,
                             'nextState': 'S_edit_water_pressure_rate'}
    ]
  },

  'S_edit_water_offset': {
    'transitions' : [
      { 'event': LCD.DOWN,   'action': dec_editData,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.UP,     'action': inc_editData,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.RIGHT,  'action': dec_editDigit,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.LEFT,   'action': inc_editDigit,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.SELECT, 'action': save_water_offset,
                             'nextState': 'S_display_water_offset'}
    ]
  },

  'S_edit_water_offset2': {
    'transitions' : [
      { 'event': LCD.DOWN,   'action': dec_water_offset,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.UP,     'action': inc_water_offset,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.RIGHT,  'action': dec_water_offset_digit,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.LEFT,   'action': inc_water_offset_digit,
                             'nextState': 'S_edit_water_offset'},
      { 'event': LCD.SELECT, 'action': save_water_offset,
                             'nextState': 'S_display_water_offset'}
    ]
  },

  'S_edit_water_pressure_rate2': {
    'transitions' : [
      { 'event': LCD.DOWN,   'action': dec_water_pressure_rate,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.UP,     'action': inc_water_pressure_rate,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.RIGHT,  'action': dec_water_pressure_rate_digit,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.LEFT,   'action': inc_water_pressure_rate_digit,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.SELECT, 'action': save_water_pressure_rate,
                             'nextState': 'S_display_water_pressure_rate'}
    ]
  },

  'S_edit_water_pressure_rate': {
    'transitions' : [
      { 'event': LCD.DOWN,   'action': dec_editData,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.UP,     'action': inc_editData,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.RIGHT,  'action': dec_editDigit,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.LEFT,   'action': inc_editDigit,
                             'nextState': 'S_edit_water_pressure_rate'},
      { 'event': LCD.SELECT, 'action': save_water_pressure_rate,
                             'nextState': 'S_display_water_pressure_rate'}
    ]
  },

  'S_timed_display_datetime': {
    'entryAction': timed_display_datetime,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_exit'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_IP_address'},
      { 'event': LCD.LEFT,   'action':    lcd.clear,
                             'nextState': 'S_display_datetime'},
      { 'event': TIMEOUT,    'nextState': 'S_timed_display_air_temperature'}
    ]
  },

  'S_timed_display_air_temperature': {
    'entryAction': timed_display_air_temperature,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_IP_address'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_air_pressure'},
      { 'event': LCD.LEFT,   'action':    lcd.clear,
                             'nextState': 'S_display_air_temperature'},
      { 'event': TIMEOUT,    'nextState': 'S_timed_display_pump_temperature'}
    ]
  },

  'S_timed_display_pump_temperature': {
    'entryAction': timed_display_pump_temperature,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_air_temperature'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_air_pressure'},
      { 'event': LCD.LEFT,   'action':    lcd.clear,
                             'nextState': 'S_display_pump_temperature'},
      { 'event': TIMEOUT,    'nextState': 'S_timed_display_air_pressure'}
    ]
  },

  'S_timed_display_air_pressure': {
    'entryAction': timed_display_air_pressure,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_pump_temperature'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_pressure'},
      { 'event': LCD.LEFT,   'action':    lcd.clear,
                             'nextState': 'S_display_air_pressure'},
      { 'event': TIMEOUT,    'nextState': 'S_timed_display_water_level'}
    ]
  },

  'S_timed_display_water_level': {
    'entryAction': timed_display_water_level,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_raw_water_level'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_water_offset'},
      { 'event': LCD.LEFT,   'action':    lcd.clear,
                             'nextState': 'S_display_water_level'},
      { 'event': TIMEOUT,    'nextState': 'S_timed_display_datetime'}
    ]
  },

  'S_display_exit': {
    'entryAction': display_exit,
    'transitions' : [
      { 'event': LCD.UP,     'action':    lcd.clear,
                             'nextState': 'S_display_water_pressure_rate'},
      { 'event': LCD.DOWN,   'action':    lcd.clear,
                             'nextState': 'S_display_datetime'},
      { 'event': LCD.SELECT, 'nextState': 'S_exit'}
    ]
  },

  'S_exit': { # just a dummy
    'entryAction': exit_now,
    'transitions' : [
    ]
  }
}

def activateScreenSaver():
  global armed
  global last_pressed_time

  if time.time() - last_pressed_time > VISIBLE_TIME:
    turnOffLCD()
    armed = False # force waking keypress to not be processed

def processEvent (event):
  global current_state
  global event_time

  state = states [current_state]
  for transition in state['transitions']:
    if transition ['event'] == event:
      print "state: " + current_state + " event: " + str(event)
      event_time = 0 # default to no event timer and cancel existing timer
      if 'action' in transition:
        print "state: " + current_state + " event: " + str(event) + " action: " + str(transition['action'])
        do_action (transition ['action'])
      current_state = transition ['nextState']
      if 'entryAction' in states[current_state]:
        print "state: " + current_state + " entry action: " + str(states[current_state]['entryAction'])
        do_action (states [current_state]['entryAction'])

def processKeyEvent ():
  global last_pressed_time
  global VISIBLE_TIME
  global armed

  keypressed = False
  for button in buttons:
    if lcd.is_pressed(button): # this would be faster if all buttons were read once
      keypressed = True
      current_time = time.time()
      if current_time - last_pressed_time > VISIBLE_TIME: # LCD off
        turnOnLCD()
      last_pressed_time = current_time
      if armed:
        armed = False # to lock duplicate processing of this key press
        #print "keypress state: " + current_state + " key: " + str(button)
        processEvent (button)
  if not keypressed:
    armed = True

def processTimeoutEvent ():
  global event_time

  if event_time != 0 and time.time() - event_time > 0:
    processEvent (TIMEOUT)
