#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
resamples -- resamples input data for more selective frequency analysis

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

import math                            # for pi, sqrt, ceil
 
from config import SAMPLES_PER_SECOND
from config import RESOLUTION
from config import MINIMUM_NUMBER_OF_CYCLES
from config import CLOSEST_METHOD
from config import INTERPOLATION_METHOD
from config import NORMALIZATION_METHOD


#Notes

#There is a one to one relationship between a sample object and a spectrum
#object. The group of samples is maintained to feed the new samples as they
#arrive. The group of spectra is maintained for analyzing, reporting, plotting
#and monitoring.

#So when a period is to be added, it is added as sample to samples and a
#spectrum to spectra with a link from sample to spectrum. One path is created
#in its entirety.

#'freshen' isn't quite the right word. It is releasing older list members


#### CLASSES ####

class Resamples (object):
  """define an object containing a list of time series of resampled data

  Methods:
    __init__: construct the resample object
    evaluate: add a new element to all time series
    freshen: drop older elements from all time series
  """


  def __init__ (self):
    """Resample the current measurement for all measurement buffers.

    Args:
      tick: (float) current time as epoch
      sample: (float) current wave height in inches
      lastTick: (float) last time as epoch
      lastSample: (float) last wave height in inches
    
    Returns:
      None
    
    Raises:
      None
    """
    self.resamples = []
    #for config in configs: # actually this may be two loops:
    #  one for boat lengths and one for more general periods
    #  resamples.append( Resample( config, tick, value))


  def evaluate( self, tick, value, lastTick, lastValue ):
    """Resample the current measurement for all measurement buffers.

    Args:
      tick: (float) current time as epoch
      value: (float) current wave height in inches
      lastTick: (float) last time as epoch
      lastValue: (float) last wave height in inches
    
    Returns:
      None
    
    Raises:
      None
    """
    #print "samples: ", varString( samples)
    #print "resampling", len(self.resamples)
    for resample in self.resamples:
      #print "sample: ", varString( sample)
      resample.evaluate( tick, value, lastTick, lastValue)


  def freshen( self):
    """Release unnecessary items from lists

    Args:
  
    Returns:
      None
    
    Raises:
      None
    """

    for resample in self.resamples:
      resample.freshen ()



# pylint: disable=too-many-instance-attributes
class Resample (object):
  """define a resample object containing a single time series of resampled data

  Methods:
    __init__: construct the resample object
    evaluate: add a new element to a time series
    freshen: drop older elements from a time series
  """

  def __init__ (self, cyclePeriod, tick, value, legend):
    """Initialize the resample data objects with configuration data.

    Args:
      cyclePeriod: (float) period of cycle in s for period of interest
      tick: (float) current tick in s
      value: (float) current value for water level
    
    Returns:
      None
    
    Raises:
      None
    """

    # save sampling characteristics based on cyclePeriod
    samplesPerCycle = math.floor( 2**(RESOLUTION + 1)) # +1 for Nyquest rate
    # make sure the resampling rate is less than sampling rate
    if cyclePeriod < 1. / SAMPLES_PER_SECOND:
      print "Cannot accodate cyclePeriod =", cyclePeriod
      # this should raise an error
    else:
      #print "check", cyclePeriod, samplesPerCycle, SAMPLES_PER_SECOND, \
      #    (cyclePeriod / samplesPerCycle), (1. / SAMPLES_PER_SECOND)
      while (cyclePeriod / samplesPerCycle) < (1. / SAMPLES_PER_SECOND):
        samplesPerCycle = samplesPerCycle / 2 # sacrifice resolution
      self.cyclePeriod = cyclePeriod # s in target cycle
      self.resamplingPeriod = cyclePeriod / samplesPerCycle # s between samples
      self.samplesPerCycle = int( samplesPerCycle) # akin to resolution
      self.minimumSamples = int( samplesPerCycle * MINIMUM_NUMBER_OF_CYCLES)
      self.frequencyOfInterest = 1. / cyclePeriod #...WHAT IS THIS USED FOR??
      self.levels = []  # history of wave heights

      # record the first sample and get ready for next sample
      self.levels.append( value)
      self.lastTime = tick # time of last resample
      self.resamplingDueTick = tick + self.resamplingPeriod # epoch in s
      self.legend = legend # legend for graphs
    #print "legend:", self.legend
    #print "cyclePeriod:", self.cyclePeriod
    #print "resamplingPeriod:                ", self.resamplingPeriod
    #print "frequencyOfInterest:", self.frequencyOfInterest
    #print "samplesPerCycle:", self.samplesPerCycle
    #print "minimumSamples:", self.minimumSamples


  def evaluate( self, tick, value, lastTick, lastValue ):
    """Resamples the current measurement for a particular resampled stream.

    Args:
      tick: (float) current time as epoch
      value: (float) current wave height in inches
      lastTick: (float) last time as epoch
      lastValue: (float) last wave height in inches
  
    Returns:
      None
    
    Raises:
      None
    """

    #print "resample", self.resamplingPeriod, value, len( self.levels)
    while tick > self.resamplingDueTick: # this should not loop, but in case
      #print "resample adding:", interpolate (self.resamplingDueTick, tick, \
      #    value, lastTick, lastValue), self.resamplingDueTick, tick, value, \
      #    lastTick, lastValue
      self.levels.append( interpolate (self.resamplingDueTick, tick, value,
                                       lastTick, lastValue) )
      self.lastTime = self.resamplingDueTick # time of last resample
      self.resamplingDueTick = self.resamplingDueTick + self.resamplingPeriod
    #print "Len resample", self.resamplingPeriod, len(self.levels)


  def freshen( self):
    """Freshen the resampled data by deleting older data.

    Args:
      None
  
    Returns:
      None
    
    Raises:
      None
    """

    if len( self.levels) > self.minimumSamples:
      self.levels = self.levels [-self.minimumSamples:]

# pylint: enable=too-many-instance-attributes


#### GLOBALS


#### FUNCTIONS ####

def interpolate(desiredTick, currentTick, currentValue, lastTick, lastValue):
  """Determines a sampled value between two measurements

  This uses desiredTick to get the proportion of time between the last and
  current measurements and uses that to get the same proportion of value
  between the last and current value.
 
  Args:
    desiredTick : (float) epoch time in s of the desired value
    currentTick : (float) epoch time in s of the current value measurement
    currentValue : (float) current value
    lastTick : (float) epoch time in s of the last value measurement
    lastValue : (float) last value
  
  Returns:
    interpolatedValue : (float) interpolated value
  
  Raises:
    None
  """
  if currentTick > lastTick:
    timeRatio = (desiredTick - lastTick) / (currentTick - lastTick)
  else:
    timeRatio = 1
  if NORMALIZATION_METHOD == CLOSEST_METHOD:
    if timeRatio < .5:
      interpolatedValue = lastValue
    else:
      interpolatedValue = currentValue

  elif NORMALIZATION_METHOD == INTERPOLATION_METHOD:
    interpolatedValue = lastValue + timeRatio * (currentValue - lastValue)
  return interpolatedValue


#### MAIN FUNCTION ####

#if __name__ == "__main__":
    # execute only if run as a script
#    test()
