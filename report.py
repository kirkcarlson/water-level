#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
report -- module for sending messages to a file or to the standard output

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
import sys
from config import VERB_DEBUG
from config import MAX_LIST



#### CLASSES ####

class ReportChannel( object):
  """An output channel for reports and events

  attributes:
    name: string representing the output channel name
    handle: file handle for the output
    verbosity: interger representing the amount of information desired
  """

  def __init__ ( self, filename, verbosity=0):
    """Return a ReportChannel object selected with *filename* and contolled
    with *verbosity*.
  
    Args:
      filename: (str) file name
      verbosity: (int) Desired level of message output
    
    Returns:
      None
    
    Raises:
      None
    """

    if filename == "":
      self.handle = sys.stdout
    else:
      self.handle = open(filename,"a")
    self.verbosity = verbosity


# pylint disable=pointless-statement
  def close (self):
    """close an open output channel."""
    if self.handle is not None:
      pass#self.handle.close
# pylint enable=pointless-statement


  def setVerbosity( self, verbosity):
    """Set the value of verbosity for the channel.
  
    Args:
      verbosity: (int) Desired level of message output for the channel.
    
    Returns:
      None
    
    Raises:
      None
    """
    self.verbosity = verbosity


  def write( self, message):
    """Send a message to a ReportChannel.
  
    Args:
      message: (str) String to be reported.
    
    Returns:
      None
    
    Raises:
      None
    """
    self.handle.write( message)


  def writeln( self, message):
    """Send a one-line message to the ReportChannel.
  
    Args:
      value: float the value.
    
    Returns:
      None
    
    Raises:
      None
    """
    self.write( message + "\n") 


  def prEvent( self, tick, processName, message, verbosity):
    """Send a formated event message on the ReportChannel, if the verbosity
    level is met.
  
    Args:
      tick: (float) epoch for the event time stamp
      processName: (str) name of the process detecting the event
      message: (str) String to be reported
      verbosity: (int) Interest level of this event.
    
    Returns:
      None
    
    Raises:
      None
    """

    dateString = '{:%b %d %H:%M:%S}'.format(
        datetime.datetime.fromtimestamp (float(tick)))
    if verbosity >= self.verbosity:
      self.writeln( "{:<16} {:<20} {}".format(
          dateString, processName, message))

  def prReport( self, message):
    """send a report message to the ReportChannel.
  
    Args:
      message: (str) String to be reported
    
    Returns:
      None
    
    Raises:
      None
    """

    self.writeln( message)


  def prDebug( self, message):
    """print debug statements controlled by the verposity.
  
    Args:
      message: (str) String to be reported
    
    Returns:
      None
    
    Raises:
      None
    """
  
    if VERB_DEBUG > self.verbosity:
      self.writeln( message)
  

  def prLog( self, tick, processName, message, verbosity):
    """Print a message for the log file
  
    Args:
      tick: (float) epoch for the event time stamp
      processName: (str) name of the process detecting the event
      message: (str) String to be reported
      verbosity: (int) Interest level of this event.
    
    Returns:
      None
    
    Raises:
      None
    """
  
    dateString = '{:%b %d %H:%M:%S}'.format(
        datetime.datetime.fromtimestamp (tick))
    if verbosity >= self.verbosity:
      print "{:<16} {:<20} {}".format(dateString, processName, message)


#### FUNCTIONS ####

newPadding = '    '
ITER_NUM = False # False for syntactically correct output
                 # True for "enumeration:" for lists and tuples

def varString(invar, padding=''):
  """convert the variable to a structured string for printing

  Args:
    invar: variable to be printed
    padding: padding to be applied on left hand side to show structure
  
  Returns:
    (str) representing the value of invar
  
  Raises:
    None
  """

  outStr = ""
  if isinstance(invar, dict):
    outStr = outStr + dictString( invar, padding)

  elif isinstance(invar,list):
    outStr = outStr + listString( invar, padding)

  elif isinstance(invar,tuple):
    outStr = outStr + tupleString( invar, padding)

  elif isinstance(invar,str):
    outStr = outStr + '"' + str(invar) + '"'

  else:
    outStr = outStr + str(invar)
  return outStr


def dictString( invar, padding):
  """Add a value to the running statistics for the variable.
  
  Args:
    value: float the value.
   
  Returns:
    None
    
  Raises:
    None
  """
  outStr = "{"
  newline = "\n"
  for k,v in invar.iteritems():
    outStr = outStr + newline + padding + newPadding + varString(k) + ': ' + \
        varString(v, padding + newPadding)
    newline =  ",\n" 
  newline = "\n"
  outStr = outStr + newline + padding + "}"
  return outStr


def listString( invar, padding):
  """Add a value to the running statistics for the variable.
  
  Args:
    value: float the value.
   
  Returns:
    None
    
  Raises:
    None
  """
  newline = "\n"
  if not invar:
    outStr = "[]"
  elif len(invar) < MAX_LIST:
    outStr = "["
    for k,v in enumerate (invar):
      if ITER_NUM:
        outStr = outStr + newline + padding + newPadding + str(k) + ': ' + \
            varString(v, padding + newPadding)
      else:
        outStr = outStr + newline + padding + newPadding +\
          varString(v, padding + newPadding)
      newline =  ",\n" 
    newline = "\n"
    outStr = outStr + newline + padding + "]"
  else:
    outStr = str(invar)
  return outStr


def tupleString( invar, padding):
  """Add a value to the running statistics for the variable.
  
  Args:
    value: float the value.
    
  Returns:
    None
    
  Raises:
    None
  """
  newline = "\n"
  outStr = "("
  for k,v in enumerate (invar):
    if ITER_NUM:
      outStr = outStr + newline + padding + newPadding + str(k) + ': ' +\
          varString(v, padding + newPadding)
    else:
      outStr = outStr + newline + padding + newPadding +\
          varString(v, padding + newPadding)
    newline =  ",\n" 
  newline = "\n"
  outStr = outStr + newline + padding + ")"
  return outStr



def testVarString ():
  """ Function to exercise the varString function
  
  Args:
    None
    
  Returns:
    None
    
  Raises:
    None
  """
  i = 34
  f = 3.14159
  s = "string"
  s1234 = "preceding should be 1, 2, 3, 4"
  s123 = "preceding should be 1, 2, 3"
  t = 1, 'b', 3, "preceding should be 1, \"b\", 3"
  l = [1, 2, 3, 4, s1234]
  ll = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  d1 = {1:1, 2:2, 3:3, 4:s123, 5:t, 6:l}
  d2 = { 1: 1, '2a': 2, '2b': '2b', 3: t, 4: l, 5: d1 }

  print 'integer: ', varString (i)
  print 'float: ', varString (f)
  print 'string: ', varString (s)
  print 'tuple: ', varString (t)
  print 'list: ', varString (l)
  print 'long list: ', varString (ll)
  print 'simple dict: ', varString (d1)
  print 'complex dict: ', varString (d2)


if __name__ == "__main__":
  # execute only if run as a script
  testVarString()
  # should be something here to test the rest of the module
