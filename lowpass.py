#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
lowpass - module for implementing a crude low pass filter

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
from collections import deque



#### CLASSES ####

class LowPass ( object):
  """In in a positive trend, return max number in span, else return min number in span."""

  def __init__ (self, span):
    """Initialze a low pass object
  
    Args:
      seed: (float) initial value of average
      span: (int) number of samples in series
      
    Returns:
      None
    
    Raises:
      None
    """
    self.span = span
    self.members = deque([])
    self.positive = True
    self.average = None
    self.first = True


  def reset( self): # for the averaging version
    """Reset an average
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    self.average = None
    self.first = True


  def update( self, value):
    """update low pass filter as the running average of the inputs
  
    Args:
      value
    
    Returns:
      Updated average value
    
    Raises:
      None
    """

    if self.first:
      self.first = False
      newAverage = value
    else:
      newAverage = (self.average * (self.span - 1) + value) / self.span
    self.average = newAverage
    return newAverage


  def updateFunky( self, value):
    """Update a low pass filter with a new vlaue
  
    Args:
      value: (float) the value to update the filter
    
    Returns:
      value: (float) the value passing the filter
    
    Raises:
      None
    """

    self.members.append(value)
    while len( self.members) > self.span:
      self.members.popleft()
    value = max (self.members)

    if self.positive:
      value = max(self.members)
      if value >= 0:
        return value
      #value is negative
      value = min(self.members)
      self.positive = False
      return value
    #value is negative
    value = min(self.members)
    if value < 0:
      return value
    #value is positive 
    value = max(self.members)
    self.positive = True
    return value


  def test(self):
    """Test the functions and methods in this module.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """
    tests = [ 1,2,3,4,3,2,1,2,3,4,5,6,5,4,3,2,1,0,-1,-2,-1,0,1,0,-1,-1,-2,-3,-2,1, 2, 3, 4]
    result =[ 1,2,3,4,4,4,4,3,3,4,5,6,6,6,6,5,4,3, 2, 1, 0,0,1,1, 1, 1, 0,-3,-3,-3,-3,-2,4]
    for i, test in enumerate( tests):
      lp = self.update( test)
      if lp is not result[i]:
        print "got:", lp, " expected", result[i]
        exit(1)
      print test, lp
    exit(0)


if __name__ == "__main__":
  testLP = LowPass( 4)
  testLP.test()



