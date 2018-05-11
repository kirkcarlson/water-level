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



#### CLASSES ####

class Trap ( object):
  """Trap values that are either too high or too low."""

  def __init__ (self, high, low, units, span, name="", port=None):
    """Initialze a trap object
  
    Args:
      high: (float) high limit of good values
      low: (float) low of good values
      units: (string) units used in reports
      span: (int) number of samples in hysteresis
      port: (obj) optional output port for report
      name: (string) optional name of the trap for reports
      
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
    


  def reset (self, seed):
    """reset a trap object
  
    Args:
      seed: (float) initial value of average
      
    Returns:
      None
    
    Raises:
      None
    """
    self.inRangeCount = 0


  def append( self, value):
    """Append a value to a trap

    Returns False unless an out of range value is found. Only one True
    is sent for a series of out of range values until the value returns
    to in range values for a period of time.

    May trigger a report.

    Args:
      value
    
    Returns:
      boolean indicated whether trap was tripped
    
    Raises:
      None
    """

    if value > self.high: # out of range
      if self.inRangeCount is 0: # first time
        self.inRange = self.span # start count down
        if self.port is not None:
          self.report(self, value, self.port)
        return True
      else:
        self.inRangeCount = self.inRangeCount - 1

    elif value < self.low: # out of range
      if self.inRangeCount is 0: # first time
        self.inRange = self.span # start count down
        if port is not None:
          self.report(self, value, port)
        return True
      else:
        self.inRangeCount = self.inRangeCount - 1

    else: # in range
      if self.inRangeCount > 0: # hysteresis
        self.inRangeCount = self.inRangeCount - 1
    return False
    
    
  def report( self, value, reportChan):
    """Report the exceding of a trap
  
    Args:
      value: (float) value to be reported
      reportChan: destination for the report
    
    Returns:
      None
    
    Raises:
      None
    """

    # just a dummy for now
    if value > self.high:
      print "{0} too high is {1}".format( self.name, value)
    elif value < self.low:
      print "{0} too low is {1}".format( self.name, value)


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


  def _test_(self):
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
      self.append( test)
    print "{0}: {1}".format( self.name,  self.getString())
    for test in tests[-4:]:
      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.reset(25)
      self.append( test)
    print "{0}: {1}".format( self.name,  self.getString())


if __name__ == "__main__":
  testTrap = Trap( 27, -1, "in", 3, name="test trap")
  testTrap._test_()
