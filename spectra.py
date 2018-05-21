#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
spectra -- module for handling wave and wake spectra

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

import math                            # for FFT
import datetime                        # for time stamp during test
import time                            # for time stamp during test

import numpy as np                     # for FFT
from numpy import arange               # for FFT
#import scipy.fftpack                   # for FFT

import resamples                       # resampled values

from config import GRAVITY_CONSTANT
from config import TARGET_PERIODS
from config import BOAT_LENGTHS
from config import MINIMUM_NUMBER_OF_CYCLES
from config import BUFFER_SIZE 



#### CLASSES ####

class Spectra( object):
  """ class of list of individual frequency response time series
  """

  def __init__( self):
    """construct the spectral group structures

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    self.times = []
    self.spectra = []
       

  def evaluate( self, currentTime):
    """evaluate all of the individual frequency responses in the spectra

    Args:
      currentTime: (float) the current time as an epoch in seconds

    Returns:
      None

    Raises:
      None
    """

    # save the evaluation time and evaluate all frequencies
    self.times.append( currentTime)
    for spectrum in self.spectra:
      spectrum.evaluate()


  def freshen( self, responsesToKeep):
    """clean out old spectra data

    Args:
      responsesToKeep: (int) number of responses to keep

    Returns:
      None

    Raises:
      None
    """

    # freshen the responses of all frequencies
    for spectrum in self.spectra:
      spectrum.freshen( responsesToKeep)


class Spectrum( object):
  """ class of an individual frequency response time series
  """

  def __init__( self, sample):
    """construct the structures for an individual spectrum time series

    Args:
      sample: pointer to sample time series object

    Returns:
      None

    Raises:
      None
    """

    self.responses = []
    self.sample = sample
    #consider moving STATIC things from evaluate method to here

  def evaluate( self):
    """ find an individual instantaneous frequence response

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    #STATIC stuff for constructor?
    # build out the buffer with an integral number of samples
    numberOfCycles = BUFFER_SIZE / self.sample.samplesPerCycle
    numberOfPartialCycles = int( numberOfCycles % MINIMUM_NUMBER_OF_CYCLES)
    numberOfFullCycles = int( numberOfCycles / MINIMUM_NUMBER_OF_CYCLES)

    #print "source size", len( self.sample.levels)
    #print "BUFFER_SIZE", BUFFER_SIZE
    #print "samplesPerCycle", self.sample.samplesPerCycle
    #print "numberOfCycles", numberOfCycles
    #print "numberOfFullCycles", numberOfFullCycles
    #print "numberOfPartialCycles", numberOfPartialCycles

    #print "number of samples", len( self.sample.levels)
    if len( self.sample.levels) < \
        MINIMUM_NUMBER_OF_CYCLES * self.sample.samplesPerCycle:
      #print  "Not enough samples"
      pass
    else:
      sampleBuffer = self.sample.levels[
          -int (numberOfPartialCycles * self.sample.samplesPerCycle):]
      #print "size of sampleBuffer after first append ", len( sampleBuffer)
      if numberOfFullCycles > 0:
        for _ in range( 0, numberOfFullCycles):
          sampleBuffer = sampleBuffer + self.sample.levels[
              -int( MINIMUM_NUMBER_OF_CYCLES * self.sample.samplesPerCycle):]
          #print "size of sampleBuffer after subsequent append ",
          #    len( sampleBuffer)
      #print "size of sampleBuffer after appends ", len( sampleBuffer)

      # transform sample into a response
      fft = np.fft.rfft( sampleBuffer)

      # append response to time series
      #print "FFT", fft
      #frequencyOfInterestIndex = log2( numberOfCycles)
      frequencyOfInterestIndex = numberOfCycles

      #STATIC stuff for constructor?
      #print "FFT foII", self.sample.cyclePeriod, numberOfCycles,
      #    frequencyOfInterestIndex, fft[frequencyOfInterestIndex],
      #    abs(fft[frequencyOfInterestIndex])
      #freqs = rfftfreq( BUFFER_SIZE, self.sample.resamplingPeriod)
      #if self.sample.frequencyOfInterst != freqs[frequencyOfInterestIndex]:
      #  print "Selecting the wrong frequency
      #print "freqs:",freqs
      #print "Frequency of Interest:", self.sample.frequencyOfInterest,
      #   freqs[frequencyOfInterestIndex]


      self.responses.append( abs(fft[ frequencyOfInterestIndex]))
      # time is stored in the spectra parent


  def freshen( self, responsesToKeep):
    """clean out old spectra data

    Args:
      responsesToKeep: (int) number of responses to keep

    Returns:
      None

    Raises:
      None
    """

    if len( self.responses) > responsesToKeep:
      self.responses = self.responses[ -responsesToKeep:]


#### GLOBALS ####

testResamples = None
testSpectra = None



#### FUNCTIONS ####

# pylint: disable=too-many-arguments
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
  samples = resamples.Resamples()
  specs = Spectra()

  for boatLength in boatLengths:
    #was...waveSpeed = math.sqrt (GRAVITY_CONSTANT * boatLength / 2 /math.pi)
    #was cyclePeriod = boatLength / waveSpeed # s
    #this all had the same effect... if just solving for waveSpeed it should be
    # boatLength/cyclePeriod
    cyclePeriod = math.sqrt (boatLength / GRAVITY_CONSTANT/ 2 /math.pi) # ft/s
    ##waveSpeed = GRAVITY_CONSTANT / 2 / math.pi * cyclePeriod
    waveSpeed = boatLength / cyclePeriod
    legend = "{0}' boat has period {1} and speed {3} ".format(
        boatLength, cyclePeriod, waveSpeed)

    # create resample object inside the resamples object
    samples.resamples.append(
        resamples.Resample( cyclePeriod, tick, value, legend))

    # create spectrum object inside the spectra object
    specs.spectra.append ( Spectrum( samples.resamples))


  for period in targetPeriods:
    legend = "{}s period".format( period)

    # create resample object inside the resamples object
    samples.resamples.append( resamples.Resample( period, tick, value, legend))

    # create spectrum object inside the spectra object
    specs.spectra.append ( Spectrum( samples.resamples[-1]))

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
    raise ValueError("n should be an integer")
  val = 1.0/(n*d)
  N = n//2 + 1
  results = arange(0, N, dtype=int)
  return results * val



#### MAIN FUNCTION ####

# pylint: disable=too-many-locals
def test ():
  """test the creation and evaluation of frequency responses

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  # configuration
  period = 2.5 # seconds
  waveHeight = 1 # inch
  samplesPerSecond = 30
  #numberOfSeconds = 10
  tick = 0 # starting value
  #value = 0 # starting value

  # initialize resample buffers
  initSampling( 0, 0, BOAT_LENGTHS, TARGET_PERIODS, testResamples, testSpectra)
  #print "Init resample len", len(  testResamples.resamples)

  # generate and resample square wave of the given period
  numberOfPulses = 10
  numberOfPeriodsPerPulse = 4
  samplesPerPeriod = int(period * samplesPerSecond) # round off here not good
  samplePeriod = 1. / samplesPerSecond
  #totalNumberOfPeriods = int( math.ceil( numberOfSeconds / period))
  sampleNumber = 0 # counter for doing the FFT thing
  FFT_TIME = samplesPerSecond # one a second after enough samples collected...
  spectrumTime = time.time()

  for iPulse in range (0, 2 * numberOfPulses): # do a number of pulses
    for _ in range (0, numberOfPeriodsPerPulse): # do a number of periods
      for iSample in range (0, samplesPerPeriod): # samples for one period
        # do FFTs on all resamples once every second
        if sampleNumber % FFT_TIME == 0:
          print "FFT time", tick, sampleNumber
          testSpectra.evaluate (spectrumTime + (sampleNumber / FFT_TIME))
        sampleNumber = sampleNumber + 1
        # resample across all resample streams
        print "resample number", sampleNumber
#        for resample in testResamples.resamples:
        lastTick = tick
        lastHeight = -waveHeight/2
        tick = tick + samplePeriod
        # i / blastTime % 2: 0 square wave, 1 quiet=zero
            
        if iPulse % 2:
          if iSample < samplesPerPeriod/2:
            height = -waveHeight/2
          else:
            height = waveHeight/2
        else:
          height = 0
        testResamples.evaluate( tick, height, lastTick, lastHeight)
      #print "End of iSample", iSample, iPeriod, iPulse, sampleNumber
    #print "End of iPeriod", iSample, iPeriod, iPulse, sampleNumber
  #print "End of iPulse", iSample, iPeriod, iPulse, sampleNumber
  # pylint: enable=too-many-locals


if __name__ == "__main__":
  # execute only if run as a script
  test()
