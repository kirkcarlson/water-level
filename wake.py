# !/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
""" wake: module for collecting the parts of a wake

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

import influx


#### CONSTANTS ####


#### ENUMERATED TYPES ####


#### CLASSES ####

class Wake(object):
    """Keep track of attributes of an individual wake cluster.
    
    Normal cycle of methods:
    init -- only to create an instance of the class
    reset -- before every wake cluster
    update -- to add one or more wave to the wake cluster
    close -- to close the current wake cluster and update statistics
    report -- to report on the accumulated wake cluster. This may be done
      at any time, but normally after a close and before a reset.

    """ 

    def __init__(self, outChan, influxObj):
        """initialize the attributes of an individual wake cluster

        Args:
          outChan: channel for output stream
          influxObj: influx object for communicating with InfluxDB

        Returns:
          None

        Raises:
          None
        """
        self.outChan = outChan
        self.ifx = influxObj
        # self.clusterTick = 0   # start time of a cluster arrival
        self.tick = None
        self.minPeriod = None
        self.maxPeriod = 0
        self.minPeak = None
        self.maxPeak = 0
        self.minPower = None
        self.maxPower = 0
        self.lastPower = 0
        self.totPower = 0
        self.startTime = None
        self.distance = 0
        self.numberOfCrests = 0
        self.lastWaveLength = 0
        self.firstPeriod = 0
        self.lastPeriod = 0
        self.lastTime = None


    def reset(self):
        """reset the attributes of a wake

        Args:
          None

        Returns:
          None

        Raises:
          None
        """
        self.minPeriod = None
        self.maxPeriod = None
        self.minPeak = None
        self.maxPeak = 0
        self.minPower = None
        self.maxPower = 0
        self.lastPower = 0
        self.firstPeriod = 0
        self.lastPeriod = 0
        self.totPower = 0
        self.startTime = None
        self.distance = 0
        self.numberOfCrests = 0


    def update( self, tick, period, peak, power):
        """update the attributes of a wake with the attributes of a wave

        Args:
          self: the wake object
          tick: float (s) time of the end of the wave
          period: float (s) period of the wave
          peak: float (in) peak to peak height of the wave
          power: float (mW?) power of the wave
          

        Returns:
          None

        Raises:
          None
        """
        dtd = datetime.datetime.fromtimestamp( tick)
        print "  wake.update {:%H:%M:%S}.{:02d} per:{:.2f} pk:{:.2f} pow:{:.2f}".format(\
                dtd, dtd.microsecond/10000, period, peak, power)

        if self.startTime == None:
            self.firstPeriod = period
            self.startTime = tick
        if self.minPeriod is None or period < self.minPeriod:
            self.minPeriod = period
        if period > self.maxPeriod:
            self.maxPeriod = period
            self.maxPeriodTick = tick
        if self.minPeak is None or peak < self.minPeak:
            self.minPeak = peak
        if peak > self.maxPeak:
            self.maxPeak = peak
            self.maxPeakTick = tick
        if self.minPower is None or power < self.minPower:
            self.minPower = power
        if power > self.maxPower:
            self.maxPower = power
            self.maxPowerTick = tick
        self.totPower = self.totPower + power
        self.numberOfCrests = self.numberOfCrests + 1
        self.lastPower = power
        self.lastTime = tick
        self.lastPeriod = period


    def close( self):
        """close the attributes of a wake with internal calculations

        Args:
          self: the wake object

        Returns:
          None

        Raises:
          None
        """
        self.distance = calculateDistance( self.firstPeriod,
                self.lastPeriod,
                self.lastTime - self.startTime)
        distance = self.distance
        if distance > 3000:
            distance = 3000
        period = (self.firstPeriod + self.lastPeriod) / 2
        if period > 4:
            period = (self.lastTime - self.startTime) / \
                    self.numberOfCrests # another average period
        if period > 4:
            period = self.firstPeriod
        if period > 4:
            period = self.lastPeriod
        if period > 4:
            period = 4
        # Period x wave speed = wave length
        # wave speed =~ [wave period]g /2pi
        # wave lenth = period x period x g / 2pi
        wavelength = period * period * 32.174 / 2 /3.1414
        self.ifx.sendPoint( self.startTime, "cluster", "wakePeriod", 
                period)
        self.ifx.sendPoint( self.startTime, "cluster", "wakeWavelength", 
                wavelength)
        self.ifx.sendPoint( self.startTime, "cluster", "wakeDistance",
                distance)
        self.report() # this should be temporary


    def getAttributes(self):
        """get the attributes on an individual wake cluster

        Args:
          self: the wake object

        Returns:
            'startTime' : startTime (s) starting time of the wake cluster
            'minPeriod' : minPeriod minimum period of the wake cluster
            'maxPeriod' : maxPeriod maximum period of the wake cluster
            'minPeak' : minPeak minimum peak of the wake cluster
            'maxPeak' : maxPeak maximum peak of the wake cluster
            'minPower' : minPower minimum power of the wake cluster
            'maxPower' : maxPower maximum power of the wake cluster
            'totPower' : totPower total power of the wake cluster
            'duration' : duration duration of the wake wake cluster
            'numCrests' : numberOfCrests number of crests in the wake cluster
            'distance' : distance to source of wake in feet

        Raises:
          None

>>> foo()
{'a': 1, 'c': 3, 'b': 2}
*>>> def fum(a, b, c):
...   print 'a',a
...   print 'b',b
...   print 'c',c
...
>>> fum(**foo())
a 1
b 2
c 3

        """
        return  {'startTime' : self.startTime, \
                'minPeriod' : self.minPeriod, \
                'maxPeriod' : self.maxPeriod, \
                'minPeak' : self.minPeak, \
                'maxPeak' : self.maxPeak, \
                'minPower' : self.minPower, \
                'maxPower' : self.maxPower, \
                'totPower' : self.totPower, \
                'duration' : self.lastTime - self.startTime + self.firstPeriod, \
                'numberOfCrests' : self.numberOfCrests, \
                'distance' : self.distance }


    def report(self):
        """generate a report on the accumulated wake information

        Args:
          None

        Returns:
          None

        Raises:
          None
        """
        if self.startTime == None:
            # print "No wakes to report"
            return
        # calculate distance based on duration
        firstWaveSpeed = 32/6.28 * self.firstPeriod
        lastWaveSpeed = 32/6.28 * self.lastPeriod
        duration = self.lastTime - self.startTime + self.firstPeriod
        # calculate distance based on dispersion (if possible)
        # t1 and r1 are time and speed of first wave of wake
        # t2 and r2 are time and speed of last wave of wake
        #    t2 and r2 should the first occurence of a different speed wake
        # distance = t1 * r1 = t2 * r2
        # time t2 = t1 + dur
        # t2/t1 = r1/r2
        # (t1+dur)/t1= r1/r2
        # dur/t1 = r1/r2 - 1
        # t1 = dur/(r1/r2 -1)
        # conditional to remove divide by zero
        if lastWaveSpeed > 0 and firstWaveSpeed != lastWaveSpeed:
            t1 = duration / (firstWaveSpeed/lastWaveSpeed - 1)
        else:
            t1 = duration
        # find possible crests
        theoreticalCrests = duration/ (self.lastPeriod + self.firstPeriod) /2
        # report wake attributes
        dtd = datetime.datetime.fromtimestamp( self.startTime)
        print "Individual wake report"
        print "    Time: start {:%H:%M:%S}.{:02d} duration {:.2f}s crests {:2d}/{:.1f}".format(
                dtd, dtd.microsecond/10000, duration, self.numberOfCrests,
                theoreticalCrests)
        print "    Period min {:.2f} max {:.2f} ave {:.2f}".format(
                self.minPeriod, self.maxPeriod, duration/self.numberOfCrests)
        print "    Peak min {:.2f} max {:.2f}".format(
                self.minPeak, self.maxPeak)
        print "    Power: min {:.2f} max {:.2f} total {:.2f}".format(
                self.minPower, self.maxPower, self.totPower)
        print "    Distance by duration {:.2f} by period {:.2f}".format(
                duration * (firstWaveSpeed - lastWaveSpeed) / 2,
                self.distance)
        print "    Distance {:.2f}".format( self.distance)


#### FUNCTIONS ####

def calculateDistance( period1, period2, timeDiff):
    """ calculate distance based on periods of two waves and a time diffence

    Args:
        period1: (s) period of the first wake
        period2: (s) period of the last wake
        timeDiff: (s) difference in time between the two wakes
    Return:
        distance suggested by the two periods

    Raises:
        None
    """
    if period1 <= period2:
        return 0
    else:
        constant = 32.174/2/3.1414 # g/2pi
        # distance = rate1 * time1 = rate2 * time2
        # rate = period * constant so dividing by the constant
        # period1 * time1 = period2 * time2
        # time2 = time1 + time difference
        # solving for time1:
        # period1 * time1 = period2 * (time1 + time difference)
        # time1 *(period1 - period2) = period2 * time difference
        # time1 = period2 * time difference /(period1 -period2) 
        time1 = period2 * timeDiff / (period1 - period2)
        distance = period1 * constant * time1
        print "calculateDistance", period1, period2, timeDiff, time1, distance
        return distance
    

def test():
    """tests the functions of this module

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    pass # not much of a test is it


if __name__ == "__main__":
    # execute only if run as a script
    test()
