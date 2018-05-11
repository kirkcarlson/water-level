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



#### CLASSES ####

class Stats2 ( object):
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


  def append( self, value):
    """Add a value to the running statistics for the variable.
  
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

    # just a dummy for now
    print "{0} average is {1}".format( self.name, self.average)
    print "{0} standard deviation is {1}".format( self.name, self.standardDeviatoin)
    print "{0} coefficient of variation is {1}".format( self.name, self.coefficientOfVariation)


  def getString ( self):
    """Get the value in a string
  
    Args:
      None
    
    Returns:
      None
CoV: -135670.792792 stdD: 0.0132999354559 mean: -9.80309407959e-06

CoV: 102842.021633 stdD: 0.0202727786057 mean: 1.97125438451e-05

Water Level High ##NEW## 32.9606172641  Low 32.4783796817
Wave Heights High ##NEW## 0.204392891219  Low -0.25264025676
pFR 0 17 60 Wake Response Details 0 4
/home/kirk/.local/lib/python2.7/site-packages/matplotlib/cbook/deprecation.py
    
    Raises:
      None
    """

    return "{0:.2f}".format( self.average), \
           "{0:.2f}".format( self.standardDeviation), \
           "{0:.2f}".format( self.coefficientOfVariation)



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
    ave, sd, cv = self.getString()
    print "{0}: ave {1} SD {2} CV {3}".format( self.name,  ave, sd, cv)
    for test in tests[-4:]:
      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.reset()
      self.append( test)
    ave, sd, cv = self.getString()
    print "{0}: ave {1} SD {2} CV {3}".format( self.name,  ave, sd, cv)



if __name__ == "__main__":
  testStats = Stats2( "test level", "in", 25)
  testStats._test_()
