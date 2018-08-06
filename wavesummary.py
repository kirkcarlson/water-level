# !/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
""" wavesummary -- module summarizing wave attributes over a period of time

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
import influx


#### CONSTANTS ####

POWER_DEGRADATION = .02  # amount to decrease dominant power per second


#### ENUMERATED TYPES ####


#### CLASSES ####

class Wavesummary(object):
    """Keep track of wave attributes over time."""

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


#### FUNCTIONS ####


def test():
    """tests the functions of this module

    Args:
      None

    Returns:
      None

    Raises:
      None
    """
    pass # not much of a test


if __name__ == "__main__":
    # execute only if run as a script
    test()
