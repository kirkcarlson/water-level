# !/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
""" cluster: module for divining waves and wakes

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

import average
import config
import influx
import mysched
import report


#### CONSTANTS ####

WAVE_VARIANCE = .1  # Allowable wave variance for coherence
POWER_DEGRADATION = .02  # amount to decrease dominant power per second
MINIMUM_WAKE_COUNT = 1  # minimum number of crests in a wake
MINIMUM_WAKE_PERIOD = 1.  # minimum wake period (s)

#### ENUMERATED TYPES ####

#idleState, \
#consideringState, \
#wakeUpState, \
#wakeDownState = range( 4)

#stateNames = [ \
#"idleState", \
#"consideringState", \
#"wakeUpState", \
#"wakeDownState" ]

idleState, \
consideringState, \
wakeState = range( 3)

stateNames = [ \
"idleState", \
"consideringState", \
"wakeState" ]

waveWaveType, \
wakeWaveType, \
coherentWakeWaveType = range (3)

waveTypeNames = [ \
"waveWaveType", \
"wakeWaveType", \
"coherentWakeWaveType"]

#waveWaveType, \
#wakeWaveType, \
#wakeEndWaveType, \
#wakePendingWaveType, \
#pendingWaveType = range (5)

#waveTypeNames = [ \
#"waveWaveType", \
#"wakeWaveType", \
#"wakeEndWaveType", \
#"wakePendingWaveType", \
#"pendingWaveType"]


#### CLASSES ####

def closeEnough (sample, target, variance):
    """ Returns True if sample is close enough to target

    Args:
        sample: (float) value being tested
        target: (float) target value
        variance: (float) absolute value allowed away from target
            for example 10% would use a variance of .1 * target
            for example a tolerance of +/10 would would use a variance of 10

    Return:
        True if sample close to target
        False otherwise

    Raises:
        None
    """
    if sample >= target - variance and target <= target + variance:
        return True
    else:
        return False

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
        print "calcDistance", period1, period2, timeDiff, time1, distance
        return distance
    
class Cluster( object):
    """Account wave and wake clusters in a series of waves

    Wakes are a cluster of waves that have a bit more power than the average
    wave and usually have a coherent wavelength. Waves that aren't wakes are
    classified as just waves.
    """

    def __init__(self, outChan, sched, influxObj):
        """initialize the attributes of the cluster

        Args:
          outChan: channel for output stream
          sched: mysched.Schedule object
          influxObj: influx.Influx object

        Returns:
          None

        Raises:
          None
        """
        self.outChan = outChan
        self.sched = sched
        self.taskID = None # task ID of scheduled task, if any
        self.ifx = influxObj
        self.pendingWaveQueue = []  # list of saved wave attribute in limbo
        self.state = idleState
        self.wakeCount = 0
        self.wakeBeginPeriod = None
        self.wakeBeginPower = 0
        self.wakeBeginTick = 0
        self.lastConsideredWavePower = 0 #***OLD***
        self.wave = Wave( outChan, influxObj)  # store for wave information
        self.wake = Wake( outChan, influxObj)  # store for individual wake information
        self.wakeSum = WakeSummary( outChan, "Coherent", influxObj)  # wake summary info
        #self.wakeISum = WakeSummary( outChan, "Incoherent")  # wake summary info


    def waveType( self, tick, period, peak, power):
        """determines whether wave is part of wake or not

        Args:
          tick: float (s) time of the end of the wave
          period: float (s) period of the wave
          peak: float (in) peak to peak height of the wave
          power: float (mW?) power of the wave

        Returns:
          waveType as a enumerated integer

        Raises:
          None
        """
        dtd = datetime.datetime.fromtimestamp(tick)
        print "{:%y/%m/%d %H:%M:%S}.{:02d} waveType".format( dtd, dtd.microsecond/10000),
        print "per:{:.2f} pk:{:.2f} pow:{:.2f} {:s}".format(\
                period, \
                peak, \
                power, \
                stateNames[self.state])
        print "  noise:{:.2f} ave:{:.2f}".format(\
                self.wave.noiseThreshold,\
                self.wave.avePower.average)

        if power > self.wave.noiseThreshold and period >= MINIMUM_WAKE_PERIOD:
            if self.wakeBeginPeriod is None:
                return wakeWaveType
            else:
                if closeEnough (period, self.wakeBeginPeriod, WAVE_VARIANCE *
                            self.wakeBeginPeriod):
                    return coherentWakeWaveType
                else:
                    return wakeWaveType
        else:
            return waveWaveType



    def update( self, tick, period, peak, power):
        """update wave or wake stats based on its type appropriate

        if the pendingWaveQueue is not empty or wakeSummary is in progress,
        a timer is set to clean that up.

        Args:
          tick: float (s) time of the end of the wave
          period: float (s) period of the wave
          peak: float (in) peak to peak height of the wave
          power: float (mW?) power of the wave

        Returns:
          None

        Raises:
          None
        """

        wType = self.waveType( tick, period, peak, power)
        print "  Cluster.update state:{:s} waveType:{:s}".format(\
                stateNames [self.state], \
                waveTypeNames [wType])
        if self.state is idleState: # timer is not running
            if wType is waveWaveType:
                self.pendingWaveQueue.append(( tick, period, peak, power))
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wave.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeBeginPeriod = None
                self.state = idleState
            elif wType is wakeWaveType:
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.wakeBeginTick = tick
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = consideringState
            else:
                # should not get here
                print "***error in cluster.update idleState***"
                self.wakeBeginPeriod = None
                self.state = idleState

        elif self.state is consideringState: # timer is running
            if wType is waveWaveType: # maybe OK, wait and see
                # don't do this forever, timer is supposed to be running
                self.pendingWaveQueue.append(( tick, period, peak, power))
            elif wType is wakeWaveType: # new incoherent wake
                self.unschedClusterEnd( self.taskID) # stop timer
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wave.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.wakeBeginTick = tick
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = consideringState
            elif wType is coherentWakeWaveType: # continuing wake
                self.unschedClusterEnd( self.taskID) # stop timer
                self.waveCount = self.waveCount + 1
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                if self.waveCount > MINIMUM_WAKE_COUNT: # definitely a wake
                    # when is the self.wake reset kirk
                    for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                        self.wake.update( tick2, period2, peak2, power2)
                    self.pendingWaveQueue = []
                    self.state = wakeState
                else: # may be a wake
                    self.state = consideringState
            else:
                # should not get here
                print "***error in cluster.update consideringState***"
                self.wakeBeginPeriod = None
                self.state = idleState

        elif self.state is wakeState: # timer is running
            if wType is waveWaveType: # maybe OK, wait and see
                self.pendingWaveQueue.append(( tick, period, peak, power))
            elif wType is wakeWaveType: # new incoherent wake
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wake.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wake.close() # close the existing wake
                self.wakeSum.update( **self.wake.getAttributes())
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = consideringState
            elif wType is coherentWakeWaveType: # continuing wake
                self.unschedClusterEnd( self.taskID)
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wake.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeEndPeriod = period
                self.wakeEndPower = power
                self.wakeEndTick = tick
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = wakeState
            else:
                # should not get here
                print "***error in cluster.update wakeState***"
                self.wakeBeginPeriod = None
                self.state = idleState
        else:
            # should not get here
            print "***error in cluster.update state***"
            self.wakeBeginPeriod = None
            self.state = idleState


    def cleanup( self, tick):
        """clean up cluster state machine... called by timed routine
        Args:
          None

        Returns:
          None


        Raises:
          None
        """
        # print "cluster.cleanup"
        if self.state is wakeState:
            self.wake.close() # close the existing wake
            self.wakeSum.update( **self.wake.getAttributes())
        # treat accumulated waves as waves
        for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
            self.wave.update( tick2, period2, peak2, power2)
        self.pendingWaveQueue = []
        self.wakeBeginPeriod = None
        self.state = idleState


    def schedClusterEnd( self, currentTime, period):
        """schedule the end of a cluster function
    
        Args:
            None
    
        Returns:
            processID from mysched.schedule()
    
        Raises:
            None
        """
        # print "---schedClusterEnd", currentTime, period
        return self.sched.schedule( self.cleanup,
                                    currentTime,
                                    0,
                                    period)


    def unschedClusterEnd( self, taskID):
        """unschedule the end of a cluster function
    
        Args:
            None
    
        Returns:
            None
    
        Raises:
            None
        """
        # print "---unschedClusterEnd"
        self.sched.unschedule( taskID)


class Wave(object):
    """Keep track of wave attributes."""

    def __init__(self, outChan, influxObj):
        """initialize the attributes of a wave

        Args:
          outChan: channel for output stream
          influxObj: influx.Influx object

        Returns:
          None

        Raises:
          None
        """
        self.outChan = outChan
        self.ifx = influxObj
        self.startTick = 0
        self.noiseThreshold = 1. # temp for now 0.
        self.noiseThresholdTick = None
        self.maxPeriod = 0
        self.maxPeak = 0
        self.maxPower = 0
        self.minPeriod = None
        self.minPeak = None
        self.minPower = None
        self.avePeriod = average.Average("Wave Period Average", "nW?", 50)
        self.avePeak = average.Average("Wave Period Average", "nW?", 50)
        self.avePower = average.Average("Wave Power Average", "nW?", 50)
        self.avePower.update( 1) # same as 1" x 1s wave temp for now
        self.totPower = 0


    def reset( self, tick):
        """reset the accumulated wave statistics to begin anew

        Args:
          tick: float (s) epoch of the start of sampling period

        Returns:
          None

        Raises:
          None
        """
        self.startTick = tick
        self.noiseThreshold = 1.
        self.noiseThresholdTick = None
        self.maxPeriod = 0
        self.maxPeak = 0
        self.maxPower = 0
        self.minPeriod = None
        self.minPeak = None
        self.minPower = None
        self.avePeriod.reset()
        self.avePeak.reset()
        self.avePower.reset()
        self.avePower.update( 1) # same as 1" x 1s wave temp for now
        self.totPower = 0


    def update( self, tick, period, peak, power):
        """update the accumated wave statistics with this wave

        Args:
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
        print "  wave.update {:%H:%M:%S}.{:02d} per:{:.2f} pk:{:.2f} pow:{:.2f}".format(\
                dtd, dtd.microsecond/10000, period, peak, power)
        
        if self.noiseThresholdTick is None:
            heldPower = self.noiseThreshold
        else:
            heldPower = self.noiseThreshold * (
                    1 - (POWER_DEGRADATION * (tick - self.noiseThresholdTick)))
            # print "  noise in:{:.3f} PD:{:.2f} tick:{:.1f} nTTick:{:.1f} heldP:{:.3f}".format(\
            #         self.noiseThreshold, \
            #         POWER_DEGRADATION, \
            #         tick, \
            #         self.noiseThresholdTick, \
            #         heldPower)
        if power > heldPower:
            self.noiseThreshold = power
        else:
            self.noiseThreshold = heldPower
        self.noiseThresholdTick = tick

        if period > self.maxPeriod:
            self.maxPeriod = period
        if self.minPeriod is None or period < self.minPeriod:
            self.minPeriod = period
        if peak > self.maxPeak:
            self.maxPeak = peak
        if self.minPeak is None or peak < self.minPeak:
            self.minPeak = peak
        if power > self.maxPower:
            self.maxPower = power
        if self.minPower is None or power < self.minPower:
            self.minPower = power
        self.avePeriod.update( period)
        self.avePeak.update( peak)
        self.avePower.update( power)
        self.totPower = self.totPower + power

        self.ifx.sendPoint( tick, "cluster", "wavePeriod", period)
        self.ifx.sendPoint( tick, "cluster", "wavePeak", peak)
        self.ifx.sendPoint( tick, "cluster", "wavePower", power)
        self.ifx.sendPoint( tick, "cluster", "wavePowerAve", self.avePower.average)
        self.ifx.sendPoint( tick, "cluster", "wavePowerNoise", self.noiseThreshold)


    def report( self):
        """generate report of collected wave statistics

        Args:
          None

        Returns:
          None

        Raises:
          None
        """
        print "wave.report"
        if self.minPeriod is None:
            print "   no wave report at this time"
            return
        print "    Period: min {:.2f} max {:.2f} ave {:.2f}".format (
                self.minPeriod, self.maxPeriod, self.avePeriod.average)
        print "    Peak:   min {:.2f} max {:.2f} ave {:.2f}".format (
                self.minPeak, self.maxPeak, self.avePeak.average)
        print "    Power:  min {:.2f} max {:.2f} ave {:.2f}".format (
                self.minPower, self.maxPower, self.avePower.average)
        print "    Power:  noise {:.2f}".format ( self.noiseThreshold)
        print "    Power:  total {:.2f}".format ( self.totPower)


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
        self.coherent = True # assume it is coherent unless it is not


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
        self.coherent = True # assume it is coherent unless it is not


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
        lastPeriod = self.lastPeriod
        if not self.wakeIsCoherent( period): # changes self.lastPeriod
            # print "Changing wake to incoherent", period, lastPeriod
            self.coherent = False


    def close( self):
        """close the attributes of a wake with internal calculations

        Args:
          self: the wake object

        Returns:
          None

        Raises:
          None
        """
        pass # do what you gotta do
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


    def wakeIsCoherent( self, period):
        """determine if the proposed wave is coherent with rest of the wake

        Args:
          self: the wake object
          period: float (s) period of the wave

        Returns:
          None

        Raises:
          None
        """
        if self.lastPeriod > 0:
            factor = period/self.lastPeriod
        else:
            factor = 1
        # print "wakeIsCoherent", period, self.lastPeriod, factor,  (1. - WAVE_VARIANCE), (1. + WAVE_VARIANCE)
        self.lastPeriod = period
        if factor >= (1. - WAVE_VARIANCE) and factor <= (1. + WAVE_VARIANCE):
            return True
        else:
            return False


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
            'coherent' : coherent is the cluster coherent

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
                'distance' : self.distance, \
                'coherent' : self.coherent}


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
        if self.coherent:
            print "    wake was coherent"
        else:
            print "    wake was incoherent"


class WakeSummary(object):
    """Keep track of a bunch of wake clusters over time."""

    def __init__( self, outChan, name, influxObj):
        """initialize the attributes of a wake summary

        Args:
          outChan: channel for output stream
          name: name of the wake summary
          influxObj: influx.Influx object


        Returns:
          None

        Raises:
          None
        """
        self.outChan = outChan
        self.name = name
        self.ifx = influxObj
        self.maxPeriod = 0
        self.minPeriod = None
        self.maxPeak = 0
        self.minPeak = None
        self.maxPower = 0
        self.minPower = None
        self.maxCrests = 0

        self.totPower = 0
        self.totDuration = 0
        self.startTime = None
        self.numberOfWakes = 0

        self.maxDistance = 0

    def reset( self, tick):
        self.startTime = tick
        self.numberOfWakes = 0
        self.totDuration = 0
        self.totPower = 0

        self.maxPeriod = 0
        self.minPeriod = None
        self.maxPeak = 0
        self.minPeak = None
        self.maxPower = 0
        self.minPower = None
        self.maxCrests = 0

    def update( self, startTime, minPeriod, maxPeriod, minPeak, maxPeak, minPower,
            maxPower, totPower, duration, numberOfCrests, distance, coherent):
        """ update the wake summary with a new wake

        Args:
            'startTime' : startTime float (s) start time of the wake cluster
            'minPeriod' : minPeriod minimum period of the wake cluster
            'maxPeriod' : maxPeriod maximum period of the wake cluster
            'minPeak' : minPeak minimum peak of the wake cluster
            'maxPeak' : maxPeak maximum peak of the wake cluster
            'minPower' : minPower minimum power of the wake cluster
            'maxPower' : maxPower maximum power of the wake cluster
            'totPower' : totPower total power of the wake cluster
            'duration' : duration duration of the wake wake cluster
            'numberOfCrests' : numberOfCrests number of crests in the wake cluster
            'distance' : distance to source of waves in feet
            'coherent' : coherent is the cluster coherent
        """

        dtd = datetime.datetime.fromtimestamp( startTime)
        coh = "coherent"
        if not coherent:
          coh = "incoherent"
        print "  wakeSummary.update {:%H:%M:%S}.{:02d}".format( dtd, dtd.microsecond/10000),
        print "  per:{:.2f} pk:{:.2f} pow:{:.2f} tot:{:.2f} dur:{:.2f} cre:{:.2f} coh:{:s}".format(\
                maxPeriod, maxPeak, maxPower, \
                totPower, duration, numberOfCrests, coh)
        self.numberOfWakes = self.numberOfWakes + 1
        self.totDuration = self.totDuration + duration
        self.totPower = self.totPower + totPower

        if maxPeriod > self.maxPeriod:
            self.maxPeriod = maxPeriod
        if self.minPeriod == None or minPeriod < self.minPeriod:
            self.minPeriod = minPeriod
        if maxPeak > self.maxPeak:
            self.maxPeak = maxPeak
        if self.minPeak == None or minPeak < self.minPeak:
            self.minPeak = minPeak
        if maxPower > self.maxPower:
            self.maxPower = maxPower
        if self.minPower == None or minPower < self.minPower:
            self.minPower = minPower
        if numberOfCrests > self.maxCrests:
            self.maxCrests = numberOfCrests
        if distance > self.maxDistance:
            self.maxDistance = distance

        self.ifx.sendPoint( startTime, "cluster", "wakeMinPeriod", minPeriod)
        self.ifx.sendPoint( startTime, "cluster", "wakeMaxPeriod", maxPeriod)
        self.ifx.sendPoint( startTime, "cluster", "wakeMinPeak", minPeak)
        self.ifx.sendPoint( startTime, "cluster", "wakeMaxPeak", maxPeak)
        self.ifx.sendPoint( startTime, "cluster", "wakeMinPower", minPower)
        self.ifx.sendPoint( startTime, "cluster", "wakeMaxPower", maxPower)
        self.ifx.sendPoint( startTime, "cluster", "wakeTotPower", totPower)
        self.ifx.sendPoint( startTime, "cluster", "wakeDuration", duration)
        self.ifx.sendPoint( startTime, "cluster", "wakeNumCrests", numberOfCrests)


    def report(self):
        """generate a report on the collection of wakes

        Args:
          None

        Returns:
          None

        Raises:
          None
        """
        if self.startTime == None or self.numberOfWakes is 0:
            print "No wake summary for " + self.name
            return
        dtd = datetime.datetime.fromtimestamp( self.startTime)
        print self.name + " wake group report"
        print "  Time: start {:%H:%M:%S}.{:02d} duration {:.2f}s wakes {:d}".format(
                dtd, dtd.microsecond/10000, self.totDuration, self.numberOfWakes)
        if self.minPeriod == None:
            min = 0
        else:
            min = self.minPeriod
        print "    Period min {:.2f} max {:.2f}".format(
                min, self.maxPeriod)
        if self.minPeak == None:
            min = 0
        else:
            min = self.minPeak
        print "    Peak min {:.2f} max {:.2f}".format(
                min, self.maxPeak)
        if self.minPower == None:
            min = 0
        else:
            min = self.minPower
        print "    Power: min {:.2f} max {:.2f} total {:.2f}".format(
                min, self.maxPower, self.totPower)
        print "    Power: ave {:.2f}".format( self.totPower/self.numberOfWakes)
        print "    Crests: max {:d}".format( self.maxCrests)




#### FUNCTIONS ####

# pylint: disable=pointless-string-statement
'''c
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


def test():
    """tests the functions of this module

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    clusterOutChan = report.ReportChannel("")
    test = Cluster(clusterOutChan)

    ### VARIABLES AND TEST DATA ###
    # data is time, period, peak, power tuples
    data = [(1., 1., .5, .5),
            (2., 1., .7, .7),
            (3., 1., .5, .5),
            (4., 1., .7, .7),
            (5., 1., .5, .5),
            (6., 2.1, 10.2, 21.42),
            (8.1, 2.0, 11.5, 23),
            (10.1, 1.4, 5.5, 7.7 ),
            (11.5, 1.4, 3.5, 4.9 ),
            (12.9, 1., .5, .5),
            (13.9, 1., .5, .5),
            (14.9, 1.1, .5, .5),
            (16, 1.2, .6, .75),
            (17.2, 1.2, .8, .96),
            (18.4, 1.2, 1.00, 1.2),
            (19.6, 1.2, .8, .96),
            (20.8, 1.2, .6, .72),
            (22, 1.1, .5, .5),
            (23, 1., .7, .7),
            (24, 1., .5, .5),
            (25, 1., .7, .7),
            ]

    ### CODE ###

    test.wakeCSum.reset(0.01)
    test.wakeISum.reset(0.01)
    for wave in data:
        print "\ntest", wave
        test.update(wave[0], wave[1], wave[2], wave[3])
    test.wave.report()
    test.wakeCSum.report()
    test.wakeISum.report()


if __name__ == "__main__":
    # execute only if run as a script
    test()
