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



#### NOTES ####

A resample object is a time series of samples used for FFT analysis. The
original sample is resampled at a rate determined by the desired frequency
for the FFT analysis. For this module the FFT performed on the resampled data
is only interested in a single FFT response.

A resamples object holds a collection of resample objects.

sample->resampling->sample series->FFT->response for particular freqency

'freshen' isn't quite the right word. It releases older list members.

"""



#### IMPORTS ####

import math                            # for pi, sqrt, ceil

import numpy as np                     # for FFT
from numpy import arange               # for FFT

from config import SAMPLES_PER_SECOND
from config import RESOLUTION
from config import MINIMUM_NUMBER_OF_CYCLES
from config import CLOSEST_METHOD
from config import INTERPOLATION_METHOD
from config import NORMALIZATION_METHOD
from config import GRAVITY_CONSTANT
#from config import TARGET_PERIODS
#from config import BOAT_LENGTHS
from config import BUFFER_SIZE 


#### CLASSES ####

class Resamples (object):
  """define an object containing a collection of Resample objects

  Methods:
    __init__: construct the resample object
    evaluate: add a new element to all time series
    freshen: drop older elements from all time series
  """


  def __init__ (self):
    """Resample the current measurement for all measurement buffers.

    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    self.resamples = []


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
    for resample in self.resamples:
      resample.evaluate( tick, value, lastTick, lastValue)


  def fft( self):
    """Do a fourier transforom on all samples

    Args:
    
    Returns:
      None
    
    Raises:
      None
    """
    for resample in self.resamples:
      resample.fft()


  def freshen( self):
    """Release unnecessary items from lists

    Args:
      None
  
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

  def __init__ (self, cyclePeriod, tick, value):
    """Initialize the resample data objects with configuration data.

    Args:
      cyclePeriod: (float) period of cycle in s for period of interest
      value: (float) current value for water level
    
    Returns:
      None
    
    Raises:
      Error if cyclePeriod is less than sampling rate/2
    """

    # save sampling characteristics based on cyclePeriod
    samplesPerCycle = math.floor( 2**(RESOLUTION + 1)) # +1 for Nyquest rate
    # make sure the resampling rate is less than sampling rate
    if cyclePeriod < 2. / SAMPLES_PER_SECOND:
      raise RuntimeError ("Cannot accomodate cyclePeriod")
    else:
      while (cyclePeriod / samplesPerCycle) < (1. / SAMPLES_PER_SECOND):
        samplesPerCycle = samplesPerCycle / 2 # sacrifice resolution
      self.cyclePeriod = cyclePeriod # s in target cycle
      self.resamplingPeriod = cyclePeriod / samplesPerCycle # s between samples
      self.samplesPerCycle = int( samplesPerCycle) # akin to resolution
      self.minimumSamples = int( samplesPerCycle * MINIMUM_NUMBER_OF_CYCLES)
      #self.frequencyOfInterest = 1. / cyclePeriod # used to check FFT FoI
      self.waveLength = cyclePeriod * math.sqrt( 2 * math.pi *
                                                 GRAVITY_CONSTANT)
      self.levels = []  # list of resampled levels
      # record the first sample and get ready for next sample
      self.levels.append( value)
      self.lastTime = tick # time of last resample
      self.resamplingDueTick = tick + self.resamplingPeriod # epoch in s
      self.response = None


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

    while tick > self.resamplingDueTick: # this should not loop, but in case
      self.levels.append( interpolate( self.resamplingDueTick, tick, value,
                                       lastTick, lastValue) )
      self.lastTime = self.resamplingDueTick # time of last resample
      self.resamplingDueTick = self.resamplingDueTick + self.resamplingPeriod


  def fft( self):
    """ find the frequence response for a collection of samples

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    #STATIC stuff for constructor?
    # build out the buffer with an integral number of samples
    numberOfCycles = BUFFER_SIZE / self.samplesPerCycle
    numberOfPartialCycles = int( numberOfCycles % MINIMUM_NUMBER_OF_CYCLES)
    numberOfFullCycles = int( numberOfCycles / MINIMUM_NUMBER_OF_CYCLES)

    if len( self.levels) >= MINIMUM_NUMBER_OF_CYCLES * self.samplesPerCycle:
      sampleBuffer = self.levels[
        -int (numberOfPartialCycles * self.samplesPerCycle):]
      if numberOfFullCycles > 0:
        for _ in range( 0, numberOfFullCycles):
          sampleBuffer = sampleBuffer + self.levels[
            -int( MINIMUM_NUMBER_OF_CYCLES * self.samplesPerCycle):]

      # transform sample into a response
      fft = np.fft.rfft( sampleBuffer)

      #frequencyOfInterestIndex = log2( numberOfCycles)
      frequencyOfInterestIndex = numberOfCycles
      self.response = abs(fft[ frequencyOfInterestIndex])


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


#### FUNCTIONS ####

def interpolate( desiredTick, currentTick, currentValue, lastTick, lastValue):
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



# pylint: disable=too-many-arguments
# pylint: disable=pointless-string-statement
'''
def initSampling( tick, value, boatLengths, targetPeriods, samples, specs):
  """Initialize the sampling for the FFT analysis of wakes and waves.

  Args:
    tick: (float) time of current sample in epoch seconds
    value: (float) value of current sample
    boatLengths: (list of int) length in feet of boats of interest for wakes
    targetPeriods: (list of float) periods in s of interest for waves
    samples: (global pointer) destination of samples collection
    specs: (global pointer) destination of the spectra collection
  
  Returns:
    None
  
  Raises:
    None
  """

  #create data structures
  samples = Resamples()
  #specs = Spectra()

  for boatLength in boatLengths:
    #was...waveSpeed = math.sqrt (GRAVITY_CONSTANT * boatLength / 2 /math.pi)
    #was cycl ePeriod = boatLength / waveSpeed # s
    #this all had the same effect... if just solving for waveSpeed it should be
    # boatLength/cyclePeriod
    cyclePeriod = math.sqrt (boatLength / GRAVITY_CONSTANT/ 2 /math.pi) # ft/s
    ##waveSpeed = GRAVITY_CONSTANT / 2 / math.pi * cyclePeriod
    #waveSpeed = boatLength / cyclePeriod

    # create resample object inside the resamples object
    samples.resamples.append(
      Resample( cyclePeriod, tick, value))

    # create spectrum object inside the spectra object
    #specs.spectra.append ( Spectrum( samples.resamples))


  for period in targetPeriods:
    # create resample object inside the resamples object
    ##samples.resamples.append( resamples.Resample( period, tick, value))

    # create spectrum object inside the spectra object
    #specs.spectra.append ( Spectrum( samples.resamples[-1]))

'''
# pylint: enable=pointless-string-statement
# pylint: enable=too-many-arguments



def log2( number):
  """return the base 2 log of the number

  This function assumes that the number is a single power of 2, i.e.,
  0, 1, 2, 4, 8, 16, 32.

  Args:
    time: (float) the current time as an epoch in seconds

  Returns:
    None

  Raises:
    None
  """

  if number == 1:
    logValue = 0
  elif number == 2:
    logValue = 1
  elif number == 4:
    logValue = 2
  elif number == 8:
    logValue = 3
  elif number == 16:
    logValue = 4
  elif number == 32:
    logValue = 5
  else:
    logValue = -1
  return logValue


def rfftfreq(n, d=1.0):
  """ Return the Discrete Fourier Transform sample frequencies
  (for usage with rfft, irfft).

  The returned float array `f` contains the frequency bin centers in cycles
  per unit of the sample spacing (with zero at the start). For instance, if
  the sample spacing is in seconds, then the frequency unit is cycles/second.

  Given a window length `n` and a sample spacing `d`::

  f = [0, 1, ..., n/2-1, n/2] / (d*n) if n is even
  f = [0, 1, ..., (n-1)/2-1, (n-1)/2] / (d*n) if n is odd

  Unlike `fftfreq` (but like `scipy.fftpack.rfftfreq`)
  
  Args:
    None
    n : (int) Window length.
    d : (scalar) optional Sample spacing (inverse of the sampling rate).
      Defaults to 1. The Nyquist frequency component is considered to be
      positive.
  
  Returns:
    f : ndarray Array of length ``n//2 + 1`` containing the sample frequencies.
  
  Raises:
    valueError: if n is not an integer

  Examples
  --------
  >>> signal = np.array([-2, 8, 6, 4, 1, 0, 3, 5, -3, 4], dtype=float)
  >>> fourier = np.fft.rfft(signal)
  >>> n = signal.size
  >>> sample_rate = 100
  >>> freq = np.fft.fftfreq(n, d=1./sample_rate)
  >>> freq
  array([ 0., 10., 20., 30., 40., -50., -40., -30., -20., -10.])
  >>> freq = np.fft.rfftfreq(n, d=1./sample_rate)
  >>> freq
  array([ 0., 10., 20., 30., 40., 50.])

  """
  #if not (isinstance( n, int) or isinstance( n, integer)):
  if not isinstance( n, int):
    raise ValueError ("n should be an integer")
  val = 1.0/(n*d)
  N = n//2 + 1
  results = arange(0, N, dtype=int)
  return results * val



#### MAIN FUNCTION ####

#if __name__ == "__main__":
    # execute only if run as a script
#    test()



################
