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

3 Partial conversion to InfluxDB and Grafana show their benefits. Now need to limit
the use of Series as the program eventually consumes all RAM...

3//drop> main.py:  longWaterLevels = series.Series( "Long Water Level", "in")
3//drop> main.py:  longWaterLevelAves = series.Series( "Average Water Level", "in")
3//drop> main.py:  longWaterLevelVariations = series.Series( "Ave Water Level Variations", "")
3//drop> main.py:  longWaterLevelHighs = series.Series( "Average Water Level Highs", "in")
3//drop> main.py:  longWaterLevelLows = series.Series( "Average Water Level Lows", "in")
3//drop> main.py:  rawWaterLevels = series.Series( "Raw Water Level", "in")
3>drop> main.py:  sampleTimeSeries = resamples.Resamples()
3>drop> main.py:  sampleTimeSeries.resamples.append( resamples.Resample(
3>drop> main.py:  spectraTimeSeries = spectra.Spectra()
3>drop> main.py:  spectraTimeSeries.spectra.append ( spectra.Spectrum(
3//drop> main.py:  waveBaselines = series.Series( "Wave Baseline", "in")
3//drop> main.py:  waveHeights = series.Series( "Wave Height", "in")
3//drop> main.py:  waveHeightAves = series.Series( "Average Wave Height", "in")
3//drop> main.py:  waveHeightVariations = series.Series( "Wave Height Variations", "in")
3//drop> main.py:  waveTimes = series.Series( "Wave Times", "s")
3//drop> main.py:  waveTimes2 = series.Series( "Wave Times2", "s")
3//drop> main.py:  wavePeaks = series.Series( "Wave Peaks", "in")
3//drop> main.py:  wavePeaks2 = series.Series( "Wave Peaks2", "in")
3//drop> main.py:  wavePeriods = series.Series( "Wave Periods", "s")
3//drop> main.py:  wavePeriods2 = series.Series( "Wave Periods2", "s")
3//drop> main.py:  wavePowers = series.Series( "Wave Power", "nw?")
3//drop> main.py:  wavePowers2 = series.Series( "Wave Power2", "nw?")
3//drop> main.py:  wavePowerVariations = series.Series( "Wave Power Variations", "")
3//drop> main.py:  wavePowerVariations2 = series.Series( "Wave Power Variations2", "")

3>drop> main.py:  sampleTimeSeries.resamples[-1]))

4 need to find things that use the last element of a list [-1]
4//drop>cluster.py:      endTime = self.events[-1]["time"]
4//drop>level.py:      waveHeight = level - self.stats.averages[1][-1]
4//drop>level.py:      # waveHeight = level - self.stats.averages[1][-1]
4//drop>level.py:      #waveHeight = self.stats.averages[0][-1] - self.stats.averages[1][-1]
4//drop>level.py:      # was using waveHeight = shortAves[-1] - longAves[-1]
4//drop>main.py:  ###longWaterLevel.analyze( currentTick, waterLevel.stats.averages[2][-1],
4//drop>main.py:    waterLevelChangeRate1Minute = ( longWaterLevels.values[-1] -
4//drop>main.py:    waterLevelChangeRate5Minute = ( longWaterLevels.values[-1] -
4//drop>main.py:    waterLevelChangeRate15Minute = ( longWaterLevels.values[-1] -
4//drop>main.py:              "response" : spectrum.responses[-1]
4//drop>main.py:              "response" : spectrum.responses[-1]
4//drop>main.py:              "response" : spectrum.responses[-1]
4//drop>main.py:              "response" : spectrum.responses[-1]
4>drop>main.py:        sampleTimeSeries.resamples[-1]))
4>drop>main.py:        sampleTimeSeries.resamples[-1]))
4//drop>main.py:    #waveHeight = waterLevel.waveHeights[-1]
4//drop>plot.py:  baseTime = times [-1]
4//drop>plot.py:    path = fileTimePng (baseName, times[-1])
4//drop>plot.py:    timeFirstName = fileTimeFirstPng (baseName, times[-1])
4//drop>plot.py:    path = fileTimePng (baseName, times[-1])
4//drop>plot.py:    timeFirstName = fileTimeFirstPng (baseName, times[-1])
4//drop>plot.py:  baseTime = pSpectra.times[-1]
4//drop>plot.py:        path = fileTimePng (name, pSpectra.times[-1],
4//drop>plot.py:        path = fileTimePng (name, pSpectra.times[-1])
4//drop>rawwaves.py:    #                           self.powers.averages[1][-1])
4>drop>spectra1.py:    specs.spectra.append ( Spectrum( samples.resamples[-1]))
4>drop>spectra.py:    specs.spectra.append ( Spectrum( samples.resamples[-1]))
4//drop>stats.py:        aveage.append( util.runningAverage( average[-1], value,
4//drop>stats.py:            self.averages[0][-1] * self.averages[0][-1],
4//drop>stats.py:        diff = self.sumOfSquares -(self.averages[1][-1] * self.averages[1][-1])
4//drop>stats.py:        self.coefficientOfVariations.append( self.standardDeviations[-1] /\
4//drop>stats.py:            self.averages[1][-1] * 100) # percent
4//drop>stats.py:        mean = average[-1]
4//drop>stats.py:        mean = self.averages[1][-1] # use updated medium for the mean
4//drop>stats.py:          self.averages[0][-1],
4//drop>stats.py:          self.standardDeviations[-1],
4//drop>stats.py:          self.coefficientOfVariations[-1])
4//drop>stats.py:      print "stats mean:{0:.2f}".format( self.averages[0][-1])
4//drop>stats.py:        "{:5.2f}".format(self.values[-1])) )
4//drop>stats.py:          "{:5.2f}".format( self.averages[i][-1])) )
4//drop>stats.py:          "{:5.2f}".format( self.standardDeviations[-1]) ))
4//drop>stats.py:          "{:5.2f}".format( self.coefficientOfVariations[-1]) ))
4>//drop>watch.py:  levelWatch.report( times[-1], outChan) # print watch stats

5 // get rid of most (all?) of the plot stuff

6 add plotting of statistics stuff...anything that uses a Stats object or Average object

7 add High/low registers, plotting and candlestick plots
  add hilo for water level hourly daily, weekly
  wavePeakHighs ... wavePowerHighs   hourly, daily, weekly
  wakePeakHighs ... wakePowerHighs   hourly, daily, weekly

8 watches can be greatly simplified, they should just check against a threshold with
amount of hysteresis.

9 consolodate routines that communicate with grafana/influxdb into a module


"""
#### IMPORTS ####

import sys
import datetime
import math
import json

import sched
import config
import cluster
import dominant
import findwave
import inputchan
import influx
import level
#import plot
import report
import resamples
import spectra
#import stats
import wave


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
EVERY_WEEK =      24 * 60 * 60 # do every day and test day of week
EVERY_MONTH =     24 * 60 * 60 # do every day and test day of month

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
mainSched = sched.Schedule()

waterLevel = None
longWaterTicks = None
longWaterLevelHiLoTicks = None
rawWave = None
dominantPeriod = None
sampleTimeSeries = None
spectraTimeSeries = None

longWaterLevel = None
longWaterLevelAve = None
longWaterLevelStats = None
longWaterLevelHourlyHighLow = None
longWaterLevelDailyHighLow = None
longWaterLevelWeeklyHighLow = None
longWaterLevelMonthlyHighLow = None
waterLevelChangeRate1Minutes = None
waterLevelChangeRate5Minutes = None
waterLevelChangeRate10Minutes = None
waterLevelChangeRate15Minutes = None
medWaterLevelAve = None
waveHeightLowPass = None
waveHeightHourlyHighLow = None
waveHeightDailyHighLow = None
waveHeightWeeklyHighLow = None
waveHeightMonthlyHighLow = None
waveHeightAve = None
waveHeightStats = None
rawWave2 = None
wavePowerStats = None
wavePowerStats2 = None
waveCluster = None


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


def reportCluster( currentTime):
  """report on the wave clusters in the past config.CLUSTER_WINDOW

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  global cluster
  global currentTick

  #clusterReport( currentTick)
  influx.sendMeasurementLevel( currentTick, "cluster", "energy", waveCluster.energy)
  influx.sendMeasurementLevel( currentTick, "cluster", "distance", waveCluster.distance)
  waveCluster.report( currentTick)
  waveCluster.reset( currentTick)


def updateLongWaterLevel( currentTime):
  """update the long water level time series (once a minute)

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  global longWaterLevels
  from influx import influxWrites

  longAve = longWaterLevelAve.average
  print "{0:%Y-%m-%dT%H:%M:%S.%f-0400 updateLongWaterLevels {1}}"\
      .format( datetime.datetime.fromtimestamp(currentTick),
               influx.influxWrites)
  influx.influxWrites = 0
  longWaterLevels.append( longAve)
  longWaterLevelHourlyHighLow.append( longAve)
  longWaterLevelDailyHighLow.append( longAve)
  longWaterLevelWeeklyHighLow.append( longAve)
  longWaterLevelMonthlyHighLow.append( longAve)

  # calculate the water level change rates
  lenLevels = len( longWaterLevels)
  if lenLevels > 1+1:
    waterLevelChangeRate1Minute = ( longAve -
                                    longWaterLevels[-(1+1)]) * 60
  else:
    waterLevelChangeRate1Minute = 0

  if lenLevels > 1+5:
    waterLevelChangeRate5Minute = ( longAve -
                                    longWaterLevels[-(1+5)]) * 12
  else:
    waterLevelChangeRate5Minute = 0

  if lenLevels > 1+10:
    waterLevelChangeRate10Minute = ( longAve -
                                     longWaterLevels[-(1+10)]) * 6
  else:
    waterLevelChangeRate10Minute = 0

  if lenLevels > 1+15:
    waterLevelChangeRate15Minute = ( longAve -
                                     longWaterLevels[-(1+15)]) * 4
  else:
    waterLevelChangeRate15Minute = 0

  if lenLevels > 30:
    longWaterLevels = longWaterLevels[-15:]

  # send long term water levels to InfluxDB for graphing
  influx.sendMeasurementLevel( currentTime,
                               "waterLevel",
                               "longAve",
                               longAve)
  influx.sendMeasurementLevel( currentTime,
                               "waterLevel",
                               "changeRate1Minute",
                               waterLevelChangeRate1Minute)
  influx.sendMeasurementLevel( currentTime,
                               "waterLevel",
                               "changeRate5Minute",
                               waterLevelChangeRate5Minute)
  influx.sendMeasurementLevel( currentTime,
                               "waterLevel",
                               "changeRate10Minute",
                               waterLevelChangeRate10Minute)
  influx.sendMeasurementLevel( currentTime,
                               "waterLevel",
                               "changeRate15Minute",
                               waterLevelChangeRate15Minute)


def waterLevelReport15( currentTime):
  """report on the water level in the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  ###Generate the 15 minute water level report.###
  waterLevel.report( currentTime, outChan)
  waterLevel.watch.reset( currentTick)


def longWaterLevelHourlyReport( currentTime):
  """report on the long term water level in the last hour

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  longWaterLevelHourlyHighLow.report( currentTime, outChan)
  longWaterLevelHourlyHighLow.reset()


def longWaterLevelDailyReport( currentTime):
  """report on the long term water level in the last day

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  longWaterLevelDailyHighLow.report( currentTime, outChan)
  longWaterLevelDailyHighLow.reset()


def longWaterLevelWeeklyReport( currentTime):
  """report on the long term water level in the last week

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """
  if datetime.datetime.fromtimestamp(currentTick).weekday == 0:
    longWaterLevelWeeklyHighLow.report( currentTime, outChan)
    longWaterLevelWeeklyHighLow.reset()


def longWaterLevelMonthlyReport( currentTime):
  """report on the long term water level in the past month

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  if datetime.datetime.fromtimestamp(currentTick).day == 1:
    longWaterLevelMonthlyHighLow.report( currentTime, outChan)
    longWaterLevelMonthlyHighLow.reset()


def waveReport15( currentTime):
  """report on wave activity in the last 15 minutes

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  rawWave.report( currentTime, outChan)
  rawWave.peakwatch.reset( currentTime) # other periods will want their own watch
  rawWave.periodwatch.reset( currentTime)
  rawWave.powerwatch.reset( currentTime) 


def doFFTs( currentTime):
  """do an FFT on each of the resampled data streams

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  spectraTimeSeries.evaluate( currentTime)
  sendLimitedFftSamples()

  sampleTimeSeries.freshen() # prescribed amount
  spectraTimeSeries.freshen( 10 * 5) # ten seconds worth on 200ms..


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

  index = 0
  # should only do the following once...
  numberOfBoatLengths = len( config.BOAT_LENGTHS)
  
  for spectrum in spectraTimeSeries.spectra:
    if len( spectrum.responses) >= 1:
      response = spectrum.responses[-1]
      if index < numberOfBoatLengths:
        boatLength = config.BOAT_LENGTHS[ index]
        cyclePeriod = math.sqrt (boatLength / config.GRAVITY_CONSTANT/\
                2 /math.pi) # ft/s
        influx.sendTaggedMeasurementLevel( currentTick,
                                           "spectrum",
                                           "boatLength",
                                           boatLength,
                                           "boatResponse",
                                           response)
        '''
        influx.sendTaggedMeasurementLevel( currentTick - cyclePeriod,
                                           "spectrum",
                                           "boatLength",
                                           boatLength,
                                           "startBoatResponse",
                                           response)
        '''
      else:
        period = config.TARGET_PERIODS[ index - numberOfBoatLengths]
        influx.sendTaggedMeasurementLevel( currentTick,
                                           "spectrum",
                                           "period",
                                           period,
                                           "periodicResponse",
                                           response)
        '''
        influx.sendTaggedMeasurementLevel( currentTick - period,
                                           "spectrum",
                                           "period",
                                           period,
                                           "startPeriodicResponse",
                                           response)
        '''
    index = index + 1
      

def sendLimitedFftSamples():
  """send limited FFT samples to the InfluxDB server

  Args:
    None
  
  Returns:
    None
  
  Raises:
    None
  """

  # send measurements to the influxdb

  index = 0
  # should only do the following once...
  numberOfBoatLengths = len( config.BOAT_LENGTHS)
  boatResponse = 0
  spectraResponse = 0
  boatLength = 0
  period = 0
  
  # find the dominant response by wavelength and period
  for spectrum in spectraTimeSeries.spectra:
    if len( spectrum.responses) >= 1:
      response = spectrum.responses[-1]
      if index < numberOfBoatLengths:
        if response > boatResponse:
          boatResponse = response
          boatLength = config.BOAT_LENGTHS[ index]
          cyclePeriod = math.sqrt (boatLength / config.GRAVITY_CONSTANT/\
                2 /math.pi) # ft/s
      else:
        if response > spectraResponse:
          spectraResponse = response
          period = config.TARGET_PERIODS[ index - numberOfBoatLengths]
    index = index + 1
  influx.sendTaggedMeasurementLevel( currentTick,
                                     "spectrum",
                                     "boatLength",
                                     boatLength,
                                     "boatResponse",
                                     boatResponse)
  influx.sendTaggedMeasurementLevel( currentTick,
                                     "spectrum",
                                     "period",
                                     period,
                                     "periodicResponse",
                                     spectraResponse)
  if config.SEND_START_RESPONSES:
    influx.sendTaggedMeasurementLevel( currentTick - cyclePeriod,
                                       "spectrum",
                                       "boatLength",
                                       boatLength,
                                       "startBoatResponse",
                                       boatResponse)
    influx.sendTaggedMeasurementLevel( currentTick - period,
                                       "spectrum",
                                       "period",
                                       period,
                                       "startPeriodicResponse",
                                       spectraResponse)
  dominantPeriod.update( period, spectraResponse)
      

def schedClusterEnd( someFunction, currentTime, period):
  """schedule the end of a cluster

  Args:
    None
  
  Returns:
    processID from sched.schedule()
  
  Raises:
    None
  """
  return mainSched.schedule(
    reportCluster,
    #someFunction(), # needs another parameter, but that binds the value
    currentTime,
    0,
    period)


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

  global waterLevel
  global rawWave
  global rawWave2
  global dominantPeriod
  global sampleTimeSeries
  global spectraTimeSeries

  global longWaterLevelAve
  global longWaterLevelStats
  global longWaterLevelHourlyHighLow
  global longWaterLevelDailyHighLow
  global longWaterLevelWeeklyHighLow
  global longWaterLevelMonthlyHighLow
  global longWaterLevels
  global longWaterLevelHiLoTicks
  global waterLevelChangeRate1Minutes
  global waterLevelChangeRate5Minutes
  global waterLevelChangeRate15Minutes
  global medWaterLevelAve
  global waveHeightHourlyHighLow
  global waveHeightDailyHighLow
  global waveHeightWeeklyHighLow
  global waveHeightMonthlyHighLow
  global waveHeightLowPass
  global waveHeightStats
  global waveHeightAve

  global wavePowerStats
  global wavePowerStats2
  global waveCluster


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
  influx.init("waterlevel")

  # initialize data structures
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

  findWave = findwave.FindWave() # determine wave peaks and periods
  dominantPeriod = dominant.Dominant() # determine dominant Period and response

  instantWaveHeight = 0
  rawWave = wave.Wave( currentTick) # wave height time series
                                          # (not sure this is used...)
  longWaterLevels = []
  rawWave2 = wave.Wave( currentTick) # filtered wave height time series
  findWave2 = findwave.FindWave() # determine need wave peaks
  longWaterLevelAve = average.Average( "Averaged Water Level", "in",
                                       config.LONG_AVE_SAMPLES)
  longWaterLevelStats =  stats2.Stats2( "Average Water Level", "in", 20)

  longWaterLevelHourlyHighLow = highlow.HighLow( "Water Level Limits", "in")
  longWaterLevelDailyHighLow = highlow.HighLow( "Water Level Limits", "in")
  longWaterLevelWeeklyHighLow = highlow.HighLow( "Water Level Limits", "in")
  longWaterLevelMonthlyHighLow = highlow.HighLow( "Water Level Limits", "in")
  waterLevelChangeRate1Minutes = []
  waterLevelChangeRate5Minutes = []
  waterLevelChangeRate15Minutes = []
  medWaterLevelAve = average.Average( "Wave Baseline Water Level", "in",
                                      config.MEDIUM_AVE_SAMPLES)
  waveHeightAve = average.Average( "Average Wave Height", "in", 20)
  waveHeightHourlyHighLow = highlow.HighLow( "Wave Height Limits", "in")
  waveHeightDailyHighLow = highlow.HighLow( "Wave Height Limits", "in")
  waveHeightWeeklyHighLow = highlow.HighLow( "Wave Height Limits", "in")
  waveHeightMonthlyHighLow = highlow.HighLow( "Wave Height Limits", "in")
  waveHeightLowPass = lowpass.LowPass( 4) # number of wave cycles
    #lowpass = 2 eliminates 80% of waves, = 4 eliminates 94% in a light chop
    # 4 reduces sampling to 4/30 or 1 every 120 ms, that is still 8/sec
  waveHeightTrap = trap.Trap( 4, -1, "in", 30,
                              name="Wave Height",
                              port=outChan)
  waveHeightStats = stats2.Stats2( "Wave Height", "in", 20)

  wavePowerStats = stats2.Stats2( "Wave Power", "nw?", 20)
  wavePowerStats2 = stats2.Stats2( "Wave Power Stats22", "nw?", 20)
 
  waveCluster = cluster.Cluster( "Wave Clusters",
                                 outChan,
                                 config.CLUSTER_MULTIPLIER )
  clusterTaskID = None
  
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
  #                    EVERY_MINUTE, 0) # s/b longer
  mainSched.schedule( doFFTs, currentTick, EVERY_200_MSEC, 0)

  mainSched.schedule( longWaterLevelHourlyReport, currentTick, EVERY_HOUR, 0)
  mainSched.schedule( longWaterLevelDailyReport, currentTick, EVERY_DAY, 0)
  mainSched.schedule( longWaterLevelWeeklyReport, currentTick, EVERY_WEEK, 0)
  mainSched.schedule( longWaterLevelMonthlyReport, currentTick, EVERY_MONTH, 0)

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
    '''
    influx.sendMeasurementLevel( currentTick,
                                 "waterLevel",
                                 "waterLevel",
                                 currentLevel)
    '''

    longWaterLevelAve.update( currentLevel)
    waveBaseLine = medWaterLevelAve.update( currentLevel)
    '''
    influx.sendMeasurementLevel( currentTick,
                                 "waterLevel",
                                 "waveBaseLine",
                                 waveBaseLine)
    '''

    instantWaveHeight = currentLevel - waveBaseLine
    '''
    influx.sendMeasurementLevel( currentTick,
                                 "waterLevel",
                                 "waveHeight",
                                 instantWaveHeight)
    '''

    instantWaveHeightAve = waveHeightAve.update( instantWaveHeight)
    '''
    influx.sendMeasurementLevel( currentTick,
                                 "waterLevel",
                                 "aveWaveHeight",
                                 instantWaveHeightAve)
    '''
    waveHeightAve2 = waveHeightLowPass.append( instantWaveHeight)
    waveHeightStats.append( instantWaveHeight)
    # this really doesn't do what you want:
    #   since this is instantaneous, the mean should be = 0.
    #   This makes the coefficientOfVariation get really big, since it is
    #   StdDev/mean.

    if findWave.findWave( currentTick, instantWaveHeight):
      peak = findWave.wavePeakToPeak
      period = findWave.wavePeriod
      power = findWave.wavePower
      rawWave.analyze( currentTick, peak, period, power, outChan) # what is this doing?

      wavePowerStats.append( power)
      # want to reset dominant wave period here

    if findWave2.findWave( currentTick, waveHeightAve2):
      peak = findWave2.wavePeakToPeak
      period = findWave2.wavePeriod
      power = findWave2.wavePower
      '''
      #if wave is also coherent  ... or is the coherent test only for clusters
      if dominantPeriod.firstPeriod == dominantPeriod.secondPeriod ==
          dominantPeriod.thirdPeriod:
        save power as part of the cluster
      else:
        save power as part of the background waves
      '''
      influx.sendMeasurementLevel( currentTick, "wave", "peak", peak)
      influx.sendMeasurementLevel( currentTick, "wave", "period", period)
      influx.sendMeasurementLevel( currentTick, "wave", "power", power)
      dominantPeriod.reset()

      waveHeightHourlyHighLow.append( peak)
      waveHeightDailyHighLow.append( peak)
      waveHeightWeeklyHighLow.append( peak)
      waveHeightMonthlyHighLow.append( peak)

      if waveCluster.isACluster( currentTick, peak, period, power): 
        if clusterTaskID is not None:
          unschedClusterEnd( clusterTaskID) # so it can be updated
          clusterTaskID = None
        else:
          waveCluster.reset( currentTick) # so it starts clean
        waveCluster.update( currentTick, peak, period, power)
        clusterTaskID = schedClusterEnd( reportCluster, currentTick,
                config.CLUSTER_WINDOW)


    # resample raw wave for spectral analysis
    sampleTimeSeries.evaluate ( currentTick, instantWaveHeight,
                                lastTick, lastWaveHeight)

    # do the timed jobs that are due
    mainSched.execute(currentTick)

  print "longWaterLevelAve", longWaterLevelAve
  print
  print "waveHeightAve",  waveHeightAve
  print
  print "waveHeightHourlyHighLow", waveHeightHourlyHighLow
  print "waveHeightDailyHighLow", waveHeightDailyHighLow
  print "waveHeightWeeklyHighLow", waveHeightWeeklyHighLow
  print "waveHeightMonthlyHighLow", waveHeightMonthlyHighLow
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
