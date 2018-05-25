#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
trap - module for trapping high and low values

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

from config import VERB_COMMON


#### CLASSES ####

# pylint: disable=too-many-instance-attributes
class Trap ( object):
  """Trap values that are either too high or too low."""

  # pylint: disable=too-many-arguments
  def __init__ (self, high, low, units, span, name="", port=None):
    """Initialze a trap object
  
    Args:
      high: (float) high limit of good values
      low: (float) low of good values
      units: (string) units used in reports
      span: (int) number of samples in hysteresis
      name: (string) optional name of the trap for reports
      port: (obj) optional output port for report
      
    Returns:
      False: value is in range or no change from previous report
      True: value is out of range
    
    Raises:
      None
    """
    self.low = low + 0.
    self.high = high + 0.
    self.units = units
    self.span = span
    self.inRangeCount = 0
    self.name = name
    self.port = port
  # pylint: enable=too-many-arguments
    


  def reset (self):
    """reset a trap object
  
    Args:
      seed: (float) initial value of average
      
    Returns:
      None
    
    Raises:
      None
    """
    self.inRangeCount = 0


  def update( self, tick, value):
    """Update the trap with a new value

    Returns False unless an out of range value is found. Only one True
    is sent for a series of out of range values until the value returns
    to in range values for a period of time.

    May trigger a report.

    Args:
      tick: (float)(s) Epoch of value
      value: (float) value to be checked
    
    Returns:
      boolean indicated whether trap was tripped
    
    Raises:
      None
    """

    if value > self.high: # out of range
      if self.inRangeCount is 0: # first time
        self.inRangeCount = self.span # start count down
        self.report(tick, value)
        return True
      else:
        self.inRangeCount = self.inRangeCount - 1

    elif value < self.low: # out of range
      if self.inRangeCount is 0: # first time
        self.inRangeCount = self.span # start count down
        self.report(tick, value)
        return True
      else:
        self.inRangeCount = self.inRangeCount - 1

    else: # in range
      if self.inRangeCount > 0: # hysteresis
        self.inRangeCount = self.inRangeCount - 1
    return False
    
    
  def report( self, tick, value):
    """Report the exceding of a trap
  
    Args:
      tick: (float)(s) epoch of the event
      value: (float) value to be reported
      reportChan: destination for the report
    
    Returns:
      None
    
    Raises:
      None
    """

    if self.port is None:
      if value > self.high:
        print "{0} too high is {1}".format( self.name, value)
      elif value < self.low:
        print "{0} too low is {1}".format( self.name, value)
    else:
      if value > self.high:
        self.port.prEvent(
          tick,
          "Trap",
          "{0} too high is {1}".format( self.name, value),
          VERB_COMMON)
      elif value < self.low:
        self.port.prEvent(
          tick,
          "Trap",
          "{0} too low is {1}".format( self.name, value),
          VERB_COMMON)



  def getString ( self):
    """Get the value in a string
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """

    return "{0}..{1} {2}".format( self.low, self.high, self.units)


  def test(self):
    """Test the functions and methods in this module.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    tests = [ 25., 26., 27., 28., 29., 28., 27., 26., 25., 26., 27.]
    for test in tests:
      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.update( 0, test)
    print "{0}: {1}".format( self.name,  self.getString())
    for test in tests[-4:]:
      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.reset()
      self.update( 0, test)
    print "{0}: {1}".format( self.name,  self.getString())
# pylint: enable=too-many-instance-attributes



if __name__ == "__main__":
  testTrap = Trap( 27, -1, "in", 3, name="test trap")
  testTrap.test()
