#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
findwave - module for finding a wave with zero crossing analysis

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

import math

#from config import POWER_CONSTANT 



#### CLASSES ####

class FindWave (object):
  """Find a wave by doing zero crossing analysis. """ 
  # pylint: disable=too-few-public-methods

  # pylint: disable=too-many-instance-attributes
  def __init__ (self):
    self.levelTrend = 0

    self.waveHeight = 0 # instantaneous height
    self._firstTime = True
    self._lastPositiveTrend = True
    self._positivePeak = 0
    self._negativePeak = 0
    self._positivePeriod = 0
    self._negativePeriod = 0
    self._zeroCrossingTick = 0
    self.waveTick = 0
    self.wavePeakToPeak = 0
    self.wavePeriod = 0
    self.waveBalance = 0
    self.wavePower = 0

  #pylint: enable=too-many-instance-attributes


  def findWave (self, tick, currentWaveHeight):
    """analyze wave height to find zero crossings and peaks of raw waves.
    
    Args:
      tick: (long) epoch in s.
      waveHeight: (float) instantaneous wave height above or below average.
    
    Returns:
      True if a wave was found, false otherwise
    
    Raises:
      None
    """
  
    waveFound = False
    if self._firstTime:
      self._firstTime = False
      self._lastPositiveTrend = True
      self._positivePeak = 0
      self._negativePeak = 0
      self._positivePeriod = 0
      self._negativePeriod = 0
      self._zeroCrossingTick = 0
    else:
      positiveTrend = bool( currentWaveHeight >= 0)
      if positiveTrend != self._lastPositiveTrend: # zero crossing
        #print "zero crossing: pos:" + str(positive_peak) + 
        #    " neg:" + str(negative_peak)
        if positiveTrend: # ending negative period and the wave as a whole
          self._negativePeriod = tick - self._zeroCrossingTick
          self.wavePeriod = self._positivePeriod + self._negativePeriod
          self.wavePeakToPeak = self._positivePeak - self._negativePeak
          self._positivePeak = currentWaveHeight # for the new period...
          self.waveTick = tick
  
          #self.wavePower = POWER_CONSTANT * self.wavePeakToPeak * \
          #    self.wavePeakToPeak * self.wavePeriod 
  
          #ALT wave power calculation
          g = 32.174 # gravitation constant ft/s/s
          density = 62.29 # density of water pounds/ft/ft/ft
          depth = 4 # water depth ft, variable depending on measurement loc
  
          #waveSpeed = math.sqrt( math.tanh( 2 * math.pi * depth /
          #    self.wavePeakToPeak/12) *\
          #    g * waveLength / 2 / math.pi)
          #waveLength = waveSpeed * wavePeriod
          #
          #waveSpeed = g * wavePeriod/2/pi # for wavelength / water depth
          #    ratio < 0.5...depth>2*wavelen
          # we are not there... 8ft wave needs 4 feet of water,
          #    30ft wave needs 15 feet of water
          # shallow formula: period velocity = square root(g * water depth)
          waveSpeed = math.sqrt(g * 4) # feet/s
          waveLength = self.wavePeriod * waveSpeed # feet
  
          waveHeight = self.wavePeakToPeak/12 # in feet
          self.wavePower = g * density * waveHeight * waveHeight * \
             waveSpeed * (.5 + (2 * math.pi * depth / waveLength) / \
                math.sinh (4 * 3.159 * depth / waveLength)) / 8 # in HP
  	
  
          #end ALT wave power calculation
  
          if self._negativePeriod > 0 and self._negativePeak < 0: # no div by 0
            self.waveBalance = (self._positivePeriod * self._positivePeak) / \
                (self._negativePeriod * -self._negativePeak) -0.5 # 0 balanced,
                                                                # +/- imbalance
          else:
            self.waveBalance = 0
          if self.wavePeriod < 90: # s, reasonableness check
            waveFound = True
    
        else: # end of positive period, the first half of a wave
          self._positivePeriod = tick - self._zeroCrossingTick
          self._negativePeak = currentWaveHeight
    
        # prepare for next wave
        self._zeroCrossingTick = tick
        self._lastPositiveTrend = positiveTrend
    
      # not zero crossing, in the body of a wave somewhere
      if positiveTrend:
        if currentWaveHeight > self._positivePeak:
          self._positivePeak = currentWaveHeight
      else:
        if currentWaveHeight < self._negativePeak:
          self._negativePeak = currentWaveHeight
    return waveFound


#pylint: enable=too-few-public-methods
  
  
def test():
  """ perform unit tests on this module

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  


if __name__ == "__main__":
  # execute only if run as a script
  test()
