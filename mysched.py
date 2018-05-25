#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
mysched -- module for scheduling tasks

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

class Schedule (object):
  """an object for managing task scheduling to execute at specific times

  Methods:
    schedule: add a task to be executed in the future
    unschedule: remove a task from the execution order
    execute: excecute timed tasks that are due
  
  Returns:
    None
  
  Raises:
    None
  """

  def __init__ (self):
    self.tasks = []
    self.processID = 1


  def schedule (self, function, tick, period, offset=0):
    """schedule a task for future execution
  
    Args:
      function: (addr) parameterless function to be executed
      tick: (float) the current epoch in seconds
      period: (int) how often the task is to be executed in seconds,
              set to 0 for non-recurring tasks
      offset: (int) optional offset s after the period for execution
    
    Returns:
      processID assigned
    
    Raises:
      None
    """
  
    self.processID = self.processID + 1
    if period == 0: # one time scheduling, just use the offset
      due = tick + offset
    else:
      due = nextDue ( tick, period, offset)

    self.tasks.append ( {
      'processID': self.processID,
      'function':  function,
      'period':    period,
      'offset':    offset,
      'due':       due
    })
    return self.processID


  def unschedule (self, processID):
    """Remove a task from the scheduled process list

    Args:
      processID: (float) identifier for the task to be removed
  
    Returns:
      None
  
    Raises:
      None
    """
    #print "unschedule, processID is type: ", type(processID), processID,
    #    self.tasks
    #print "unschedule: ", processID
    #print self.tasks
    for i, task in enumerate( self.tasks):
      if processID == task['processID']:
        #print "popping", i
        self.tasks.pop( i)
        break
    #print self.tasks

  def execute(self, tick):
    """Execute timed tasks that are due.

    Args:
      tick: (float) current time as epoch seconds
  
    Returns:
      None
  
    Raises:
      None
    """
    for i, task in enumerate( self.tasks):
      if tick > task['due']:
        #print "execute popping", i, tasks
        dueTask = self.tasks.pop(i)
        #print tasks
        if dueTask['function'] is not None:
          dueTask['function']( tick) # execute the task
          if dueTask['period'] > 0: # recurring task
            due = nextDue (tick, dueTask['period'], dueTask['offset'])
            self.tasks.append ( {
              'processID': dueTask['processID'],
              'function':  dueTask['function'],
              'period':    dueTask['period'],
              'offset':    dueTask['offset'],
              'due':       due
            })
 

#### FUNCTIONS ####

def nextDue (tick, period, offset=0):
  """Determine the tick with something will be due

  Args:
    tick: (long) epoch s of the current time
    period: (long) duration s between scheduling (like every 5 minutes)
    offset: (long) duration s from scheduled time (like 2 seconds after)
      the offset is used to sequence processing and to resolve pile ups
 
  Returns:
    (long) epoch s of the due time
  
  Raises:
    None
  """
  return int( tick / period) * period + period + offset


def test():
  """Test the methods and functions of this module

  The test results should be as follows:
  Tick:  0
  Tick:  1
  Tick:  2
  hi
  Tick:  3
  Tick:  4
  hi
  Tick:  5
  Tick:  6
  hi
  hello
  Tick:  7
  Tick:  8
  hi
  hi there
  Tick:  9
  Tick:  10
  hi
  Tick:  11
  hello
  Tick:  12
  hi
  Tick:  13
  hi there
  Tick:  14
  hi
  Tick:  15
  Tick:  16
  hi
  hello
  Tick:  17
  Tick:  18
  hi
  hi there
  Tick:  19 


  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  def test1():
    """Test routine
    """
    print "hi"
  
  def test2():
    """Test routine
    """
    print "hello"
  
  def test3():
    """Test routine
    """
    print "hi there"
  
  def test4():
    """Test routine
    """
    print "one time event"

  mainSched = Schedule ()
  currentTick = 0
  mainSched.schedule (test1, currentTick, 1, 0)
  mainSched.schedule (test2, currentTick, 5, 0)
  mainSched.schedule (test3, currentTick, 5, 2)
  mainSched.schedule (test4, currentTick, 0, 5) # one time event
  print mainSched.tasks
  for currentTick in range (0,20):
    print "Tick: ", currentTick
    mainSched.execute( currentTick)


if __name__ == "__main__":
  test()
