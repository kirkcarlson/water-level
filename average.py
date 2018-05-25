#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
average - module for calculating a running average

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

#import report


#### CLASSES ####

class Average( object):
  """Average a value over time."""

  def __init__ (self, name, units, span):
    """Initialze an average object
  
    Args:
      name: (string) name of average value used in reports
      units: (string) units of the value used in reports
      span: (int) number of samples in series
      
    Returns:
      None
    
    Raises:
      None
    """
    self.name = name
    self.units = units
    self.span = span
    self.average = None

    self.first = True


  def reset( self):
    """Reset an average
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    self.average = None
    self.first = True


  def update( self, value):
    """Append a value to an average
  
    Args:
      value
    
    Returns:
      Updated average value
    
    Raises:
      None
    """

    if self.first:
      self.first = False
      newAverage = value
    else:
      newAverage = (self.average * (self.span - 1) + value) / self.span
    self.average = newAverage
    return newAverage


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

    aveReport = "{0} average is {1}{2}".format( self.name, self.average, self.units)
    reportChan.prEvent( reportTick, "Ave", aveReport)


  def getString ( self):
    """Get the value in a string
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """

    return "{0} {1}".format( self.average, self.units)


  def test( self):
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
    print "{0}: {1}".format( self.name,  self.getString())


if __name__ == "__main__":
  #testAve = Average("test level", #name
  #               "in", #units
  #               25., #seed
  #               4 #span
  #               )
  testAve = Average( "test level", "in", 4)
  testAve.test()
