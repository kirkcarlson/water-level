# !/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
""" findwake: module for separating wakes from waves

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

import wake
import wakesummary
import wavesummary


#### CONSTANTS ####

WAVE_VARIANCE = .1  # Allowable wave variance for coherence
MINIMUM_WAKE_COUNT = 1  # minimum number of crests in a wake
MINIMUM_WAKE_PERIOD = 1.  # minimum wake period (s)

#### ENUMERATED TYPES ####

IDLE_STATE, \
CONSIDERING_STATE, \
WAKE_STATE = range( 3)

stateNames = [ \
"IDLE_STATE", \
"CONSIDERING_STATE", \
"WAKE_STATE" ]

WAVE_WAVE_TYPE, \
WAKE_WAVE_TYPE, \
COHERENT_WAKE_WAVE_TYPE = range (3)

waveTypeNames = [ \
"WAVE_WAVE_TYPE", \
"WAKE_WAVE_TYPE", \
"COHERENT_WAKE_WAVE_TYPE"]


#### CLASSES ####

class FindWake( object):
    """find wake clusters in amungst a set of waves

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
        self.state = IDLE_STATE
        self.wakeCount = 0
        self.wakeBeginPeriod = None
        self.wakeBeginPower = 0
        self.wakeBeginTick = 0
        self.lastConsideredWavePower = 0 #***OLD***
        self.waveSummary = wavesummary.Wavesummary( outChan, influxObj)  # store for wave information
        self.wake = wake.Wake( outChan, influxObj)  # store for individual wake information
        self.wakeSummary = wakesummary.WakeSummary( outChan, "Coherent", influxObj)  # wake summary info
        #self.wakeISum = wakesummary.WakeSummary( outChan, "Incoherent")  # wake summary info


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
                self.waveSummary.noiseThreshold,\
                self.waveSummary.avePower.average)

        if power > self.waveSummary.noiseThreshold and period >= MINIMUM_WAKE_PERIOD:
            if self.wakeBeginPeriod is None:
                return WAKE_WAVE_TYPE
            else:
                if closeEnough (period, self.wakeBeginPeriod, WAVE_VARIANCE *
                            self.wakeBeginPeriod):
                    return COHERENT_WAKE_WAVE_TYPE
                else:
                    return WAKE_WAVE_TYPE
        else:
            return WAVE_WAVE_TYPE



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
        print "  FindWake.update state:{:s} waveType:{:s}".format(\
                stateNames [self.state], \
                waveTypeNames [wType])
        if self.state is IDLE_STATE: # timer is not running
            if wType is WAVE_WAVE_TYPE:
                self.pendingWaveQueue.append(( tick, period, peak, power))
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.waveSummary.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeBeginPeriod = None
                self.state = IDLE_STATE
            elif wType is WAKE_WAVE_TYPE:
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.wakeBeginTick = tick
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = CONSIDERING_STATE
            else:
                # should not get here
                print "***error in cluster.update IDLE_STATE***"
                self.wakeBeginPeriod = None
                self.state = IDLE_STATE

        elif self.state is CONSIDERING_STATE: # timer is running
            if wType is WAVE_WAVE_TYPE: # maybe OK, wait and see
                # don't do this forever, timer is supposed to be running
                self.pendingWaveQueue.append(( tick, period, peak, power))
            elif wType is WAKE_WAVE_TYPE: # new incoherent wake
                self.unschedClusterEnd( self.taskID) # stop timer
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.waveSummary.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.wakeBeginTick = tick
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = CONSIDERING_STATE
            elif wType is COHERENT_WAKE_WAVE_TYPE: # continuing wake
                self.unschedClusterEnd( self.taskID) # stop timer
                self.waveCount = self.waveCount + 1
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                if self.waveCount > MINIMUM_WAKE_COUNT: # definitely a wake
                    # when is the self.wake reset kirk
                    for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                        self.wake.update( tick2, period2, peak2, power2)
                    self.pendingWaveQueue = []
                    self.state = WAKE_STATE
                else: # may be a wake
                    self.state = CONSIDERING_STATE
            else:
                # should not get here
                print "***error in cluster.update CONSIDERING_STATE***"
                self.wakeBeginPeriod = None
                self.state = IDLE_STATE

        elif self.state is WAKE_STATE: # timer is running
            if wType is WAVE_WAVE_TYPE: # maybe OK, wait and see
                self.pendingWaveQueue.append(( tick, period, peak, power))
            elif wType is WAKE_WAVE_TYPE: # new incoherent wake
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wake.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wake.close() # close the existing wake
                self.wakeSummary.update( **self.wake.getAttributes())
                self.wakeBeginPeriod = period
                self.wakeBeginPower = power
                self.waveCount = 0
                self.wake.reset() # start a new individual wake
                self.pendingWaveQueue.append(( tick, period, peak, power))
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = CONSIDERING_STATE
            elif wType is COHERENT_WAKE_WAVE_TYPE: # continuing wake
                self.unschedClusterEnd( self.taskID)
                for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
                    self.wake.update( tick2, period2, peak2, power2)
                self.pendingWaveQueue = []
                self.wakeEndPeriod = period
                self.wakeEndPower = power
                self.wakeEndTick = tick
                #self.taskID = self.schedClusterEnd( tick, config.CLUSTER_WINDOW)
                self.taskID = self.schedClusterEnd( tick, 2*period)
                self.state = WAKE_STATE
            else:
                # should not get here
                print "***error in cluster.update WAKE_STATE***"
                self.wakeBeginPeriod = None
                self.state = IDLE_STATE
        else:
            # should not get here
            print "***error in cluster.update state***"
            self.wakeBeginPeriod = None
            self.state = IDLE_STATE


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
        if self.state is WAKE_STATE:
            self.wake.close() # close the existing wake
            self.wakeSummary.update( **self.wake.getAttributes())
        # treat accumulated waves as waves
        for (tick2, period2, peak2, power2) in self.pendingWaveQueue:
            self.waveSummary.update( tick2, period2, peak2, power2)
        self.pendingWaveQueue = []
        self.wakeBeginPeriod = None
        self.state = IDLE_STATE


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


#### FUNCTIONS ####

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
    test = FindWake(clusterOutChan, None, None)

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
