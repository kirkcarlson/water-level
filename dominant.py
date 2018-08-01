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


#### CLASSES ####

class Dominant (object):
  """Dominant frequency."""


  def __init__ (self):
    """Return a dominant object.
  
    Args:
      None
    
    Returns:
      None
    
    Raises:
      None
    """

    self.firstPeriod = 0
    self.secondPeriod = 0
    self.thirdPeriod = 0
    self.firstResponse = 0
    self.secondResponse = 0
    self.thirdResponse = 0
    """what

    Args:
      power: float (mW?) power of the wave

    Returns:
      None

    Raises:
      None
    """


  def update( self, period, response):
    """Add a spectrum measurement to determine which is dominant
  
    Args:
      period: float (s) The wave period of the measured wave
      response: float (nW) The response of the particular period
    
    Returns:
      None
    
    Raises:
      None
    """

    if response > self.firstResponse:
      self.thirdResponse = self.secondResponse
      self.secondResponse = self.firstResponse
      self.firstResponse = response
      self.thirdPeriod = self.secondPeriod
      self.secondPeriod = self.firstPeriod
      self.firstPeriod = period
    elif response > self.secondResponse:
      self.thirdResponse = self.secondResponse
      self.secondResponse = response
      self.thirdPeriod = self.secondPeriod
      self.secondPeriod = period
    elif response > self.thirdResponse:
      self.thirdResponse = response
      self.thirdPeriod = period


  def reset (self):
    """Clear data arrays before the saved period of time.
  
    Args:
      period: (int) (s) time to preserve in the current lists
    
    Returns:
      None
    
    Raises:
      None
    """
    self.firstPeriod = 0
    self.secondPeriod = 0
    self.thirdPeriod = 0
    self.firstResponse = 0
    self.secondResponse = 0
    self.thirdResponse = 0


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
  pass
