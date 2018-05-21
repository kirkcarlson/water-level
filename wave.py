#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
wave - module for holding wave data

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

import stats
import watch
#import cluster
#from config import CLUSTER_MULTIPLIER



#### CLASSES ####

# pylint: disable=too-many-instance-attributes
class Wave (object):
  """Wave."""


  def __init__ (self, tick):
    """Return a Wave object.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    import report

    self.times = [] # all of the samples below use this common time list

    self.peaks = stats.Stats([ ("Short",2), ("Medium", 3*30)]) # 3 seconds
    self.peakwatch = watch.Watch("Wave peak", 0, tick, 2)
    self.periods = stats.Stats([ ("Short",2), ("Medium", 3*30)]) # 3 seconds
    self.periodwatch = watch.Watch("Wave period", 0, tick, 4)
    self.powers = stats.Stats([ ("Short",2), ("Medium", 3*30)]) # 3 seconds
    self.powerwatch = watch.Watch("Wave power", 0, tick, 10)
    reportChan = report.ReportChannel("")


#pylint: disable=too-many-arguments
  def analyze( self, tick, peak, period, power, reportChan):
    """Add a wave measurement to the running statistics.
  
    Args:
      tick: float epoch (s) The time of the measurement.
      peak: float (in) The peak to peak height of the wave.
      period: float (s) The wave period between two zero crossings.
      power: float (nW) The power of the wave.
    
    Returns:
      True if wave qualifies as a cluster
      False if wave does not qualify as a cluster
    
    Raises:
      None
    """
    self.times.append(tick)

    self.peakwatch.analyze(tick, peak, reportChan)
    self.peaks.analyze(peak)
    self.periodwatch.analyze(tick, period, reportChan)
    self.periods.analyze(period)
    self.powerwatch.analyze(tick, power, reportChan)
    self.powers.analyze(power)
#pylint: enable=too-many-arguments


  def report (self, tick, reportChan):
    """Generate reports for various parameters
  
    Args:
      tick: (float) (s) current time as an epoch
      reportChan: (object) output channel for the report
    
    Returns:
      None
    
    Raises:
      None
    """
    self.peakwatch.report( tick, reportChan)
    self.peaks.report( "Wave Peak", tick, reportChan)
    self.periodwatch.report( tick, reportChan)
    self.periods.report( "Wave Period", tick, reportChan)
    self.powerwatch.report( tick, reportChan)
    self.powers.report( "Wave Power", tick, reportChan)


  def freshen (self, period):
    """Clear data arrays before the saved period of time.
  
    Args:
      period: (int) (s) time to preserve in the current lists
    
    Returns:
      None
    
    Raises:
      None
    """
    self.times = self.times [-period:]
    self.peaks.freshen(period)
    self.periods.freshen(period)
    self.powers.freshen(period)


  def test(self):
    """Test the functions and methods of this module.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    # set up some levels
    tests = [
        #tick, peak, period, power
        [ 1.,  .3, 2.2, .1],
        [ 4.,  .5, 1.2, .2],
        [ 7.,  .1, 4.2, .3],
        [ 9.,  .2, 3.2, .2],
        [ 12., .5, 5.5, .1],
        [ 20., .2, 1.2, .2]
    ]
    for i in range (0,len(tests)):
      testdata = {  'tick':    tests[i][0],
                    'peak':    tests[i][1],
                    'period':  tests[i][2],
                    'power':   tests[i][3]
                 }
      self.analyze( **testdata )
      #self.analyze( tick, peak, period)


    print "testing freshen"
    self.freshen (3)
# pylint: enable=too-many-instance-attributes


if __name__ == "__main__":
  # execute only if run as a script
  RW = Waves(0) 
  RW.test()
