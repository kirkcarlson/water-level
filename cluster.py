#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
cluster: module for monitoring a cluster of power spikes

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

import average
import report
from config import CLUSTER_MULTIPLIER
from config import MAX_DISTANCE_LIMIT
from config import VERB_DEBUG



#### CONSTANTS ####


#### CLASSES ####

class Cluster( object):
  """The consolidated conditions a cluster of power spikes

  A cluster is a series of related waves. Sea waves are near the same period.
  A cluster begins with the detection of coherent waves.
  A cluster ends with the lack of coherent waves for more than one wave period,
  an abrupt change in period, or decrease of power to triggering threshold.
  ... it could be a change in slope of energy to separate "hay stacks" or
  "lumps."

  A cluster is initialized with current values and watch criteria.

  Periodically a value is evaluated by the watch to set the maximum, minimum,
  etc.

  Attributes:
    name: a name representing the consolidated conditions
    level: the current value
    trend: the current value trend (rising, falling, neutral)
    min: the minimum value during the period
    max: the maximum value during the period maxRiseRate: the maximum positive change during the period
    maxFallRate: the maximum negative change during the period
    reversals: the number of trend reversals in the period
    startTick: epoch of consolidation (s)
  """
  # pylint: disable=too-many-instance-attributes
  # Eight is reasonable in this case.

  def __init__(self, name, outChan, multiplier):
    """Return a LevelRegister object whose name is *name*."""
    self.name = name
    self.outChan = outChan
    self.powerAverage = average.Average( "Wave Power Average", "nW?", 500)
    # 500 with 1s waves implies about 8 minutes
    # this maybe should also be at the main level...
    self.powerMultiplier = multiplier
    self.clusterTick = 0 # start time of a cluster arrival
    self.clusterGenTick = 0 # start time of when cluster was generated
    self.maxPower = 0.
    self.maxPowerTick = 0
    self.maxPeriod = 0.
    self.maxPeriodTick = 0
    self.maxPeak = 0.
    self.maxPeakTick = 0
    self.processID = None
    self.distance = 0
    self.energy = 0
    self.waveLength = 0 # also maximum wave length
    self.threshold = 1

    #self.events = []
    #this is an array of:
    #             { # cluster event with the following attributes
    #               'time': None
    #               'distance': None
    #               'period': None
    #               'energy': None
    #             }






  def prReport( self, tick, ):
    """Print a report summarizing the power spike cluster
    """

    ev = "Cluster en: "+\
      "{:.1f} dur: {:.1f} pow: {:4.1f} peak: {:.1f} per: {:.1f}".format(
        self.energy,
        tick - self.clusterTick,
        self.maxPower,
        self.maxPeak,
        self.maxPeriod),
    self.outChan.prEvent( tick , # this marks end of cluster
                          self.name,
                          ev,
                          VERB_DEBUG)


  def isACluster( self, tick, peak, period, power):
    """should the current wave be part of a cluster
  
    Args:
      tick: (float) epoch associated with the level
      power: (float) amount of power for the current wave
      period: length (s) of the current wave
      power: (float) power of the current wave
    
    Returns:
      True if wave qualifies as a cluster
      False if wave does not qualify as a cluster
    
    Raises:
      None
    """

    if self.powerAverage.average is None: # first time, seed ave
      self.powerAverage.update(power) 
      return False
    else:
      self.powerAverage.update(power) 
      self.threshold = self.powerMultiplier * self.powerAverage.average

      if power < self.threshold: # it is not a cluster
        #self.powerAverage.update(power) 
        #sendPowerThreshold( tick, self.threshold)
        return False
      else: # it is a cluster...
        self.energy = self.energy + (power * period)
        if power >= self.maxPower:
          self.maxPowerTick = tick
          self.maxPower = power
        if peak > self.maxPeak:
          self.maxPeak = peak
          self.maxPeakTick = tick
        return True


  def reset( self, tick):
    """reset the statistics for a cluster
  
    Args:
      tick: float epoch associated start of cluster (end of first wave?)
    
    Returns:
      None, although the register object is updated
    
    Raises:
      None
    """
    self.clusterTick = tick
    self.maxPower = 0
    self.maxPowerTick = tick
    self.maxPeriod = 0
    self.maxPeriodTick = tick
    self.maxPeak = 0
    self.maxPeakTick = tick
    self.energy = 0


  def update( self, tick, peak, period, power):
    """update the statistics for a cluster
  
    Args:
      tick: float epoch associated start of cluster (end of first wave?)
      peak: peak to peak wave height in inches
      period: in seconds
      power: in nW?
    
    Returns:
      None, although the register object is updated
    
    Raises:
      None
    """
    if power > self.maxPower:
      self.maxPower = power
      self.maxPowerTick = tick
    self.energy = self.energy + power * period # energy is power * time

    waveSpeed = 32/6.28 * period
    self.waveLength = waveSpeed * period

    distance = 0
    if period < self.maxPeriod:
      maxPeriodWaveSpeed = 32/6.28 * self.maxPeriod
      distance =  (tick - self.maxPeriodTick) * waveSpeed /\
                  (maxPeriodWaveSpeed - waveSpeed)
      if distance > MAX_DISTANCE_LIMIT:
        distance = MAX_DISTANCE_LIMIT
      if distance > self.distance:
        self.distance = distance
      
      self.outChan.prEvent( tick , # this marks begin of event
                            self.name,
                            "Period {:.1f}s wavespeed: {:.1f} ft/s wavelength "\
                                "{:.1f} distance {:.0f}".format(
                                  period, waveSpeed, self.waveLength, distance),
                            VERB_DEBUG)
    if period > self.maxPeriod:
      self.maxPeriod = period
      self.maxPeriodTick = tick
    if peak > self.maxPeak:
      self.maxPeak = period
      self.maxPeakTick = tick


  def analyzePeriod( self, tick, period): # NOT CALLED, OBSOLETE?
    """Analyze the value for real-time limits.
  
    Args:
      tick: float epoch associated with the level
      period: float value to be analyzed
    
    Returns:
      None, although the register object is updated
    
    Raises:
      None
    """

    #Make sure this event qualifies
    if self.processID and period > 1:
      #report period, wavelength, height
      waveSpeed = 32/6.28 * period
      self.waveLength = waveSpeed * period

      #Want only a single line in output, so...
      distance = 0
      if self.maxPeriod > 0: # previous period in this cluster
        if period < self.maxPeriod:
          maxPeriodWaveSpeed = 32/6.28 * self.maxPeriod
          distance =  (tick - self.maxPeriodTick) * waveSpeed /\
                      (maxPeriodWaveSpeed - waveSpeed)
          if distance < MAX_DISTANCE_LIMIT:
            self.distance = distance
          else:
            self.distance = MAX_DISTANCE_LIMIT
      
      self.outChan.prEvent(
        tick , # this marks begin of event
        self.name,
        "Period {:.1f}s wavespeed: {:.1f} ft/s wavelength "\
               "{:.1f} distance {:.0f}".format(
                 period, waveSpeed, self.waveLength, distance),
        VERB_DEBUG)
      if period > self.maxPeriod:
        self.maxPeriod = period
        self.maxPeriodTick = tick


  def freshen(self, period):
    """Removes statistics prior to the saved period.
  
    Args:
      tick: int (s) Number of seconds of data to be saved.
    
    Returns:
      None
    
    Raises:
      None
    """
    pass
    #self.events = self.events [-period:]


#### FUNCTIONS ####

# pylint: disable=pointless-string-statement
'''
now want something a bit different
outline:
  summarize the spread of frequencies (maybe in terms of boatlength)
    this may tell us something more about the boat
    may want spectral analysis to do this more properly

  is this a specialized watch or is this a different critter altogether?
    started with same sort of event -- power
    for high traffic times may need to track multiple highPeriods within a cluster at a time
'''
# pylint: enable=pointless-string-statement


def _test():
  """tests the functions of this module

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  clusterOutChan = report.ReportChannel( "")
  test = Cluster( 'Test Cluster', clusterOutChan, CLUSTER_MULTIPLIER)

  ### VARIABLES AND TEST DATA ###
  # data is time, period, power, powerAverage tuples
  data = [( 1.,  1.,    .5, .5),
          ( 2.,  1.,    .5, .5),
          ( 3.,  1.,    .5, .5),
          ( 4.,  2.1, 10.2, .5),
          ( 6.1, 2.0, 11.5, .5),
          ( 8.1, 1.4,  5.5, .5),
          ( 9.1, 1.,    .5, .5),
         ]

  ### CODE ###

  for cluster in data:
    #test.analyzePower( cluster[0], cluster[2], cluster[1], cluster[3])
    test.analyzePeriod( cluster[0], cluster[1])


if __name__ == "__main__":
  # execute only if run as a script
  _test()
