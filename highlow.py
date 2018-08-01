#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
highlow - module for keeping track of high and low value

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

class HighLow ( object):
  """Keep track of the high and low value."""

  def __init__ (self, name, units):
    """Initialze a highlow object
  
    Args:
      name: (string) name of average value used in reports
      seed: (float) initial value of average
      span: (int) number of samples in series
      
    Returns:
      None
    
    Raises:
      None
    """
    self.name = name
    self.units = units
    self.first = True
    self.low = None
    self.high = None
    self.open = None
    self.close = None

  def reset (self):
    """reset a highlow object
  
    Args:
      seed: (float) initial value of average
      
    Returns:
      None
    
    Raises:
      None
    """
    self.first = True
    self.low = None
    self.high = None
    self.open = None
    self.close = None


  def update( self, value):
    """Update a high-low with a new value
  
    Args:
      value
    
    Returns:
      Updated average value
    
    Raises:
      None
    """

    if self.first:
      self.high = value
      self.low = value
      self.open = value
      self.close = value
      self.first = False
    else:
      if value > self.high:
        self.high = value
      if value < self.low:
        self.low = value
      self.close = value


  def report( self, reportTick, reportChan):
    """Report the value of the average
  
    Args:
      reportTick: epoch correspoinding to the time for the report
      reportChan: destination for the report
    
    Returns:
      None
    
    Raises:
      None
    """

    if self.low is None:
        low = '--'
    else:
        low = "{:.2f}".format( self.low)
    if self.open is None:
        open = '--'
    else:
        open = "{:.2f}".format( self.open)
    if self.close is None:
        close = '--'
    else:
        close = "{:.2f}".format( self.close)
    if self.high is None:
        high = '--'
    else:
        high = "{:.2f}".format( self.high)

    hiloReport = self.name +\
            " low:" + low +\
            " open:" + open +\
            " close:" + close +\
            " high:" + high
    reportChan.prReport( reportTick, hiloReport) 


  def getString ( self):
    """Get the values in a string
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """

    return "{0}..{1:.2f} {2:.2f} {3:.2f} {4:.2f}".format(
      self.name, self.open, self.low, self.high, self.close)


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
      self.update( test)
    print self.getString()
    #self.report()
    self.reset()
    for test in tests[-4:]:
      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.update( test)
    print self.getString()
    #self.report()


if __name__ == "__main__":
  testAve = HighLow( "test level", "in")
  testAve.test()
