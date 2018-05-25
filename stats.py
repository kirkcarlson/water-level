#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
stats - module for keeping track of a running average, standard deviation and coefficient of variation

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

import math

from config import VERB_COMMON


#### CLASSES ####
# pylint: disable=too-many-instance-attributes

class Stats ( object):
  """Keep running average, standard deviation and coefficient of variation."""

  def __init__ (self, name, units, span):
    """Initialze a statistics object
  
    Args:
      name: (string) name of average value used in reports
      units: (string) units of value used in reports
      span: (int) number of samples in series
      
    Returns:
      None
    
    Raises:
      None
    """
    self.name = name
    self.units = units
    self.span = span

    self.first = True
    self.average = 0
    self.powerSumAverage = 0
    self.standardDeviation = 0
    self.coefficientOfVariation = 1


  def reset (self):
    """reset a statistics object
  
    Args:
      None
      
    Returns:
      None
    
    Raises:
      None
    """
    self.first = True
    self.powerSumAverage = 0
    self.standardDeviation = 0
    self.coefficientOfVariation = 1


  def update( self, value):
    """Update the running statistics with a new value
  
    Args:
      value: (float) the value to update the running statistics
    
    Returns:
      None
    
    Raises:
      None
    """

    if self.first:
      self.first = False

      mean = value
      powerSumAve = value * value
      stdDeviation = 0
      coefficientOfVariation = 0

    else:
      mean = self.average + (value - self.average) / self.span
      powerSumAve = self.powerSumAverage
      powerSumAve = powerSumAve + \
          (value * value - powerSumAve) / self.span
      try:
        stdDeviation = math.sqrt(
          abs(powerSumAve * value - value * mean * mean / (self.span - 1) ) )
      except ValueError:
        print "Standard deviation squared is negative. span:{0:.2f} pSA:{1:.2f} value:{2:.2f} mean:{3:.2f}".format( self.span, powerSumAve, value, mean)
        stdDeviation = 0
      except:
        print "Unexpected error:", 
        print "Standard deviation squared is negative. span:{0:.2f} pSA:{1:.2f} value:{2:.2f} mean:{3:.2f}".format( self.span, powerSumAve, value, mean)
        raise
      coefficientOfVariation = stdDeviation / mean * 100 #percent

    self.average = mean
    self.powerSumAverage = powerSumAve
    self.standardDeviation = stdDeviation
    self.coefficientOfVariation = coefficientOfVariation
            

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

    reportChan.prEvent (reportTick,
                        "Stat",
                        "{0} average is {1}".format(
                          self.name, self.average),
                        VERB_COMMON)
    reportChan.prEvent (reportTick,
                        "Stat",
                        "{0} standard deviation is {1}".format(
                          self.name, self.standardDeviation),
                        VERB_COMMON)
    reportChan.prEvent (reportTick,
                        "Stat",
                        "{0} coefficient of variation is {1}".format(
                          self.name, self.coefficientOfVariation),
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

    return "{0:.2f}".format( self.average), \
           "{0:.2f}".format( self.standardDeviation), \
           "{0:.2f}".format( self.coefficientOfVariation)



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
    ave, sd, cv = self.getString()
    print "{0}: ave {1} SD {2} CV {3}".format( self.name,  ave, sd, cv)
    for test in tests[-4:]:
      self.reset()
      self.update( test)
    ave, sd, cv = self.getString()
    print "{0}: ave {1} SD {2} CV {3}".format( self.name,  ave, sd, cv)

# pylint: enable=too-many-instance-attributes



if __name__ == "__main__":
  testStats = Stats( "test level", "in", 25)
  testStats.test()
