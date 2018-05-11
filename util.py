#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
utils -- Miscellaneous functions for water level processing

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


#### CONSTANTS ####


#### CLASSES ####


#### FUNCTIONS ####

def runningAverage (ave, value, span):
  """affect a running average with a new value

  This determines a running average by adding 1/span of the value to the
  (span-1)/span * average.  Note: the running average is a bit slower to
  react to abrupt changes than a purely numeric average.
  
  Args:
    ave: running average (float)
    value: new value to add to the average (float)
    span: number of values considered to be in the average
  
  Returns:
    None
  
  Raises:
    None
  """
  if ave == 0.:
    return value
  return ((span -1) * ave + value) / span
