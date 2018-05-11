#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
#pylint: disable=too-many-lines
"""
water-level a module for measuring water levels

Copyright (c) 2016-2018 Kirk Carlson, All Rights Reserved

Portions Copyright (c) 2014 Adafruit Industries
Author: Tony DiCola

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


BUGS:

1 Have to make a bigger distinction between instantaneous wave height or
sea wave height and the peak value of a wave. Doing stats on the instantaneous
value has limited value, because the mean should be zero as it has the DC
component subtracted from it.

2 Code is in a mixed state. It has some experimental code and some older code.
Need to decide which to keep and move on.


"""

#### IMPORTS ####

import sys
import datetime
import math
import json
from influxdb import InfluxDBClient

import sched
import config
import findwave
import inputchan
import level
import plot
import rawwaves
import report
import resamples
import spectra
#import stats

###NEW
import average
import highlow
import lowpass
import series
import stats2
import trap
###NEW


#### LOCAL CONSTANTS ####

errorMessage = \
    'try: ', sys.argv[0] + ' -i <inputFileName> -o <outputFileBaseName>'

EVERY_200_MSEC =           200./1000  # do every 200 milliseconds
EVERY_SECOND =               1 # do every second
EVERY_MINUTE =          1 * 60 # do every minute
EVERY_5_MINUTES =       5 * 60 # do every 5 minutes
EVERY_10_MINUTES =     10 * 60 # do every 10 minutes
EVERY_15_MINUTES =     15 * 60 # do every 15 minutes
EVERY_30_MINUTES =     30 * 60 # do every 30 minutes
EVERY_HOUR =       1 * 60 * 60 # do every hour
EVERY_4_HOURS =    4 * 60 * 60 # do every 4 hours
EVERY_8_HOURS =    8 * 60 * 60 # do every 8 hours
EVERY_DAY =       24 * 60 * 60 # do every day       
DAILY =           24 * 60 * 60 # do every day       
TWICE_DAILY =     12 * 60 * 60 # do twice a day       

#durations
DUR_10_SECONDS =          10
DUR_1_MINUTE =        1 * 60
DUR_15_MINUTES =     15 * 60
DUR_30_MINUTES =     30 * 60



#### GLOBALS ####

outChan = None
inChan = None
currentTick = None
tickdiff = None
client = None
mainSched = sched.Schedule()

levelTicks = None
waterLevel = None
longWaterLevels = None
longWaterTicks = None
longWaterLevelHiLoTicks = None
waves = None
sampleTimeSeries = None
spectraTimeSeries = None

rawWaterLevels = None
rawWaterLevelHighLow = None
longWaterLevel = None
longWaterLevelAve = None
longWaterLevelAves = None
longWaterLevelStats = None
longWaterLevelVariations = None
longWaterLevelHighLow = None
longWaterLevelHighs = None
longWaterLevelLows = None
waterLevelChangeRate1Minutes = None
waterLevelChangeRate5Minutes = None
waterLevelChangeRate15Minutes = None
medWaterLevelAve = None
waveBaselines = None
waveHeights = None
waveHeightLowPass = None
waveHeightHighLow = None
waveHeightAve = None
waveHeightAves = None
waveHeightStats = None
waveHeightVariations = None

waves2 = None
waveTimes = None
wavePeaks = None
wavePeriods = None
wavePowers = None
wavePowerStats = None
wavePowerVariations = None

waveTimes2 = None
wavePeaks2 = None
wavePeriods2 = None
wavePowers2 = None
wavePowerStats2 = None
wavePowerVariations2 = None



#### FUNCTIONS ####

def setupGracefulExit ( fileHandles):
  """setup for graceful exit

  Args:
    fileHandles: list of open file handles
  
  Returns:
    None
  
  Raises:
    None
  """
  #import signal

  # set up for a graceful exit on control-C
  OriginalExceptHook = sys.excepthook

  def NewExceptHook(hType, value, traceback):
    """hook to monitor keyboard input

    Args:
      hType: type of interrupt
      value: some sort of value that is passed through
      traceback: some sort of traceback that is passed through
  
    Returns:
      None
  
    Raises:
      None
    """

    #Replace exception hook to capture keyboard interrupt
    if hType == KeyboardInterrupt:
      for FH in fileHandles:
        FH.close()
        exit("\nExiting.")
    else:
      OriginalExceptHook(type, value, traceback)
  sys.excepthook = NewExceptHook


def processCommandLineArguments():
  """Process the command line arguments

  This processes the command line arguments, currently to set the
  input file name (if any) and the output file base name.
  
  Args:
    None
  
  Returns:
    inputFileName, outputFileBaseName
  
  Raises:
    None
  """
  import getopt                          # for argv parsing

  inputFileName = ''
  outputFileBaseName = 'test'
  #print "args: ", str( sys.argv)
  try:
    opts, remainder = getopt.getopt( sys.argv[1:], "hi:o:", [
        "ifile=", "ofile="])
    if remainder != []:
      print errorMessage
      sys.exit(2)
  except getopt.GetoptError:
    print errorMessage
    sys.exit(2)
  #print'got past the try, opts=', opts

  if opts:
    for opt, arg in opts:
      #print'got past the for'
      if opt == '-h':
        print errorMessage
        sys.exit()
      elif opt in ("-i", "--ifile"):
        inputFileName = arg
        #print "Input file is: " + inputFileName
      elif opt in ("-o", "--ofile"):
        outputFileBaseName = arg
        #print "Output file base name is: " + outputFileBaseName
  #print "inputFileName, outputFileBaseName: '" + inputFileName + "' '" +
  #    outputFileBaseName + "'"
  return inputFileName, outputFileBaseName


#def reportWave (tick, peak, period, balance, power, outChan):
#  """report the occurence of a wave with peak, period and time
#
#  Args:
#    None
#  
#  Returns:
#    None
#  
#  Raises:
#    None
#  """
#
#  #dateString = '{:%b %d %H:%M:%S}'.format(
#  #    datetime.datetime.fromtimestamp (tick))
#  #timeString = '{%H:%M:%S.%f}'.format(datetime.datetime.fromtimestamp (tick))
#  #timeString = datetime.datetime.fromtimestamp (tick).strftime(
#  #    '%Y-%m-%d %H:%M:%S.%f')
#
#  if outChan:
#    #outChan.writeln( "Raw Wave {0:<15}  {1:6.2f} in  {2:6.2f} s " +
#    #     " bal: {3:6.2f} {3:6.2f} uW".format(timeString, peak, period,
#    #                                         balance, power) )
#    pass
#    #outChan.prEvent(tick,
#    #                "Main",
#    #                "Wave Peak {:0.2f}, Period {:0.2f}, " +
#    #                "Power {:0.2f}".format(
#    #                     peak, period, balance, power),
#    #                VERB_DEBUG )
#
#  #if CSVChannel != 0:
#  #  CSVChannel.writeln(RWCSVFORMAT.format(tick, peak, period, power) )


def printPlot (plotName, numberToPlot, times, yLabel, lines):
  """ print the plotting parameters for debug purposes

  Args:
    plotName: name of the plot
    numberToPlot: number of points to plot
    times: number of times available
    yLabel: label for the y-axis
    lines: number of lines to plot
  
  Returns:
    None
  
  Raises:
    None
  """
  #print plotName, numberToPlot, "times: ", len(times),\
  #    yLabel, "lines: ", len(lines)
  pass


def updateLongWaterLevel():
  """update the long water level time series

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  ###Update the long water level from the more detailed raw water level.###
  ###longWaterLevel.analyze( currentTick, waterLevel.stats.averages[2][-1],
  ###                        outChan)
  longWaterTicks.append( currentTick)
  longAve = longWaterLevelAve.average
  longWaterLevels.append( longAve)
  longWaterLevelStats.append (longAve)
  longWaterLevelVariations.append( longWaterLevelStats.coefficientOfVariation)
  longWaterLevelHighLow.append( longAve)

  # calculate the water level change rates
  lenLevels = len( longWaterLevels.values)
  if lenLevels > 1+1:
    waterLevelChangeRate1Minute = ( longWaterLevels.values[-1] -
                                    longWaterLevels.values[-(1+1)]) * 60
  else:
    waterLevelChangeRate1Minute = 0
  if lenLevels > 1+5:
    waterLevelChangeRate5Minute = ( longWaterLevels.values[-1] -
                                    longWaterLevels.values[-(1+5)]) * 12
  else:
    waterLevelChangeRate5Minute = 0
  if lenLevels > 1+15:
    waterLevelChangeRate15Minute = ( longWaterLevels.values[-1] -
                                     longWaterLevels.values[-(1+15)]) * 4
  else:
    waterLevelChangeRate15Minute = 0

  # save change rates for plotting
  waterLevelChangeRate1Minutes.append( waterLevelChangeRate1Minute)
  waterLevelChangeRate5Minutes.append( waterLevelChangeRate5Minute)
  waterLevelChangeRate15Minutes.append( waterLevelChangeRate15Minute)


def updateLongWaterLevelHighLow():
  """update the long water level high low time series

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  longWaterLevelHiLoTicks.append( currentTick)
  longWaterLevelHighs.append( longWaterLevelHighLow.high)
  longWaterLevelLows.append( longWaterLevelHighLow.low)


def waterLevelReport15():
  """report on the water level in the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  ###Generate the 15 minute water level report.###
  waterLevel.report( currentTick, outChan)
  waterLevel.watch.reset( currentTick)


def longWaterLevelReport15():
  """report on the long term water level in the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  ###longWaterLevel.report( currentTick, outChan)
  ###longWaterLevel.watch.reset( currentTick)
  longWaterLevelHighLow.report( currentTick, outChan)
  longWaterLevelHighLow.reset()


def waveReport15():
  """report on wave activity in the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  waves.report( currentTick, outChan)
  waves.peakwatch.reset( currentTick) # other periods will want their own watch
  waves.periodwatch.reset( currentTick)
  waves.powerwatch.reset( currentTick) 


def plotRawLevel2():
  """plot the raw water level for the past 1 minute

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Raw Levels"
  numberToPlot = DUR_1_MINUTE*60*config.SAMPLES_PER_SECOND
  times = levelTicks
  yLabel = "Water Level (in)"
  lines = []
  lines.append ({'label':rawWaterLevels.name, 'points':rawWaterLevels.values})
  lines.append ({'label':waveBaselines.name, 'points':waveBaselines.values})
  lines.append ({'label':longWaterLevelAves.name,
                 'points':longWaterLevelAves.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def sendRawLevel2( currentTick, waterlevel, waveBaseLine, longWaterLevelAve,
        instantWaveHeight,
        aveWaveHeight):
  """send the raw water level to InfluxDB

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  # offset tick to trick InfluxDB
  offsetTick = currentTick + tickDiff # offset to yesterday for now

  json_body = []
  json_body.append (
    {
      "measurement" : "waterLevel",
      "tags" : {
        "type" : "raw"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : waterlevel
      }
    }
  )
  json_body.append (
    {
      "measurement" : "waterLevel",
      "tags" : {
        "type" : "waveBaseLine"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : waveBaseLine
      }
    }
  )
  json_body.append (
    {
      "measurement" : "waterLevel",
      "tags" : {
        "type" : "longWaterLevelAve"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : longWaterLevelAve
      }
    }
  )
  json_body.append (
    {
      "measurement" : "waveHeight",
      "tags" : {
        "type" : "instantWaveHeight"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : instantWaveHeight
      }
    }
  )
  json_body.append (
    {
      "measurement" : "waveHeight",
      "tags" : {
        "type" : "aveWaveHeight"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : aveWaveHeight
      }
    }
  )
  #print json_body
  if not client.write_points(json_body):
    print "Not updating database"
  #else:
  #  print '.',


def sendWave( currentTick, wavePeak, wavePeriod, wavePower):
  """send sea wave measurements to InfluxDB

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  # offset tick to trick InfluxDB
  offsetTick = currentTick + tickDiff # offset to yesterday for now

  json_body = []
  json_body.append (
    {
      "measurement" : "wave",
      "tags" : {
        "type" : "peak"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : wavePeak
      }
    }
  )
  json_body.append (
    {
      "measurement" : "wave",
      "tags" : {
        "type" : "period"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : wavePeriod
      }
    }
  )
  json_body.append (
    {
      "measurement" : "wave",
      "tags" : {
        "type" : "power"
      },
      "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                datetime.datetime.fromtimestamp(offsetTick)),
      "fields" : {
        "level" : wavePower
      }
   }
  )
  #print json_body
  if not client.write_points(json_body):
    print "Not updating database"
  #else:
  #  print '.',


def plotLongWaterLevelVariation():
  """plot the long water level variation

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  plotName = "Long Water Level Variation"
  numberToPlot = 60
  times = longWaterTicks
  yLabel = "Variation"
  lines = []
  lines.append ({'label':longWaterLevelVariations.name,
                 'points':longWaterLevelVariations.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotWaterLevelChangeRates():
  """plot the water level change rates

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  plotName = "Water Level Change Rates"
  numberToPlot = 60 # an hours worth
  times = longWaterTicks
  yLabel = "Change rate (in/hr)"
  lines = []
  lines.append ({'label':'Past minute',
                 'points':waterLevelChangeRate1Minutes})
  lines.append ({'label':'Past 5 minutes',
                 'points':waterLevelChangeRate5Minutes})
  lines.append ({'label':'Past 15 minutes',
                 'points':waterLevelChangeRate15Minutes})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotLongWaterLevelHighLows():
  """plot the long water level high lows

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  plotName = "Long Water Level High Lows"
  numberToPlot = 60
  times = longWaterLevelHiLoTicks
  yLabel = "Water Level (in)"
  lines = []
  print "pLWLHL lines:", len(lines),\
      " highs:", len( longWaterLevelHighs.values),\
      " lows:", len( longWaterLevelLows.values)
  lines.append ({'label':longWaterLevelHighs.name,
                 'points':longWaterLevelHighs.values})
  lines.append ({'label':longWaterLevelLows.name,
                 'points':longWaterLevelLows.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWaveHeights():
  """plot the raw wave heights for the past 30 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Raw Waves ##NEW##"
  numberToPlot = 5*60 * config.SAMPLES_PER_SECOND
  times = levelTicks
  yLabel = "Wave height (in)"
  lines = []
  lines.append ({'label':waveHeights.name,
                 'points':waveHeights.values})
  lines.append ({'label':waveHeightAves.name,
                 'points':waveHeightAves.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWaveHeightStats():
  """plot the wave height statistics the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Raw Wave Statistics ##NEW##"
  numberToPlot = 15*60 * config.SAMPLES_PER_SECOND
  times = levelTicks
  yLabel = "Coefficient of Variation"
  lines = []
  lines.append ({'label':waveHeightVariations.name,
                 'points':waveHeightVariations.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)

  print "Water Level High ##NEW##", rawWaterLevelHighLow.high,\
     " Low", rawWaterLevelHighLow.low
  print "Wave Heights High ##NEW##", waveHeightHighLow.high,\
     " Low", waveHeightHighLow.low
  rawWaterLevelHighLow.reset()
  waveHeightHighLow.reset()


def plotRawWavePeaks():
  """plot the wave peaks the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Peaks ##NEW##"
  numberToPlot = 15*60
  times = waveTimes.values
  yLabel = "Wave Peaks (in)"
  lines = []
  lines.append ({'label':wavePeaks.name, 'points':wavePeaks.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWavePeriods():
  """plot the wave periods the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Period ##NEW##"
  numberToPlot = 15*60
  times = waveTimes.values
  yLabel = "Wave Period (s)"
  lines = []
  lines.append ({'label':wavePeriods.name, 'points':wavePeriods.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWavePower():
  """plot the raw wave power the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Power ##NEW##"
  numberToPlot = 15*60
  times = waveTimes.values
  yLabel = "Wave Power (nw?)"
  lines = []
  lines.append ({'label':wavePowers.name, 'points':wavePowers.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWavePowerVariations():
  """plot the wave power variations the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Power Variations ##NEW##"
  numberToPlot = 15*60
  times = waveTimes.values
  yLabel = "Wave Power (nw?)"
  lines = []
  lines.append ({'label':wavePowerVariations.name,
                 'points':wavePowerVariations.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


  #plotName = "Raw Wave Statistics 2 ##NEW##"
  #numberToPlot = 15*60
  #times = levelTicks
  #yLabel = "Coefficient of Variation"
  #lines = []
  #lines.append ({'label':waveHeightVariations2.name,\
  #               'points':waveHeightVariations2.values})
  #print plotName, numberToPlot, "times: ", len(times),\
  #    yLabel, "lines: ", len(lines)
  #plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)

  #print "Water Level High 2 ##NEW##", rawWaterLevelHighLow.high,
  #      " Low", rawWaterLevelHighLow.low
  #print "Wave Heights High 2 ##NEW##", waveHeightHighLow.high,\
  #      " Low", waveHeightHighLow.low
  #rawWaterLevelHighLow.reset()
  #waveHeightHighLow.reset()


def plotRawWavePeaks2():
  """plot the raw wave peaks the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Peaks 2 ##NEW##"
  numberToPlot = 15*60
  times = waveTimes2.values
  yLabel = "Wave Peaks (in)"
  lines = []
  '''DEBUG TEMPORARY DISABLE
  lines.append ({'label':wavePeaks2.name, 'points':wavePeaks2.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)
  '''


def plotRawWavePeriods2():
  """plot the raw wave periods the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Period 2 ##NEW##"
  numberToPlot = 15*60
  times = waveTimes2.values
  yLabel = "Wave Period (s)"
  lines = []
  lines.append ({'label':wavePeriods2.name, 'points':wavePeriods2.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWavePower2():
  """plot the raw wave power the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Power 2 ##NEW##"
  numberToPlot = 15*60
  times = waveTimes2.values
  yLabel = "Wave Power (nw?)"
  lines = []
  lines.append ({'label':wavePowers2.name, 'points':wavePowers2.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawWavePowerVariations2():
  """plot the wave power variations the past 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "Wave Power Variations 2 ##NEW##"
  numberToPlot = 15*60
  times = waveTimes2.values
  yLabel = "Wave Power (nw?)"
  lines = []
  lines.append ({'label':wavePowerVariations2.name,
                 'points':wavePowerVariations2.values})
  printPlot (plotName, numberToPlot, times, yLabel, lines)
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotRawLevel():
  """plot the raw water level for the past 10 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  #waterLevel.plotLevels( DUR_30_MINUTES, "Raw Water Level")

  plotName = "Raw Water Levels"
  numberToPlot = 10*60* config.SAMPLES_PER_SECOND
  times = levelTicks
  yLabel = "Water Level (in)"
  lines = []
  lines.append ({'label':rawWaterLevels.name, 'points':rawWaterLevels.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotWaveHeight():
  """Plot the raw wave heights

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  waterLevel.plotWaveHeights(
      DUR_1_MINUTE * config.SAMPLES_PER_SECOND, "Raw Wave Height")
  waterLevel.freshen ( (DUR_1_MINUTE -1) * config.SAMPLES_PER_SECOND)


def plotRawPeaks():
  """plot the raw wave peaks

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  waves.plotWavePeaks( DUR_30_MINUTES, "Wave Peaks")


def plotRawPeriods():
  """plot raw wave periods

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  waves.plotWavePeriods( DUR_30_MINUTES, "Wave Periods")


def plotRawPower():
  """plot the power of raw waves

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  print "plotting power"
  waves.plotWavePower( DUR_30_MINUTES, "Wave Power")
  waves.freshen ( DUR_30_MINUTES) 


def plotLongWaterLevel1():
  """plot the long term water level for the past hour

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  #longWaterLevel.plotLevels( 60, "Hourly Water Level") # saved once a minute

  plotName = "Hourly Water Levels"
  numberToPlot = 60 # minute ticks
  times = longWaterTicks
  yLabel = "Water Level (in)"
  lines = []
  lines.append ({'label':longWaterLevels.name,
                 'points':longWaterLevels.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)


def plotLongWaterLevel8():
  """plot the long term water level for the past 8 hours

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plotName = "8-Hour Water Levels"
  numberToPlot = 8*60 # minute ticks
  times = longWaterTicks
  yLabel = "Water Level (in)"
  lines = []
  lines.append ({'label':longWaterLevels.name,
                 'points':longWaterLevels.values})
  plot.plotCommon (plotName, numberToPlot, times, yLabel, lines)

  longWaterLevels.freshen( 1*60)


def plotCluster():
  """plot the wave clusters

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  ###Plot the raw wave power.###
  print "plotting cluster (raw wave power?"
  waves.cluster.plot ( DUR_30_MINUTES, "Wave Cluster")
  waves.cluster.freshen ( DUR_30_MINUTES) 


def reportCluster():
  """report on the wave clusters in the past __ minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  waves.cluster.report( currentTick)


def doFFTs():
  """do an FFT on each of the resampled data streams

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  spectraTimeSeries.evaluate( currentTick)
  sendFftSamples()


def sendFftSamples():
  """send FFT samples to the InfluxDB server

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  # send measurements to the influxdb

  offsetTick = currentTick + tickDiff # offset to yesterday for now

  index = 0
  json_body = []
  # should only do the following once...
  numberOfLengths = len( config.BOAT_LENGTHS)
  
  for spectrum in spectraTimeSeries.spectra:
    if len( spectrum.responses) >= 1:
      if index < numberOfLengths: # and index < 5: #== 0:
        json_body.append (
          {
            "measurement" : "boatResponse",
            "tags" : {
              "boatLength" : config.BOAT_LENGTHS[ index]
            },
            "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                      datetime.datetime.fromtimestamp(offsetTick)),
            "fields" : {
              "response" : spectrum.responses[-1]
            }
          }
        )
      else:
        json_body.append(
          {
            "measurement" : "periodicResponse",
            "tags" : {
              "period" : config.TARGET_PERIODS[ index - numberOfLengths]
            },
            "time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
                      datetime.datetime.fromtimestamp(offsetTick)),
            "fields" : {
              "response" : spectrum.responses[-1]
            }
          }
        )
    index = index + 1
  if json_body is not []:
    #print json.dumps( json_body)
    if not client.write_points(json_body):
      print "Not updating database"
    #else:
    #  print '.',
      


def plotWakeSpectra15():
  """plot the wake spectra over the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plot.plotFrequencyResponse( spectraTimeSeries,
                              config.WAKE_START, config.WAKE_END,
                              DUR_15_MINUTES, "Wake Response")


def plotWaveSpectra15():
  """plot the wave spectra over the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plot.plotFrequencyResponse( spectraTimeSeries,
                              config.WAVE_START, config.WAVE_END,
                              DUR_15_MINUTES, "Wave Response")
 

def plotWakeSpectra1():
  """plot the wake spectra over the last minute

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  plot.plotFrequencyResponse( spectraTimeSeries,
                              config.WAKE_START, config.WAKE_END,
                              DUR_1_MINUTE, "Wake Response Details",
                              verticalSpacing=0, maxPerPage=4)


def schedClusterEnd( someFunction, currentTime, period):
  """schedule the end of a cluster

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  return mainSched.schedule( someFunction, currentTime, 0, period)


def unschedClusterEnd( taskID):
  """unschedule the end of a cluster

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  mainSched.unschedule( taskID)


#pylint: disable=too-many-locals
#pylint: disable=too-many-statements
#pylint: disable=global-statement
def test():
  """tests the functions of this module

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  global outChan
  global inChan
  global currentTick
  global tickDiff
  global client

  global levelTicks
  global waterLevel
  global waves
  global waves2
  global sampleTimeSeries
  global spectraTimeSeries

  global rawWaterLevels
  global rawWaterLevelHighLow
  global longWaterLevelAve
  global longWaterLevelAves
  global longWaterLevelStats
  global longWaterLevelVariations
  global longWaterLevelHighLow
  global longWaterLevelHighs
  global longWaterLevelLows
  global longWaterTicks
  global longWaterLevels
  global longWaterLevelHiLoTicks
  global waterLevelChangeRate1Minutes
  global waterLevelChangeRate5Minutes
  global waterLevelChangeRate15Minutes
  global medWaterLevelAve
  global waveBaselines
  global waveHeights
  global waveHeightHighLow
  global waveHeightLowPass
  global waveHeightStats
  global waveHeightAve
  global waveHeightAves
  global waveHeightVariations

  global waveTimes
  global wavePeaks
  global wavePeriods
  global wavePowers
  global wavePowerStats
  global wavePowerVariations

  global waveTimes2
  
  global wavePeriods2
  global wavePowers2
  global wavePowerStats2
  global wavePowerVariations2


  # do some initialization stuff
  inputFileName, outputFileBaseName = processCommandLineArguments()

  # initialize input channel
  inChan = inputchan.InputChannel( inputFileName)
  if not inChan.success:
    print errorMessage
    sys.exit(1)
  openFileHandles = []
  openFileHandles.append( inChan)

  # initialize output channel
  outChan = report.ReportChannel( outputFileBaseName)
  #outChan = report.ReportChannel( "")
  openFileHandles.append( outChan)

  # initialize influxdb channel
  client = InfluxDBClient(host='localhost', port=8086)
  databaseName = "waterlevel"
  if databaseName not in client.get_list_database():
    client.create_database( databaseName)
    client.create_retention_policy("keep forever", "INF", 1,
            database=databaseName)

  client.switch_database( databaseName)


  # initialize data structures
  levelTicks = []

  setupGracefulExit( openFileHandles)

  currentTick, currentLevel = inChan.getWaterLevel( currentTick)

  walltime = datetime.datetime.now()
  # find number of days between measurement and now
  daydiff = (walltime - datetime.datetime.fromtimestamp(currentTick)).days
  tickDiff = daydiff * 24 * 3600 # offset to yesterday for now

  waterLevel = level.Level( "Water Level", currentLevel, currentTick, 3.0,
                            [   ("Short", 2),     # 2 samples
                                ("Medium", 6*30), # 6 seconds
                                ("Long", 60*30)] # 1 minute
                          )

  ###longWaterLevel = level.Level( "Long Water Level", currentLevel,
  ###                              currentTick, .10, [])

  findWave = findwave.FindWave() # determine wave peaks and periods

  instantWaveHeight = 0
  waves = rawwaves.RawWaves( currentTick) # wave height time series
                                          # (not sure this is used...)
  ###NEW v
  longWaterTicks = []
  longWaterLevelHiLoTicks = []
  longWaterLevels = series.Series( "Long Water Level", "in")
  waves2 = rawwaves.RawWaves( currentTick) # filtered wave height time series
  findWave2 = findwave.FindWave() # determine need wave peaks
  rawWaterLevels = series.Series( "Raw Water Level", "in")
  rawWaterLevelHighLow = highlow.HighLow( "Water Level Limits", "in")
  longWaterLevelAve = average.Average( "Averaged Water Level", "in",
                                       config.LONG_AVE_SAMPLES)
  longWaterLevelAves = series.Series( "Average Water Level", "in")
  longWaterLevelStats =  stats2.Stats2( "Average Water Level", "in", 20)
  longWaterLevelVariations = series.Series( "Ave Water Level Variations", "")
  longWaterLevelHighLow = highlow.HighLow( "Average Water Level Limits", "in")
  longWaterLevelHighs = series.Series( "Average Water Level Highs", "in")
  longWaterLevelLows = series.Series( "Average Water Level Lows", "in")
  waterLevelChangeRate1Minutes = []
  waterLevelChangeRate5Minutes = []
  waterLevelChangeRate15Minutes = []
  medWaterLevelAve = average.Average( "Wave Baseline Water Level", "in",
                                      config.MEDIUM_AVE_SAMPLES)
  waveBaselines = series.Series( "Wave Baseline", "in")
  waveHeights = series.Series( "Wave Height", "in")
  waveHeightAve = average.Average( "Average Wave Height", "in", 20)
  waveHeightAves = series.Series( "Average Wave Height", "in")
  waveHeightHighLow = highlow.HighLow( "Wave Height Limits", "in")
  waveHeightLowPass = lowpass.LowPass( 2) # number of wave cycles
    #lowpass = 2 eliminates 80% of waves, = 4 eliminates 94% in a light chop
    # 4 reduces sampling to 4/30 or 1 every 120 ms, that is still 8/sec
  waveHeightTrap = trap.Trap( 4, -1, "in", 30,
                              name="Wave Height",
                              port=outChan)
  waveHeightStats = stats2.Stats2( "Wave Height", "in", 20)
  waveHeightVariations = series.Series( "Wave Height Variations", "in")

  waveTimes = series.Series( "Wave Times", "s")
  wavePeaks = series.Series( "Wave Peaks", "in")
  wavePeriods = series.Series( "Wave Periods", "s")
  wavePowers = series.Series( "Wave Power", "nw?")
  wavePowerStats = stats2.Stats2( "Wave Power", "nw?", 20)
  wavePowerVariations = series.Series( "Wave Power Variations", "")
  
  waveTimes2 = series.Series( "Wave Times2", "s")
  wavePeaks2 = series.Series( "Wave Peaks2", "in")
  wavePeriods2 = series.Series( "Wave Periods2", "s")
  wavePowers2 = series.Series( "Wave Power2", "nw?")
  wavePowerStats2 = stats2.Stats2( "Wave Power Stats22", "nw?", 20)
  wavePowerVariations2 = series.Series( "Wave Power Variations2", "")
  
  ###NEW ^

  # initialize resampling time series and related spectral response time series
  sampleTimeSeries = resamples.Resamples()
  spectraTimeSeries = spectra.Spectra()

  for boatLength in config.BOAT_LENGTHS:
    # convert boat length to cyclePeriod
    waveSpeed = math.sqrt (config.GRAVITY_CONSTANT * boatLength / 2 /math.pi)
    # in ft/s
    cyclePeriod = boatLength / waveSpeed # s
    legend = "{0}' boat".format( boatLength) #'
    #pylint: disable=E1305
    print "Boat length {0:n} has period {1:.2f} and speed {2:.2f}".format(
       boatLength,
       cyclePeriod,
       waveSpeed)
    #pylint: enable=E1305

    # create wave height resample object inside the resamples object
    sampleTimeSeries.resamples.append( resamples.Resample(
        cyclePeriod, currentTick, instantWaveHeight, legend))

    # create spectrum object inside the spectra object
    #   including a pointer back to the corresponding resample object
    spectraTimeSeries.spectra.append ( spectra.Spectrum(
        sampleTimeSeries.resamples[-1]))

  for period in config.TARGET_PERIODS:
    legend = "{}s period".format( period)

    # create wave height resample object inside the resamples object
    sampleTimeSeries.resamples.append( resamples.Resample(
        period, currentTick, instantWaveHeight, legend))

    # create spectrum object inside the spectra object
    #   including a pointer back to the corresponding resample object
    spectraTimeSeries.spectra.append ( spectra.Spectrum(
        sampleTimeSeries.resamples[-1]))
 

  # schedule periodic tasks
  mainSched.schedule( updateLongWaterLevel, currentTick, EVERY_MINUTE, 0)
  mainSched.schedule( updateLongWaterLevelHighLow, currentTick,
                      EVERY_MINUTE, 0) # s/b longer
  mainSched.schedule( doFFTs, currentTick, EVERY_200_MSEC, 0)
  # want to plot the cleaned water level over time: every hour, every 8 hours,
  # daily. this needs less precision.. maybe a sample once a minute
  #mainSched.schedule( plotRawLevel, currentTick, EVERY_MINUTE, 0)
  mainSched.schedule( plotWaveHeight, currentTick, EVERY_MINUTE, 0)
  mainSched.schedule( plotRawPeaks, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( plotRawPeriods, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( plotRawPower, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( plotWakeSpectra15, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( plotWaveSpectra15, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( plotLongWaterLevelVariation, currentTick,
                      EVERY_15_MINUTES, 0)
  mainSched.schedule( plotLongWaterLevelHighLows, currentTick,
                      EVERY_15_MINUTES, 0)
  mainSched.schedule( plotWaterLevelChangeRates, currentTick,
                      EVERY_15_MINUTES, 0)
  mainSched.schedule( plotRawLevel2, currentTick, EVERY_MINUTE, 0)
  mainSched.schedule( plotRawWaveHeightStats, currentTick, EVERY_MINUTE, 0)#NEW

  mainSched.schedule( plotRawWaveHeights, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePeaks, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePeriods, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePower, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePowerVariations, currentTick, EVERY_MINUTE, 0)

  mainSched.schedule( plotRawWavePeaks2, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePeriods2, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePower2, currentTick, EVERY_MINUTE, 0) ###NEW
  mainSched.schedule( plotRawWavePowerVariations2, currentTick, EVERY_MINUTE,0)

  mainSched.schedule( plotWakeSpectra1, currentTick, EVERY_MINUTE, 0)
  #mainSched.schedule( plotLongWaterLevel1, currentTick, EVERY_HOUR, 0)
  #mainSched.schedule( plotLongWaterLevel8, currentTick, EVERY_8_HOURS, 0)
  mainSched.schedule( plotLongWaterLevel8, currentTick, EVERY_HOUR, 0)
  mainSched.schedule( plotCluster, currentTick, EVERY_15_MINUTES, 0)
  # do reports last as they contain resets
  #mainSched.schedule( waterLevelReport15, currentTick, EVERY_15_MINUTES, 0)
    # has a list index out of range error
  mainSched.schedule( longWaterLevelReport15, currentTick, EVERY_15_MINUTES, 0)
  mainSched.schedule( waveReport15, currentTick, EVERY_15_MINUTES, 0)
  # generate raw wave statistics report

  print "Initialization done"
  print "sampleTimeSeries",sampleTimeSeries
  print "spectraTimeSeries",spectraTimeSeries

  ###MAIN LOOP
  #for _ in range (0, 3*60*60*30): #200000000): # limited test run
  while True: # until stopped...
    lastTick = currentTick
    lastWaveHeight = instantWaveHeight
    currentTick, currentLevel = inChan.getWaterLevel( currentTick)
    #currentTick, currentLevel = inChan.readLevel( currentTick)

    levelTicks.append( currentTick)
    ###OLDv
    # save the input to a .csv file
    #outChan.writeln( measurementsToCSV( measurement))

    ###waterLevel.analyze (currentTick, currentLevel, outChan)
    #-times, levels, stats, watch 
    ###OLD^
    ###NEW v
    rawWaterLevels.append( currentLevel)
    rawWaterLevelHighLow.append( currentLevel)

#this should only happen once a minute...
    longAve = longWaterLevelAve.update( currentLevel)
    longWaterLevelAves.append(longAve)

    waveBaseline = medWaterLevelAve.update( currentLevel)
    waveBaselines.append( waveBaseline)

    instantWaveHeight = currentLevel - waveBaseline
    waveHeights.append( instantWaveHeight)
    waveHeightHighLow.append( instantWaveHeight)
    waveHeightTrap.append( instantWaveHeight)
    instantWaveHeightAve = waveHeightAve.update( instantWaveHeight)
    waveHeightAves.append( instantWaveHeightAve)
    waveHeightStats.append( instantWaveHeight)
    waveHeightVariations.append( waveHeightStats.coefficientOfVariation)

    waveHeightAve2 = waveHeightLowPass.append( instantWaveHeight)
    sendRawLevel2( currentTick, currentLevel, waveBaseline, longAve,
        instantWaveHeight,
        waveHeightAve2)


    # this really doesn't do what you want:
    #   since this is instantaneous, the mean should be = 0.
    #   This makes the coefficientOfVariation get really big, since it is
    #   StdDev/mean.
    ###NEW ^

    ###OLDv
    #waveHeight = waterLevel.waveHeights[-1]
    #waveHeight = instantWaveHeight
    if findWave.findWave( currentTick, instantWaveHeight):
      peak = findWave.wavePeakToPeak
      period = findWave.wavePeriod
      power = findWave.wavePower
      waves.analyze( currentTick, peak, period, power, outChan)
      ###OLD^

      ###NEW
      waveTimes.append( currentTick)
      wavePeaks.append( peak)
      wavePeriods.append( period)
      wavePowers.append( power)
      wavePowerStats.append( power)
      wavePowerVariations.append( wavePowerStats.coefficientOfVariation)
      ###NEW

    ###NEW
    if findWave2.findWave( currentTick, waveHeightAve2):
      peak = findWave2.wavePeakToPeak
      period = findWave2.wavePeriod
      power = findWave2.wavePower
      waves2.analyze( currentTick, peak, period, power, outChan)
      waveTimes2.append( currentTick)
      wavePeaks2.append( peak)
      wavePeriods2.append( period)
      wavePowers2.append( power)
      wavePowerStats2.append( power)
      wavePowerVariations2.append( wavePowerStats2.coefficientOfVariation)
    
      sendWave( currentTick, peak, period, power)
    ###NEW

    # resample wave height for spectral analysis
    sampleTimeSeries.evaluate ( currentTick, instantWaveHeight,
                                lastTick, lastWaveHeight)

    # do the timed jobs that are due
    mainSched.execute(currentTick)

  print "longWaterLevelAve", longWaterLevelAve
  print
  print "waveHeightAve",  waveHeightAve
  print
  print "waveHeightHighLow", waveHeightHighLow
  print
  print "waveHeightTrap", waveHeightTrap
  print
  print "waveHeightStat", waveHeightStats
  #pylint: enable=too-many-statements
  #pylint: enable=global-statement
  #pylint: enable=too-many-locals

if __name__ == "__main__":
  # execute only if run as a script
  test()
#pylint: enable=too-many-lines
