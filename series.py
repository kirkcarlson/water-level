#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
series - module for handling time series

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

import report
import stats
import watch



#### CLASSES ####

class Series( object):
  """Manage a time series."""

  def __init__ (self, name, units):
    """Initialze a Level object
  
    Args:
      name
    
    Returns:
      None
    
    Raises:
      None
    """
    self.name = name
    self.units = units
    self.values = []


  def append( self, value):
    """Append a value to a time series
  
    Args:
      value: (float) value to be appended to time series
    
    Returns:
      None
    
    Raises:
      None
    """

    self.values.append( value)


  def report( self):
    """Report on something, but that's not clear
  
    Args:
      reportChan: destination for the report
      currentTick: epoch correspoinding to the time for the report
    
    Returns:
      None
    
    Raises:
      None
    """

    self.watch.report( currentTick, reportChan)
    self.stats.report( self.name, currentTick, reportChan)
       

  def freshen (self, numberToKeep):
    """Clean up time series
  
    Args:
      numberToKeep: (int) number of values to preserve
    
    Returns:
      None
    
    Raises:
      None
    """
    self.values = self.values [-numberToKeep:]


  def _test_(self):
    """Test the functions and methods in this module.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    tests = [1,2,3,4,5,6,7,8,9,10]
    for test in tests:
      self.append(test)
    print "values", self.values
    if len(self.values) is not len( tests):
      print "Append got wrong length, expected {0}, got {1}".format(
          len(test), len(self.values))
      exit(1)
    for i, test in enumerate( tests):
      if test is not self.values[i]:
        print "Append did not work, expected {0}, got {1}".format(
            test, self.values[i])
        exit(1)

    self.freshen (5)
    print "freshened values", self.values
    if len(self.values) is not 5:
      print "Freshen got wrong length, expected {0}, got {1}".format(
          5, len(self.values))
      exit(1)
    for i, test in enumerate( tests[-5:]):
      if test is not self.values[i]:
        print "Freshen did not work, expected {0}, got {1}".format(
            test, self.values[i])
        exit(1)

    line = self.getLine (4)
    print "line", line
    if len(line) is not 2:
      print "getline got wrong length, expected 2, got {0}".format(
          len(line))
      exit(1)
    if len( line['points']) is not 4:
      print "getline got wrong length, expected {0}, got {1}".format(
          4, len( line['points']))
      exit(1)
    for i, test in enumerate( tests[-4:]):
      if test is not line['points'][i]:
        print "getline got wrong point, expected {0}, got {1}".format(
            test, line['points'][i])
        exit(1)
    if line['label'] is not self.name:
      print "getline got wrong label, expected {0}, got {1}".format(
          self.name, line['label'])
      exit(1)
    exit(0) #success
 

if __name__ == "__main__":
  testSeries = Series("test")
  testSeries._test_()
