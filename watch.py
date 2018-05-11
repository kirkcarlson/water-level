#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
watch: Module for watching a variable over a period of time

Copyright (c) 2016-2018 Kirk Carlson, All Rights Reserved

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

import datetime

import report
from config import NEUTRAL
from config import RISING
from config import FALLING
from config import TREND



#### CLASSES ####

# pylint: disable=too-many-instance-attributes
class Watch( object):
  """The watch records minimum, maximum, trend, etc. for a given variable

  A watch is initialized with current values and watch criteria.

  Periodically a value is evaluated by the watch to set the maximum, minimum,
  etc.

  Attributes:
    name: a name representing the consolidated conditions
    level: the current value
    trend: the current value trend (rising, falling, neutral)
    min: the minimum value during the period
    max: the maximum value during the period
    maxRiseRate: the maximum positive change during the period
    maxFallRate: the maximum negative change during the period
    reversals: the number of trend reversals in the period
    startTick: epoch of consolidation (s)
  """
  # Eight is reasonable in this case.

  # pylint: disable=too-many-arguments
  def __init__(self, name, seedLevel, tick, hysteresis, anomalous=10):
    """Returns a Watch object whose name is *name*."""
    self.name = name
    self.value = seedLevel
    self.startTick = tick
    self.pastValue = seedLevel
    self.pastTime = tick
    self.min = seedLevel
    self.max = seedLevel
    self.elements = 0
    self.sum = 0
    self.ave = 0
    self.trend = NEUTRAL
    self.reversals = 0
    self.reversalValue = seedLevel
    self.reversalTime = tick
    self.hysteresis = hysteresis #should this be separate?
    self.anomalous = anomalous #should this be separate?
    # pylint: enable=too-many-arguments


  def reset( self,  tick):
    """Reset the state of a watch."""
    #self.name is unchanged
    #self.value is unchanged
    self.startTick = tick
    #self.pastValue is unchanged
    #self.pastTime is unchanged
    self.min = self.value
    self.max = self.value
    self.elements = 0
    self.sum = 0
    self.ave = 0
    #self.trend is unchanged
    self.reversals = 0
    #self.reversalValue is unchanged
    #self.reversalTime is unchanged
    #self.hysteresis is unchanged


  def analyze( self, tick, value, outChan):
    """Analyze the value for real-time limits.
  
    Args:
      tick: float epoch associated with the level
      value: float value to be analyzed
      outChan: (class) channel used for the report
    
    Returns:
      None, although the register object is updated
    
    Raises:
      None
    """
    self.value = value
    if value < self.min:
      self.min = value 
    if value > self.max:
      self.max = value 
    self.elements = self.elements + 1
    self.sum = self.sum + value
    if self.elements > 0:
      self.ave = float(self.sum) / self.elements
    else:
      self.ave = 0
    self.findTrend ( tick, value, outChan)
    if value > self.anomalous * self.ave:
      #report it
      outChan.prEvent(tick, # this marks time of the sample
                      self.name,
                      "Anomalous {} this: {:.2f} ave {:.2f}".format(
                          self.name,
                          value,
                          self.ave
                      ),
                      report.VERB_DEBUG  )


  def findTrend(self, tick, value, outChan) :
    """find major reversals in the rising/falling trend of the water level

    Args:
      tick: float epoch associated with the level
      value: float value to be analyzed
      outChan: (class) channel used for the report
    
    Returns:
      None
    
    Raises:
      None
    """
    #print "fTR levels", levels
  #  pastReversalTime = 0
  #  pastReversalLevel = pastLevel # level when direction changed
  #  reversals = 0
  #  newTrend = NEUTRAL
  #  currentTrend = NEUTRAL
  #  #print " len levels: ", len( levels)
  #  for i in range (0,len( levels)):
  #    level = levels[i]
  #    currentTime = times[i]
  #    peakTime = currentTime
    testTrend = self.trend
    testDelta = value - self.pastValue
  #    #print "testLevel:", testLevel, pastLevel
    if testDelta > self.hysteresis:
      testTrend = RISING
  #      #print "RISING", currentTime
    elif testDelta < -self.hysteresis:
      testTrend = FALLING
  #      #print "FALLING", currentTime
    if testTrend != self.trend:
      self.reversals = self.reversals + 1
  #      ##the following doesn't always belong
  
        # report the run
      if self.pastTime - self.reversalTime:
        rate = (self.pastValue-self.reversalValue)/\
                   (self.pastTime-self.reversalTime)*60 #rate/min
      else:
        rate = 0
      outChan.prEvent(
          tick, # this marks the end of run
          self.name,
          "{} run: {:.2f}-{:.2f} = {:.2f}, rate {:.2f} in/min".format(
              TREND[self.trend],
              self.pastValue, # i.e., latest peak
              self.reversalValue, # earliest peak
              self.pastValue-self.reversalValue, # run
              rate #rate/min
          ),
          report.VERB_DEBUG  )
  
        # report the reversal
      outChan.prEvent(
          tick, # this marks begin of event
          self.name,
          "Reversal {}: {:.2f}".format(
              TREND[testTrend],
              self.pastValue, # i.e., latest peak
          ),
          report.VERB_DEBUG  )
  
      self.reversalValue = self.pastValue
      self.reversalTime = self.pastTime
      self.trend = testTrend
      #print "Reversal:",level, newTrend
    elif self.trend == RISING and value > self.pastValue:
      self.pastValue = value
      self.pastTime = tick
    elif self.trend == FALLING and value < self.pastValue:
      self.pastValue = value
      self.pastTime = tick


  def report(self, tick, outChan):
    """Generate report of the watch variable."""

    #### CONSTANTS ####

    FORM = "{:<20} {:>7}"

    #### CODE ####

    
    period = tick - self.startTick
    if period < 90: # <90 seconds
      periodStr = "{:.2f} s".format( period)
    elif period < 90*60: # <90 minutes
      periodStr = "{:.1f} min".format(period/60.)
    else: # hours
      periodStr = "{:.1f} hr".format(period/60./60)

    outChan.prReport( "---")
    outChan.prReport( FORM.format("Report for", self.name) )
    outChan.prReport( FORM.format("Report time", "{:%b %d %H:%M:%S}".format(
        datetime.datetime.fromtimestamp (float(tick))) ) )
    outChan.prReport( FORM.format("Report period", periodStr) )
    outChan.prReport( FORM.format("Report samples", self.elements) )
    outChan.prReport( FORM.format("Value", "{:.2f}".format(self.value)) )
    outChan.prReport( FORM.format("Trend", "{}".format(TREND[self.trend])) )
    outChan.prReport( FORM.format("Reversals", "{:d}".format(self.reversals)) )
    outChan.prReport( FORM.format("Minimum", "{:.2f}".format(self.min)) )
    outChan.prReport( FORM.format("Maximum", "{:.2f}".format(self.max)) )
    outChan.prReport( FORM.format("Average", "{:.2f}".format(self.ave)) )

  def cmp(self, other):
    """Compare the current LevelRegister with anohter, for testing purposes."""
    if self.value != other.value:
      error = "value"
      selfValue = self.value
      otherValue = self.value
    elif self.trend != other.trend:
      error = "trend"
      selfValue = self.trend
      otherValue = self.trend
    elif self.min != other.min:
      error = "min"
      selfValue = self.min
      otherValue = self.min
    elif self.max != other.max:
      error = "max"
      selfValue = self.max
      otherValue = self.max
    elif self.ave != other.ave:
      error = "ave"
      selfValue = self.ave
      otherValue = self.ave
    elif self.reversals != other.reversals:
      error = "reversals"
      selfValue = self.reversals
      otherValue = self.reversals
    #elif self.period != other.period:
    #  error = "period"
    #  selfValue = self.period
    #  otherValue = self.period
    else:
      error = ""
    if error == "":
      print "Registers match"
    else:
      print "Bad match for key {}: values: {} and {}".format(
          error, selfValue, otherValue)
  # pylint: enable=too-many-instance-attributes



#### FUNCTIONS ####

def ave(valueList) :
  """Returns the arithmetic mean of a list of values.

  Args:
    valueList: (list of float) values
  
  Returns:
    average of the values in the list
  
  Raises:
    None
  """
  return float( sum (valueList)) / max( 1, len( valueList))


# pylint: disable=too-many-instance-attributes
class RateTrigger(object):
  """Object for detecting a rapid change of a variable.

  Methods:
    rateTrigger:
    disable:

  Attributes:
    name: 
    trigger: 
    count: 
    countdown: 
    savedValue: 
    savedTime: 
    outChan: 
    units: 
    firstTime: 
    enabled: 
  """

  def __init__( self, name, count, trigger, outChan):
    """tests the functions of this module

    Args:
      name:
      count:
      trigger:
      outChan:
  
    Returns:
      None
  
    Raises:
      None
    """
    self.name = name
    self.trigger = trigger
    self.count = count
    self.countdown = count
    self.savedValue = 0
    self.savedTime = 0
    self.outChan = outChan
    self.units = "in"
    self.firstTime = True
    self.enabled = True

  def rateTrigger( self, tick, value):
    """tests the functions of this module

    Args:
      tick: (float) current time as epoch seconds
      value: (float) value being monitored
  
    Returns:
      None
  
    Raises:
      None
    """
    triggered = False
    if self.enabled:
      if self.firstTime:
        self.savedTime = tick
        self.savedValue = value
        self.countdown = self.count
        self.firstTime = False
      self.countdown = self.countdown - 1
      if self.countdown <= 0:
        if value > self.savedValue + self.trigger or \
            value < self.savedValue - self.trigger:

          #print "Value: {} SavedValue: {} Delta {} Trigger {} Time {:.2f}" +
          #    " Tick {:.2f}".format(
          #  value,
          #  self.savedValue,
          #  value-self.savedValue,
          #  self.trigger,
          #  tick-self.savedTime,
          #  tick
          #)

          if value > self.savedValue: 
            trend = RISING
          else:
            trend = FALLING
          deltaTime = (tick - self.savedTime) / 60. #minutes
          deltaValue = value - self.savedValue
          self.outChan.prEvent(
              tick , # this marks begin of event
              self.name,
              "rapid {}: {:.2f} {} {:.2f} min".format(
                  TREND[trend], deltaValue, self.units, deltaTime),
              report.VERB_DEBUG)
          triggered = True
        self.savedTime = tick
        self.savedValue = value
        self.countdown = self.count
    else:
      self.countdown = self.countdown - 1
      if self.countdown <= 0:
        self.savedTime = tick
        self.savedValue = value
        self.countdown = self.count
        self.enabled = True
    return triggered


  def disable( self, count):
    """tests the functions of this module

    Args:
      None
  
    Returns:
      None
  
    Raises:
      None
    """
    self.enabled = False
    self.countdown = count
  # pylint: enable=too-many-instance-attributes



#pylint disable=line-too-long
def _test():
  """tests the functions of this module

  Args:
    None
  
  Returns:
    None
  
  Produces:
    19:00:09  level rate 2 rapid Rising: 0.09 in 0.15 min
    19:00:13  Water Level  Neutral run: 24.00-24.00 = 0.00, rate 0.00 in/min
    19:00:13  Water Level  Reversal Rising: 24.00
    19:00:19  level rate 2 rapid Rising: 0.10 in 0.17 min
    19:00:29  level rate 1 rapid Rising: 0.29 in 0.48 min
    19:00:30  level rate 2 rapid Rising: 0.11 in 0.18 min
    19:00:40  level rate 2 rapid Rising: 0.10 in 0.17 min
    19:00:49  level rate 0 rapid Rising: 0.49 in 0.82 min
    19:01:23  Water Level  Rising run: 24.71-24.00 = 0.71, rate 0.73 in/min
    19:01:23  Water Level  Reversal Falling: 24.71
    19:01:39  level rate 0 rapid Falling: -0.30 in 0.83 min
    19:02:25  Water Level  Falling run: 24.11-24.71 = -0.60, rate -0.60 in/min
    19:02:25  Water Level  Reversal Rising: 24.11
    19:02:29  level rate 0 rapid Rising: 0.10 in 0.83 min
    19:02:55  Water Level  Rising run: 24.41-24.11 = 0.30, rate 0.60 in/min
    19:02:55  Water Level  Reversal Falling: 24.41
    ---
    Report for           Water Level
    Report time          Dec 31 19:02:59
    Report period        3.0 min
    Report samples           180
    Value                  24.11
    Trend                Falling
    Reversals                  4
    Minimum                24.00
    Maximum                24.71
    Average                24.36  

  Raises:
    None
  """
  #pylint enable=line-too-long


  ### VARIABLES AND TEST DATA ###
  outChan = report.ReportChannel("", report.VERB_DEBUG)
  HYSTERESIS = .25 # amount water level has to change before calling it a trend
  levelWatch = Watch("Water Level", 24.000, 0, HYSTERESIS)
  rates = []

  CHANGE_TUPLES = [
      # this list of tuples set the time and level thresholds for alarms
      # these must be from long periods to short for prioritization
      # this express a rate in samples, value or value:samples or value/samples
      # (if the samples are once a minute, the rate is value per samples
      # minute, if the samples are 30 per second, the rate is value per samples
      # 1/30 second the sampling rate is set outside of this object
      (50, .60/50), #samples=seconds, inches
      (30, .60/30), #samples=seconds, inches
      (10, .60/10), #samples=seconds, inches
  ]
  for i, tup in enumerate(CHANGE_TUPLES):
    rates.append( RateTrigger ( "level rate " + str(i),
                                tup[0],
                                tup[1],
                                outChan)) # trigger, count, outChan

  levels = [
      24.123, 24.133, 24.143, 24.153, 24.163,
      24.173, 24.183, 24.193, 24.203, 24.213, #10
      24.223, 24.233, 24.243, 24.253, 24.263,
      24.273, 24.283, 24.293, 24.303, 24.313, #20
      24.323, 24.333, 24.343, 24.353, 24.363,
      24.373, 24.383, 24.393, 24.403, 24.413, #30
      24.423, 24.433, 24.443, 24.453, 24.463,
      24.473, 24.483, 24.493, 24.503, 24.513, #40
      24.523, 24.533, 24.543, 24.553, 24.563,
      24.573, 24.583, 24.593, 24.603, 24.613, #50
      24.623, 24.633, 24.643, 24.653, 24.663,
      24.673, 24.683, 24.693, 24.703, 24.713, #60
      24.703, 24.693, 24.683, 24.643, 24.663,
      24.653, 24.643, 24.633, 24.623, 24.613, #70
      24.603, 24.593, 24.583, 24.543, 24.563,
      24.553, 24.543, 24.533, 24.523, 24.513, #80
      24.503, 24.493, 24.483, 24.443, 24.463,
      24.453, 24.443, 24.433, 24.423, 24.413, #90
      24.403, 24.393, 24.383, 24.343, 24.363,
      24.353, 24.343, 24.333, 24.323, 24.313, #100
      24.303, 24.293, 24.283, 24.273, 24.263,
      24.253, 24.243, 24.233, 24.223, 24.213, #110
      24.203, 24.193, 24.183, 24.173, 24.163,
      24.153, 24.143, 24.133, 24.123, 24.113, #120
      24.123, 24.133, 24.143, 24.153, 24.163,
      24.173, 24.183, 24.193, 24.203, 24.213, #130
      24.223, 24.233, 24.243, 24.253, 24.263,
      24.273, 24.283, 24.293, 24.303, 24.313, #140
      24.323, 24.333, 24.343, 24.353, 24.363,
      24.373, 24.383, 24.393, 24.403, 24.413, #150
      24.403, 24.393, 24.383, 24.343, 24.363,
      24.353, 24.343, 24.333, 24.323, 24.313, #160
      24.303, 24.293, 24.283, 24.273, 24.263,
      24.253, 24.243, 24.233, 24.223, 24.213, #170
      24.203, 24.193, 24.183, 24.173, 24.163,
      24.153, 24.143, 24.133, 24.123, 24.113, #180
  ]

  duration = len(levels)
  times = list (range (0, duration) ) # assuming one a second
  ### need to do this better
  ###   times should be more integrated with the values. (tuples?)

  for i, time in enumerate(times): # the main sample loop
    level = levels[i]
    levelWatch.analyze(time, level, outChan) 
    for j in range ( 0, len(CHANGE_TUPLES) ):
      if rates[j].rateTrigger( time, level):
        if j+2 < len( CHANGE_TUPLES):
          for k in range ( j+1, len( CHANGE_TUPLES) ):
            rates[k].disable( rates[j].count)
        break

  levelWatch.report( times[-1], outChan) # print watch stats



if __name__ == "__main__":
  # execute only if run as a script
  _test()
