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

import datetime

from influxdb import InfluxDBClient

import report
import plot
from config import CLUSTER_WINDOW
from config import CLUSTER_MULTIPLIER
from config import MAX_DISTANCE_LIMIT




#### CONSTANTS ####

#### globals ####
client = None


#### CLASSES ####

class Cluster( object):
  """The consolidated conditions a cluster of power spikes

  A cluster is initialized with current values and watch criteria.

  Periodically a value is evaluated by the watch to set the maximum, minimum,
  etc.

  Attributes:
    name: a name representing the consolidated conditions
    level: the current value
    trend: the current value trend (rising, falling, neutral)
    min: the minimum value during the period
    max: the maximum value during the period
    maxRiseRate: the maximum positive change during the period
    maxFallRate: the maximum negative change during the period
    reversals: the number of trend reversals in the period
    startTick: epoch of consolidation (s)
  """
  # pylint: disable=too-many-instance-attributes
  # Eight is reasonable in this case.

  def __init__(self, name, outChan, multiplier):
    global client
    """Return a LevelRegister object whose name is *name*."""
    self.name = name
    self.outChan = outChan
    self.powerMultiplier = multiplier
    self.clusterTick = 0 # start time of a cluster arrival
    self.clusterGenTick = 0 # start time of when cluster was generated
    self.maxPower = 0.
    self.maxPowerTick = 0
    self.maxPeriod = 0.
    self.maxPeriodTick = 0
    self.processID = None
    self.distance = 0
    self.energy = 0
    self.waveLength = 0 # also maximum wave length

    self.events = []
    #this is an array of:
    #             { # cluster event with the following attributes
    #               'time': None
    #               'distance': None
    #               'period': None
    #               'energy': None
    #             }

    # initialize influxdb channel
    client = InfluxDBClient(host='localhost', port=8086)
    databaseName = "waterlevel"
    if databaseName not in client.get_list_database():
      client.create_database( databaseName)
      client.create_retention_policy("keep forever", "INF", 1,
              database=databaseName)

    client.switch_database( databaseName)



  def reportDummy ( self):
    """Dummy scheduling function for reporting a cluster end event"""
    from main import currentTick

    self.report( currentTick)


  # would like a timed event for the end of the cluster to make the report more timely
  # would have to modify the event due time with each new qualifying spike

  def report( self, tick):
    """Print a report summarizing the power spike cluster
    """
    self.outChan.prEvent( tick , # this marks end of cluster
                          self.name,
                          "cluster end energy: {:.1f} max power: {:4.1f} duration: {:.1f} "\
                              "max period: {:.1f}".format(
                                  self.energy,
                                  self.maxPower,
                                  tick-self.clusterTick,
                                  self.maxPeriod),
                           report.VERB_DEBUG)

    # add the cluster to the log of events
    self.events.append ( { 'time': self.clusterTick,
                           'distance': self.distance,
                           #'boatLength': self.boatLength,
                           'period': self.maxPeriod,
                           'energy': self.energy,
                         } )

    # reset accumulators for the cluster
    self.energy = 0.
    self.maxPower = 0.
    self.maxPowerTick = 0
    self.maxPeriod = 0.
    self.maxPeriodTick = 0
    self.processID = None # assume that this was called by the scheduler

  def analyzePower( self, tick, power, period, powerAverage):
    """Analyze the power spike for inclusion in cluster
  
    Args:
      tick: (float) epoch associated with the level
      power: (float) amount of power for the current wave
      period: length (s) of the current wave
      powerAverage: (float) average power over the long term
    
    Returns:
      None, although the register object is updated
    
    Raises:
      None
    """
    from main import schedClusterEnd, unschedClusterEnd

    if power > self.powerMultiplier * powerAverage:
      if self.processID:
        unschedClusterEnd ( self.processID)
      else: # start of a new cluster
        #report start of new cluster
        self.outChan.prEvent( tick , # this marks begin of event
                              self.name,
                                "cluster start".format(
                                  ),
                              report.VERB_DEBUG)
        self.clusterTick = tick
        self.maxPower = power
        self.maxTick = tick
        self.energy = 0
      self.energy = self.energy + (power * period)
      if power >= self.maxPower:
        self.maxPowerTick = tick
        self.maxPower = power
      self.processID = schedClusterEnd (self.reportDummy, tick,
                                        CLUSTER_WINDOW)


  def analyzePeriod( self, tick, period):
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
      
      self.outChan.prEvent( tick , # this marks begin of event
                            self.name,
                            "Period {:.1f}s wavespeed: {:.1f} ft/s wavelength "\
                                "{:.1f} distance {:.0f}".format(
                                    period, waveSpeed, self.waveLength, distance),
                            report.VERB_DEBUG)
      sendClusterEvent( time=tick,
                        distance=distance,
                        period=self.maxPeriod,
                        energy=self.energy #####guessing here...
                      )
      if period > self.maxPeriod:
        self.maxPeriod = period
        self.maxPeriodTick = tick


###CHANGE OF STRATEGY... send arrays of numbers to plot routine and let it figure out
### colors, shapes, positions, etc.

  def plot(self, numberToPlot, plotName):
    """ Plot the distance and size against time of power spike clusters

    Args:
      numberToPlot: number of seconds to plot
    
    Returns:
      None
    
    Raises:
      None
    """

    print "Plotting cluster"
    # find the number of points to plot, given the number of seconds
    if len(self.events) > 1:
      endTime = self.events[-1]["time"]
      startTime = endTime - numberToPlot
      numberToPlot = len(self.events)
      for event in self.events:
        if event['time'] > startTime:
          break
        numberToPlot = numberToPlot - 1
      print "Plotting cluster", numberToPlot
      if numberToPlot > 0:
        times = []
        distances = []
        energys = []
        periods = []
        for event in self.events [-numberToPlot:]: 
          times.append( event['time'])
          distances.append( event['distance'])
          energys.append( event['energy'])
          #boatLengths.append( event['boatLength'])
          periods.append( event['period'])
  
        plot.plotCluster (plotName, numberToPlot, times, distances, periods, energys)


  def freshen(self, period):
    """Removes statistics prior to the saved period.
  
    Args:
      tick: int (s) Number of seconds of data to be saved.
    
    Returns:
      None
    
    Raises:
      None
    """
    self.events = self.events [-period:]


#### FUNCTIONS ####

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

def sendClusterEvent( time, distance, period, energy ):
  """send cluster event to the InfluxDB server

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  # send measurements to the influxdb

  walltime = datetime.datetime.now()
  daydiff = (walltime - datetime.datetime.fromtimestamp(time)).days
  tickDiff = daydiff * 24 * 3600 # offset to yesterday for now
  offsetTick = time + tickDiff # offset to yesterday for now

  json_body = []
  # should only do the following once...
  
  json_body = [
    {
      "measurement" : "cluster",
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        'distance': distance+0.,
        'period': period+0.,
        'energy': energy+0.,
      }
    }
  ]
  if not client.write_points(json_body):
    print "Not updating database"
      

  


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
    test.analyzePower( cluster[0], cluster[2], cluster[1], cluster[3])
    test.analyzePeriod( cluster[0], cluster[1])


if __name__ == "__main__":
  # execute only if run as a script
  _test()
