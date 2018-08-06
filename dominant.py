#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
dominant - module for managing the dominate frequency of a wave

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

from config import NUM_CANDIDATES


#### CLASSES ####

class Dominant( object):

    def __init__( self, period):
        """ initialize the attributes of the dominant wave
      
        Args:
          period: float (s) Number of seconds that items in list are valid
        
        Returns:
          None
        
        Raises:
          None
        """
        self.candidates = []
        self.validPeriod = period


    def reset( self):
        """ resets the candidates for the dominant wave
            this should not be necessary on a rolling platform
      
        Args:
          None
        
        Returns:
          None
        
        Raises:
          None
        """
        self.candidates = []


    def update( self, tick, period, peak, power):
        """ maintains a list of the most dominant waves within a time period
      
        ..this assumes dominate power is also dominant peak and period

        Args:
          tick: float (s) number of second in the epoch
          period: float (s) The wave period of the measured wave
          peak: float (in) The peak-to-peak height of a wave in inches
          power: float (mW?) The power of the wave
        
        Returns:
          None
        
        Raises:
          None
        """
        # remove candidates that are too old
        ageLimit = tick - self.validPeriod
        done = False
        while not done and len(self.candidates) > 0:
            for i, candidate in enumerate( self.candidates): 
                if candidate[0] < ageLimit:
                    self.candidates.pop(i)
                    break
            done = True

        # if there is a vacancy, add the new value regardless of value
        if len( self.candidates) < NUM_CANDIDATES:
            self.candidates.append( (tick, period, peak, power))

        # elif new value is greater than smallest on list, replace it
        else:
            minPower = power
            minIndex = None
            for i, candidate in enumerate( self.candidates):
                if candidate[ 3] < minPower:
                    minIndex = i
                    minPower = candidate[ 3]
            if minIndex is not None:
                self.candidates.pop(i)
                self.candidates.append( (tick, period, peak, power))

    
    def value( self):
        """ returns the dominant wave period, peak, and power
      
        Args:
          None
        
        Returns:
          tuple of the period, peak and power of dominant wave
        
        Raises:
          None
        """
        maxPower = 0
        for i, candidate in enumerate( self.candidates):
            if candidate[ 3] > maxPower:
                maxIndex = i
                maxPower = candidate[ 3]
        return (self.candidates[i][1], self.candidates[i][2], \
                    self.candidates[i][3])


def test(self):
    """Test the functions and methods of this module.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    pass


if __name__ == "__main__":
  # execute only if run as a script
  #RW = sdominant(0) 
  #RW.test()
  test()
