#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
plot: module for handling the interface to the plot functions.

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
import time
import os
import math
import random
from config import LENGTH_COLORS
from config import ENERGY_SIZES

import numpy as np
import matplotlib
from matplotlib.dates import MINUTELY
import matplotlib.pyplot as plt



#### FUNCTIONS ####

def plotTimeCommon (plotName, timeToPlot, times, yLabel, lines):
  """Control the common part of the plotting for a give duration of time

  Args:
    plotName: (string) plot legend and base file name
    timeToPlot: (int) maximum number of seconds to include in plot
    times: (array of float) epoch (s)
    yLegend: legend fo the Y axis
    lines: (array of dict)
      label: (string) label for the line
      points: (array of float) data point for the line
      lineType: (optional string) type of line (e.g., -,_,.,..)
      lineColor: (optional string) color code of line (e.g., R, B, G, C)

  Return:
    None

  Raises:
    None
"""
  #convert timeToPlot to a numberToPlot
  baseTime = times [-1]
  numberToPlot = 0
  for i in range (len( times)-1, 0):
    numberToPlot = numberToPlot + 1
    if baseTime - times[i] > timeToPlot:
      break
  plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotCommon (plotName, numberToPlot, times, yLabel, lines):
  """Control the common part of the plotting

  Args:
    plotName: (string) plot legend and base file name
    numberToPlot: number of points to plot
    times: (array of float) epoch (s)
    yLegend: legend fo the Y axis
    lines: (array of dict)
      label: (string) label for the line
      points: (array of float) data point for the line
      lineType: (optional string) type of line (e.g., -,_,.,..)
      lineColor: (optional string) color code of line
        b: blue
        g: green
        r: red
        c: cyan
        m: magenta
        y: yellow
        k: black
        w: white



  Return:
    None

  Raises:
    None
"""

  if numberToPlot > len(times):
    numberToPlot = len(times)
  if numberToPlot > 0:
    timeDatetimes = [datetime.datetime.fromtimestamp(times[i]) \
            for i in range (len(times)-numberToPlot, len(times))]

    # prepare the Y-axis
    plt.ylabel( yLabel)
    pline = []
    for i, line in enumerate(lines):
      #print "Length points:", len(line['points'][-numberToPlot:])
      pline.append(plt.plot( np.array( timeDatetimes),
                             np.array( line['points'][-numberToPlot:]),
                             label=line['label'])) # color, line type?

    # prepare the X-axis
    plt.xlabel( 'Time')
    locator = matplotlib.dates.AutoDateLocator()
    locator.intervald[MINUTELY] = [1]
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter( matplotlib.dates.DateFormatter(
        "%H:%M:%S"))
    plt.gca().xaxis.set_major_locator( matplotlib.dates.AutoDateLocator(
        minticks=12, maxticks=20, interval_multiples=True))

    # prepare the basic plotting information
    plt.legend(loc=0, fontsize=9)
    plt.title( plotName)
    baseName = plotName.replace( ' ', '_')
    path = fileTimePng (baseName, times[-1])
  
    # plot it
    plt.savefig( path)
    plt.close()

    #link plot file to latest 
    latest = "./latest_" + baseName + ".png"
    if os.access(latest, os.W_OK):
      os.remove (latest)
    os.link( path, latest)
    
    #link plot file to name starting with time
    timeFirstName = fileTimeFirstPng (baseName, times[-1])
    if os.access(timeFirstName, os.W_OK):
        os.remove( timeFirstName)
    os.link( path, timeFirstName)

    
#pylint: disable=too-many-arguments
def plotCluster (plotName, numberToPlot, times, distances, periods, energys):
  """Plot the information about clusters. """

  def length2color( length):
    """Convert energy to a ploting color code.
    """
    for i in range(0,len(LENGTH_COLORS)):
      if length <= LENGTH_COLORS[i][0]:
        return LENGTH_COLORS[i][1]
    return "k"


  def energy2size( energy):
    """Convert energy to a ploting color code.
    """
    for i in range(0,len(ENERGY_SIZES)):
      if energy <= ENERGY_SIZES[i][0]:
        return ENERGY_SIZES[i][1]
    return 35


  def period2waveLength ( period):
    """Convert period to wavelength for deep water wave."""

    g = 32.174 # gravitation constant ft/s/s
    twoPi = 2 * 3.14159
    waveSpeed = g / twoPi * period  
    return period * waveSpeed


  # convert the periods to colors
  # wavelength = period * waveVelocity
  boatColors = [ length2color( period2waveLength( period))
                 for period in periods]

  # convert the energies to radii
  energySizes = [energy2size (energy) for energy in energys]

  # plot the points
  #print "plotCluster times: ", times
  plotScatter (plotName, numberToPlot, times, distances,
               c=boatColors,
               s=energySizes,
               yL='Distance (ft)')

  #pylint: enable=too-many-arguments


#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals
def plotScatter (plotName, numberToPlot, times, points,
                 c=None,
                 s=None,
                 yL='Y-legend'):
  """Control a scatter plot

  Args:
    plotName: (string) plot legend and base file name
    numberToPlot: number of points to plot
    times: (array of float) epoch (s)
    points: (array of float) value of y
    colors: (array of string or int?) for the plot color codes
    sizes: (array of int) diameter of the point
    yLegend: legend fo the Y axis
    colorLegend: color code, string tuples
    sizeLegend: int, string tuples

  Return:
    None

  Raises:
    None
"""

  if numberToPlot > len(times):
    numberToPlot = len(times)
  if numberToPlot > 0:
    timeDatetimes = [datetime.datetime.fromtimestamp(times[i]) \
            for i in range (len(times)-numberToPlot, len(times))]
    #timeDatetimes = []
    #for i in range (numberToPlot):
      #timeDatetimes.append(datetime.datetime(1970, 1, 1, 0,
      #                                       int(60*random.random()), 0, 0))
    #  timeDatetimes.append(times[i])
    #print timeDatetimes

    #fig = plt.figure()
    ax = plt.subplot(111)
  
    # prepare the Y-axis
    plt.ylabel( yL)

    # prepare the X-axis
    plt.xlabel( 'Time')
    locator = matplotlib.dates.AutoDateLocator()
    locator.intervald[MINUTELY] = [1]
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter( matplotlib.dates.DateFormatter(
        "%H:%M:%S"))
    plt.gca().xaxis.set_major_locator( matplotlib.dates.AutoDateLocator(
        minticks=12, maxticks=20, interval_multiples=True))
    if s:
      s1 = s
    else:
      s1 = None
    if c:
      c1 = c
    else:
      c1 = None

    # prepare the basic plotting information
    plt.title( plotName)
  
    plt.plot([],[]) # just to set up the plot....
    plt.scatter(timeDatetimes, points, s=s1, c=c1, alpha=0.5)
    #plt.plot(timeDatetimes, points)


    # define the text and symbols for the legend
    pseudoLines = []
    legendLabels = []
    for lengthColorTuple in LENGTH_COLORS:
      legendLabels.append( lengthColorTuple[0]) # length integer
      pseudoLines.append(
          plt.scatter(
              [], [],
              marker='o',
              color=lengthColorTuple[1], # length color character
              s=ENERGY_SIZES[1][1])) # use a small size for all

    for index, lengthColorTuple in enumerate( LENGTH_COLORS):
      legendLabels.append( ENERGY_SIZES [index][0]) # energy integer
      pseudoLines.append(
          plt.scatter(
              [], [],
              marker='o',
              color=LENGTH_COLORS[0][1], # use same color for all
              s=ENERGY_SIZES[index][1])) # energy circle size

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
  
    ax.legend((pseudoLines),
              (legendLabels),
              scatterpoints=1,
              loc='lower left',
              ncol=2,
              fontsize=8,
              labelspacing=2,
              title='Legend:\nlength--energy',
              bbox_to_anchor=(1.05, 0.2)
             )

    baseName = plotName.replace( ' ', '_')
    path = fileTimePng (baseName, times[-1])

    # plot it
    plt.savefig( path)
    plt.close()

    #link plot file to latest 
    latest = "./latest_" + baseName + ".png"
    if os.access(latest, os.W_OK):
      os.remove (latest)
    os.link( path, latest)
    
    #link plot file to name starting with time
    timeFirstName = fileTimeFirstPng (baseName, times[-1])
    if os.access(timeFirstName, os.W_OK):
        os.remove( timeFirstName)
    os.link( path, timeFirstName)


  #pylint: enable=too-many-arguments
  #pylint: enable=too-many-locals
  
    
def fileTimePng (baseName, tick, suffix=""):
  """create name for png filename
  should be more along lines generate PNG (or plot) filename
  there may ba a companion for saving spectrum data

  Args:
    baseName: string base name of the file
    sampleTimeStr: string timestamp for the file name
    suffix: additional suffix for file name, usually page number
  
  Returns:
    None
  
  Raises:
    error if baseName is not a string
  """

  currentDateTime = datetime.datetime.fromtimestamp(tick)
  #for reporting time to seconds:
  timeStr = currentDateTime.strftime( "%Y.%m.%d_%H.%M.%S")
  #for reporting time to subseconds:
  #  timeStr = currentDateTime.strftime( "%Y.%m.%d_%H.%M.%S.%f")
 
  if not isinstance(baseName, str) or baseName == "":
    raise ValueError("baseName should be string")
  elif timeStr == "":
    raise ValueError("timeStr should be string")
  else:
    return baseName + "_" + timeStr + suffix + ".png"


def fileTimeFirstPng (baseName, tick, suffix=""):
  """create name for png filename with time first
  should be more along lines generate PNG (or plot) filename
  there may ba a companion for saving spectrum data

  Args:
    baseName: string base name of the file
    sampleTimeStr: string timestamp for the file name
    suffix: additional suffix for file name, usually page number
  
  Returns:
    None
  
  Raises:
    error if baseName is not a string
  """

  currentDateTime = datetime.datetime.fromtimestamp(tick)
  #for reporting time to seconds:
  timeStr = currentDateTime.strftime( "%Y.%m.%d_%H.%M.%S")
  #for reporting time to subseconds:
  #  timeStr = currentDateTime.strftime( "%Y.%m.%d_%H.%M.%S.%f")
 
  if not isinstance(baseName, str) or baseName == "":
    raise ValueError("baseName should be string")
  elif timeStr == "":
    raise ValueError("timeStr should be string")
  else:
    return timeStr + "_" + baseName + suffix + ".png"


#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals
#pylint: disable=too-many-statements
def plotFrequencyResponse( pSpectra, startIndex, stopIndex, timeToPlot, name,
                           verticalSpacing = 5,
                           maxPerPage = 10):
  """plot some of frequency responses

  Args:
    pSpectra: object
      'times': list of times
      'spectra': list of spectrum
        'spectrum': (object)
           list of responses
           sample: pointer back to the sample object
             legend: lable to be used with plotting
    startIndex: index of the first spectum to plot
    stopIndex: index of the last spectum to plot
    timeToPlot: number of seconds of data to plot
    name: name string for the plot label and file name

  Returns:
    None

  Raises:
    None
  """

  startTime = time.time()
  print "pFR", startIndex, stopIndex, timeToPlot, name, verticalSpacing, \
      maxPerPage
  locator = matplotlib.dates.AutoDateLocator()
  locator.intervald[MINUTELY] = [1]
  verticalOffset = 0
  line = {}

  #print "len times:",len( pSpectra.times)

  # convert timeToPlot to numberToPlot
  baseTime = pSpectra.times[-1]
  numberToPlot = 0
  for i in reversed( range( 0, len(pSpectra.times) - 1)):
    numberToPlot = numberToPlot + 1
    if baseTime - pSpectra.times[i] > timeToPlot:
      break

  #print "number to plot:",numberToPlot

  pageNumber = 0 # no paging required
  linesToPlot = stopIndex - startIndex + 1
  if linesToPlot > maxPerPage:
    numberOfPages = int( math.ceil( (linesToPlot + 0.) / maxPerPage))
    linesPerPage = int( math.ceil( (linesToPlot + 0.) / numberOfPages))
    pageNumber = 1 # paging required
  x = [ datetime.datetime.fromtimestamp(i)
        for i in pSpectra.times[-numberToPlot:] ]
  # for the desired spectrum
  baseRange = startIndex
  for j in range (startIndex, stopIndex+1):
    #print "len times and response j:", \
    #    len( pSpectra.times), \
    #    len( pSpectra.spectra[j].responses), \
    #    numberToPlot

    # pad out y
    if len(pSpectra.spectra[j].responses) >= numberToPlot:
      y = [] # clear y each pass
      #print "clearing y"
    else:
      y = []
      y.extend( verticalOffset 
                for i in range(
                    0,
                    numberToPlot-len(pSpectra.spectra[j].responses)))
      #print "extending y"
    
    y.extend ( [i + verticalOffset
                for i in pSpectra.spectra[j].responses[-numberToPlot:] ] )

    # add spectrum to plot
    verticalOffset = verticalOffset + verticalSpacing
    #print "len x and y:",len(x), len(y)
    line[j - baseRange] = plt.plot(np.array( x), np.array( y),
                                   label= pSpectra.spectra[j].sample.legend)

    if (j == stopIndex) or (j - baseRange == linesPerPage - 1): # plot chart
      plt.title( name)
      plt.xlabel('Time (s)')
      plt.ylabel('Response')
      plt.gca().xaxis.set_major_formatter(
          matplotlib.dates.DateFormatter("%H:%M:%S"))
      plt.gca().xaxis.set_major_locator(
          matplotlib.dates.AutoDateLocator(
              minticks=3,
              maxticks=20,
              interval_multiples=True))
      plt.gcf().autofmt_xdate()
      plt.axes().xaxis_date()
      plt.legend(loc=0, fontsize=9)
      name = name.replace( ' ', '_')
      if pageNumber:
        path = fileTimePng (name, pSpectra.times[-1],
                            "_Page_" + str( pageNumber))
        pageNumber = pageNumber + 1
      else:
        path = fileTimePng (name, pSpectra.times[-1])
      plt.savefig( path)
      plt.close()
      line = {}
      baseRange = j + 1
  print "Time to plot response:", time.time() - startTime
  #pylint: enable=too-many-arguments
  #pylint: enable=too-many-locals
  #pylint: enable=too-many-statements


def scatterTest():
  """Test the plot functions and methods."""

  SIZE = 20
  times =  [time.time() - random.random() * 3600 for _ in range(SIZE)]
  values = [ 2500 * random.random() for _ in range( SIZE)]
  colors = [ LENGTH_COLORS[int( random.random() * len(LENGTH_COLORS))][1]
             for _ in range( SIZE)]
  sizes =  [ ENERGY_SIZES[int( random.random() * len (ENERGY_SIZES))][1] 
             for _ in range( SIZE)]

  plotScatter ("Scatter Test",
               SIZE,
               times,
               values,
               c=colors,
               s=sizes,
               yL="Distance (ft)")

  SIZE = 20
  times =  [time.time() - 3600/SIZE*i for i in range(0,SIZE) ]
  distances = [ 2500 * random.random() for _ in range( SIZE)]
  periods =  [ 3.2 * random.random() for _ in range( SIZE)]
  energys = [ 35 * random.random() for _ in range( SIZE)]

  plotCluster ("Cluster Test", SIZE, times, distances, periods, energys)

#### MAIN ####


if __name__ == "__main__":
  # execute only if run as a script
  scatterTest()
