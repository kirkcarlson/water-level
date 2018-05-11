#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
rawwaves - module for holding and analyzing the raw wave data

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
import datetime

import report


#### CONSTANTS ####

FORM = "{:<20} {:>10}"



#### CLASSES ####

#pylint: disable=too-many-instance-attributes

class Stats (object):
  """ Class for holding and calculating running statistics on a variable."""

  def __init__(self, statsConfig):
    """Initialize the attributes of this instance of the class

    Args:
      statsConfig: array of name, numberOfSamples tuples
        name: name of the average
        numberOfSamples: number of samples in the running average

    Returns:
      None

    Raises:
      None
    """
    self.values = []
    self.standardDeviations = []
    self.coefficientOfVariations = []
    self.aveConfig = statsConfig
    self.averages = [] # list of lists
    for _ in self.aveConfig:
      self.averages.append([])
    self.powerSumAverage = 0
    #self.sumOfSquares = 0
    self.first = True

  def analyze( self, value):
    """Add a value to the running statistics for the variable.
  
    runningAve = (value + (n-1)runningAve)/n
    runningStdDev = (value + (n-1)runningSum)/n
count, mean, m2
count = count + 1
delta = newValue - mean
mean = mean + delta/count
delta2 = newValue - mean
M2 = M2 + delta * delta2

    sigma squared = 1/(count+1) (sum of squares -(sum*sum)/count)
    count = 0 # number of samples processed
    sumOfSquares = 0
    sum = 0
    for each newValue:
      count = count + 1
      sumOfSquares = sumOfSquare + (newValue * newValue)
      sum = sum + newValue
    mean = sum/count
    stdDev - sqrt( sumOfSquares - (sum * sum) / (count - 1))

again:
  n = n + 1... actually it is fixed

  mean = mean + (value-mean)/ n
  pwrSumAvg = pwrSumAvg + (x * x - pwrSumAvg) / n
  stdDev = sqrt( (pwrSumAvg * n - n * mean * mean) / ( n-1) )
---
    Args:
      value: float the value.
    
    Returns:
      None
    
    Raises:
      None
    "-"-"
    self.values.append(value)

    if self.first:
      self.first = False

      for ave in self.averages:
        ave.append( value)
      self.sumOfSquares = self.sumOfSquares * self.sumOfSquares
      self.standardDeviations.append( 0)
      self.coefficientOfVariations.append( 1)
    else:

      for i, average in enumerate( self.averages):
        aveage.append( util.runningAverage( average[-1], value,
                                            self.aveConfig[i][1]) )

      if len(self.aveConfig) >= 2: # need a medium average to do stats
        self.sumOfSquares = util.runningAverage(
            self.sumOfSquares,
            self.averages[0][-1] * self.averages[0][-1],
            self.aveConfig[1][1])
        diff = self.sumOfSquares -(self.averages[1][-1] * self.averages[1][-1])
D
        if diff < 0:
          diff = -diff
        #NOTE This isn't stable enough... maybe it need to be always on long
        #     average, look this up again
        self.standardDeviations.append( math.sqrt (diff))
        self.coefficientOfVariations.append( self.standardDeviations[-1] /\
            self.averages[1][-1] * 100) # percent
        #print currentWaveHeight, sumOfSquares, longAve, longAve*longAve,
        #    standardDeviation, coefficientOfVariation


  calulations from
    https://subluminal.wordpress.com/2008/07/31/running-standard-deviations/
"""

    self.values.append(value)
    if self.first:
      self.first = False

      mean = value
      powerSumAve = value * value
      stdDeviation = 0
      coefficientOfVariation = 1

      for ave in self.averages:
        ave.append( mean)

    else:
      for i, average in enumerate( self.averages):
        n = self.aveConfig[i][1] # use the N from the medium
        mean = average[-1]
        mean = mean + (value - mean) / n
        average.append( mean)

      if len( self.averages) >= 2:
        mean = self.averages[1][-1] # use updated medium for the mean
        powerSumAve = self.powerSumAverage
        powerSumAve = powerSumAve + (value * value - powerSumAve) / n
        stdDeviation = math.sqrt( abs(
            (powerSumAve * value - value * mean * mean) / (n-1) ))
        # the following is for coefficient of variation (CV)
        coefficientOfVariation = stdDeviation / mean * 100 #percent
        # signalToNoiseRation should be Power of signal/Power of noise
        # which becomes stdDeviation of Signal squared/stdDeviation of noise
        self.powerSumAverage = powerSumAve
        self.standardDeviations.append( stdDeviation)
        self.coefficientOfVariations.append( coefficientOfVariation)
        #print "stats value:{0:.2f} mean:{1:.2f} pSA:{2:.2f} SD:{3:.2f}" +
        #     " SNR:{4:.2f}".format(
        #     value, mean, powerSumAve, stdDeviation, coefficientOfVariation)
            

  def report(self, topic, time, reportChan):
    """Generate a text report for the indicated channel
  
    Args:
      topic: the overall topic of the report (i.e., what is being monitored)
      time: the time represented by the report
      reportChan: ReportChannel for sending the report
    
    Returns:
      None
    
    Raises:
      None
    """
    print time, reportChan  # dummy for now
    if len( self.averages) >= 2:
      print "{0} stats mean:{1:.2f} pSA:{2:.2f} SD:{3:.2f} SNR:{4:.2f}".format(
          topic,
          self.averages[0][-1],
          self.powerSumAverage,
          self.standardDeviations[-1],
          self.coefficientOfVariations[-1])
    elif len( self.averages) == 1:
      print "stats mean:{0:.2f}".format( self.averages[0][-1])
      #  print "stats.report self.averages:",
      #      len( self.averages), len( self.averages[0])
    else:
      print "unable to generate stats.report self.averages"
            



  def report2(self, topic, tick, reportChan):
    """Generate a text report for the indicated channel
  
    Args:
      reportChan: ReportChannel for sending the report
      topic: the overall topic of the report (i.e., what is being monitored)
      time: the time represented by the report
    
    Returns:
      None
    
    Raises:
      None
    """
    reportChan.prReport( "---")
    reportChan.prReport( FORM.format("Report for", topic) )
    print "Report", tick, datetime.datetime.fromtimestamp (float(tick))
    #reportChan.prReport( FORM.format("Report time {:%b %d %H:%M:%S}".format(
    #    datetime.datetime.fromtimestamp (float(tick))) ) )

    reportChan.prReport( FORM.format(
        "Average",
        "{:5.2f}".format(self.values[-1])) )

    for i, indConfig in enumerate( self.aveConfig):
      reportChan.prReport( FORM.format(
          indConfig[0] + " average",
          "{:5.2f}".format( self.averages[i][-1])) )
    if len(self.averages) >= 2: # need a medium average to do stats
      reportChan.prReport( FORM.format(
          "Standard deviation",
          "{:5.2f}".format( self.standardDeviations[-1]) ))
      reportChan.prReport( FORM.format(
          "Coefficient of variation",
          "{:5.2f}".format( self.coefficientOfVariations[-1]) ))



  def freshen(self, period):
    """Removes statistics prior to the saved period.
  
    Args:
      tick: int (s) Number of seconds of data to be saved.
    
    Returns:
      None
    
    Raises:
      None
    """
    self.values = self.values [-period:]
    for average in self.averages:
      average = average[ -period: ]
    self.standardDeviations = self.standardDeviations [-period:]
    self.coefficientOfVariations = self.coefficientOfVariations [-period:]
  #pylint: enable=too-many-instance-attributes


  def _test_(self):
    """Test the functions and methods of this module.
  
    Args:
      None
    
    Returns:
      None
    
    Produces:
      Report for             testAve
      Report 300 1969-12-31 19:05:00
      Average                    0.20
      testAve average            0.29
      Standard deviation         0.00
      Coefficient of variance    1.00    

    Raises:
      None
    """
    # set up some levels
    tests = [
        #tick, value
        [ 1.,  .3],
        [ 4.,  .5],
        [ 7.,  .1],
        [ 9.,  .2],
        [ 12., .5],
        [ 20., .2]
    ]
    for i in range (0,len(tests)):
      testdata = {  #'tick':    tests[i][0],
          'value':   tests[i][1]
      }
      self.analyze( **testdata )
      #self.analyze( tick, peak, period)

    print self.__dict__
    RC = report.ReportChannel( "")
    self.report2( "TestData", 5*60, RC)

    print "testing freshen"
    self.freshen (3)
    print self.__dict__

if __name__ == "__main__":
  # execute only if run as a script
  aveConfig = [ ("testAve", 4 )]
  stats = Stats(aveConfig) 
  #pylint: disable=protected-access
  stats._test_()
  #pylint: enable=protected-access
