#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
rawlevel - module for handling the raw water levels

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

import plot
import report
import stats
import watch



#### CLASSES ####

class Level( object):
  """Water level."""

  # pylint: disable=too-many-arguments
  def __init__ (self, name, seed, tick, hysteresis, aveConfig):
    """Initialze a Level object
  
    Args:
      name
      seed
      tick
      hysteresis
      aveConfig
        list of tuples:
          name
          numberOfSamples in average
    
    Returns:
      None
    
    Raises:
      None
    """
    self.name = name
    self.times = []
    self.levels = []
    self.stats = stats.Stats( aveConfig)
    self.watch = watch.Watch( name, seed, tick, hysteresis)
    #self.waveHeights = []
# want to pass a list of named average periods. [(name,period),...]
# if the list length is zero, no need for stats
# otherwise there should be stats for each period
# the waveHeights is another special array that can be managed by main

  # pylint: enable=too-many-arguments

  def analyze( self, tick, level, reportChan):
    """Append a tuple of values to individual lists.
  
    Args:
      tick
      level
    
    Returns:
      None
    
    Raises:
      None
    """

    self.times.append( tick)
    self.levels.append( level)
    self.stats.analyze( level)
    self.watch.analyze( tick, level, reportChan)

    if len( self.stats.averages) >= 2:
      ##waveHeight = level - self.stats.averages[1][-1]
      # waveHeight = level - self.stats.averages[1][-1]
      # the above is too noisy, the level is too high a frequency so it messes
      # up the period.
      # it does have more extreme wave heights, but...
      #waveHeight = self.stats.averages[0][-1] - self.stats.averages[1][-1]
      # was using waveHeight = shortAves[-1] - longAves[-1]
      # results in some very funny waves with very long periods when the water
      # level is changing... so medium should be the zero crossing value and
      # the long should only be used for the water level
      ##self.waveHeights.append( waveHeight)
      pass # looks like something may have disappeared
       

  def report( self, currentTick, reportChan):
    """Report the latest values of the water level.
  
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
       

  def freshen (self, period):
    """Clear data arrays before a specified period of time.
  
    Args:
      period: (int) seconds to preserve
    
    Returns:
      None
    
    Raises:
      None
    """
    self.times = self.times [-period:]
    self.levels = self.levels [-period:]
    self.stats.freshen( period)
    ##self.waveHeights = self.waveHeights [-period:]


  def plotLevels (self, numberToPlot, name):
    """Plot the water level and averages.
  
    Args:
      numberToPlot: integer number of data elements to plot
      name: string used for the saved filename
    
    Returns:
      None
    
    Raises:
      None
    """
      
    lines = []
    lines.append ({'points':self.levels,           'label':'Water Level'})
    for i, averages in enumerate(self.stats.averages):
      lines.append( {'points':averages,  'label':self.stats.aveConfig[i][0]} )
    plot.plotCommon( name, numberToPlot, self.times, 'Water Level (in)', lines)
  

  '''OBSOLETE
  def plotWaveHeights (self, numberToPlot, name):
    """Plot the wave height.
  
    Args:
      numberToPlot: integer number of data elements to plot
      name: string used for the saved filename
    
    Returns:
      None
    
    Raises:
      None
    """
      
    # plot the data points
    #print "plotWH:",self.waveHeights
    lines = [
        {'points':self.waveHeights,               'label':'Wave Heights'},
        #{'points':self.stats.standardDeviations,
        # 'label':'Standard Deviation'},
        #{'points':self.stats.coefficientOfVariations,
        # 'label':'Coefficient of variation'}
    ]
    times = self.times
    plot.plotCommon( name, numberToPlot, times, 'Wave Height (in)', lines)
  '''


  def test(self):
    """Test the functions and methods in this module.
  
    Args:
      period: (int) seconds to preserve
    
    Returns:
      None
    
    Raises:
      None
    """
    reportChan = report.ReportChannel("")
## this should be strictly levels... not sure how to really test except to
## capture a run and compare it later
    # set up some levels
    tests = [
        [ 1., 25., 25.0, 25.0, 25.0, 0.0, .12, .22 ],
        [ 2., 26., 25.3, 25.2, 25.1, 0.2, .13, .23 ],
        [ 3., 27., 25.6, 25.4, 25.2, 0.4, .14, .24 ],
        [ 4., 28., 25.9, 25.6, 25.3, 0.6, .15, .25 ],
        [ 5., 29., 25.2, 25.8, 25.4, -0.2, .16, .26 ],
        [ 6., 28., 25.5, 26.2, 25.5, 0.0, .17, .27 ],
        [ 7., 27., 25.8, 26.4, 25.6, 0.2, .18, .28 ],
        [ 8., 26., 25.8, 26.2, 25.7, 0.1, .19, .29 ],
        [ 9., 25., 25.5, 26.0, 25.6, -0.1, .18, .28 ],
        [ 10., 26., 25.8, 26.0, 25.7, 0.1, .17, .27 ],
        [ 11., 27., 26.1, 26.2, 25.8, 0.3, .16, .26 ],
    ]
    for i in range (0,len(tests)):
      testdata = {  'tick':               tests[i][0],
                    'level':              tests[i][1],
                    'shortAve':           tests[i][2],
                    'mediumAve':          tests[i][3],
                    'longAve':            tests[i][4],
                    'waveHeight':         tests[i][5],
                    'standardDeviation':  tests[i][6],
                    'signalToNoiseRatio': tests[i][7] }

      # this needs to be updated to use self.analyze(tick,level, reportChan)
      self.analyze( testdata['tick'], testdata['level'], reportChan)

    # generate plots
    print self.__dict__
    #pylint: disable=too-many-function-args
    self.plotLevels (len(tests)+2, "Raw Level Test")
    self.plotWaveHeights (len(tests)-2, "Wave Height")
    self.freshen (3)
    print self.__dict__
    ##self.plotWaveHeights (len(tests), "Wave Height2")
    #pylint: enable=too-many-function-args


if __name__ == "__main__":
  testRL = Level("test level",
                 25., #seed
                 1., #tick
                 .25, # hysteresis
                 [ ("Test Ave",2),] )
  testRL.test()
