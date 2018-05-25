#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
#pylint: disable=too-many-lines
"""
water-level a module for measuring water levels

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


BUGS:

1 differentiate between instantaneous wave height or
sea wave height and the peak value of a wave. Doing stats on the instantaneous
value has limited value, because the mean should be zero as it has the DC
component subtracted from it.

2 Code is in a mixed state. It has some experimental code and some older code.
Clean it up.

3 Partial conversion to InfluxDB and Grafana show their benefits. Now need to limit
the use of Series as the program eventually consumes all RAM...
How to avoid lists in Python?

6 add plotting of statistics stuff...anything that uses a Stats object or Average object
cluster.py:    self.powerAverage = average.A<type 'type'>: type object 'Resamples' has no attribute 'resamples'
kirk@onyx:~/dev/water-level$ grep waveLengthSamples *py
verage( "Wave Power Average", "nW?", 500)
//main.py:  longWaterLevelAve = average.Average( "Averaged Water Level", "in",
//main.py:  medWaterLevelAve = average.Average( "Wave Baseline Water Level", "in",
main.py:  waveHeightAve = average.Average( "Average Wave Height", "in", 20)
main.py:  longWaterLevelStats =  stats.Stats( "Average Water Level", "in", 20)
main.py:  waveHeightStats = stats.Stats( "Wave Height", "in", 20)
main.py:  wavePowerStats = stats.Stats( "Wave Power", "nw?", 20)
wave.py:    self.peaks = stats.Stats( "Wave Peaks", "in", 3*30) # 3 seconds
wave.py:    self.periods = stats.Stats( "Wave Periods", "s", 3*30) # 3 seconds
wave.py:    self.powers = stats.Stats( "Wave Powers", "nw/ft?", 3*30) # 3 seconds
are the last three redundant?

7 add High/low registers, plotting and candlestick plots
  add hilo for water level hourly daily, weekly
  wavePeakHighs ... wavePowerHighs   hourly, daily, weekly
  wakePeakHighs ... wakePowerHighs   hourly, daily, weekly

8 watches can be greatly simplified, they should just check against a threshold with
amount of hysteresis.

* shorten SendMeasurementLevel so that it fits on one line ALL the time

// change append to update when not appending to a list
//HighLow
//Average
//Stats
cluster.py:    #self.events.append ( { 'time': self.clusterTick,
level.py:    self.times.append( tick)
level.py:    self.levels.append( level)
//lowpass.py:  def append( self, value):
//lowpass.py:    self.members.append(value)
//lowpass.py:      lp = self.append( test)
main.py:  longWaterLevels.append( longAve)
main.py:  openFileHandles.append( inChan)
main.py:  openFileHandles.append( outChan)
main.py:    waveHeightAve2 = waveHeightLowPass.append( instantWaveHeight)
resamples.py:    #  resamples.append( Resample( config, tick, value))
resamples.py:      self.levels.append( value)
resamples.py:      self.levels.append( interpolate( self.resamplingDueTick, tick, value,
sched.py:    self.tasks.append ( {
sched.py:            self.tasks.append ( {
series.py:  def append( self, value):
series.py:      value: (float) value to be appended to time series
series.py:    self.values.append( value)
series.py:      self.append(test)
spectra.py:    self.times.append( currentTime)
spectra.py:      #print "size of sampleBuffer after first append ", len( sampleBuffer)
spectra.py:          #print "size of sampleBuffer after subsequent append ",
spectra.py:      #print "size of sampleBuffer after appends ", len( sampleBuffer)
spectra.py:      # append response to time series
spectra.py:      self.responses.append( abs(fft[ frequencyOfInterestIndex]))
spectra.py:    samples.resamples.append(
spectra.py:    specs.spectra.append ( Spectrum( samples.resamples))
spectra.py:    samples.resamples.append( resamples.Resample( period, tick, value))
spectra.py:    specs.spectra.append ( Spectrum( samples.resamples[-1]))
//trap.py:  def append( self, value):
//trap.py:      self.append( test)
//trap.py:      self.append( test)
//watch.py:    rates.append( RateTrigger ( "level rate " + str(i),
//wave.py:    self.times.append(tick)
//wave.py:    self.peaks.append(peak)
//wave.py:    self.periods.append(period)
//wave.py:    self.powers.append(power)


* Not all of the Stats variables declared are being used
// waveHeightTrap is not being updated

BUG

"""
#### IMPORTS ####

import sys
import datetime
import math

import average
import cluster
import dominant
import findwave
import highlow
import influx
import inputchan
import lowpass
import mysched
import report
import resamples
import stats
import trap
from config import BOAT_LENGTHS
from config import GRAVITY_CONSTANT
from config import CLUSTER_WINDOW
from config import TARGET_PERIODS
from config import SEND_START_RESPONSES
from config import LONG_AVE_SAMPLES
from config import MEDIUM_AVE_SAMPLES
from config import CLUSTER_MULTIPLIER
from config import SEND_RAW_MEASUREMENTS
from config import SEND_RAW_WAVES
from config import INFLUXDB_DATABASE

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
currentTick = None
mainSched = mysched.Schedule()
ifx = None # influxdb channel

dominantPeriod = None
waveLengthSamples = None
periodSamples = None

longWaterLevel = None
longWaterLevelAve = None
longWaterLevelStats = None
longWaterLevels = []
levelHourlyHighLow = None
levelDailyHighLow = None
levelWeeklyHighLow = None
levelMonthlyHighLow = None
medWaterLevelAve = None
waveHeightLowPass = None
waveHeightHourlyHighLow = None
waveHeightDailyHighLow = None
waveHeightWeeklyHighLow = None
waveHeightMonthlyHighLow = None
waveHeightAve = None
waveHeightStats = None
wavePowerStats = None
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


def reportCluster( tick):
  """report on the wave clusters in the past CLUSTER_WINDOW
  This is a scheduled routine, so limited arguments.

  Args:
    tick: (float)(s) Epoch of the end of the cluster
  
  Returns:
    None
  
  Raises:
    None
  """

  # the following doesn't look quite right...
  print "DEBUG clusterReport marking the end of a cluster"
  ifx.sendPoint( tick, "cluster", "energy", waveCluster.energy)
  ifx.sendPoint( tick, "cluster", "distance", waveCluster.distance)
  ifx.sendPoint( tick, "cluster", "period", waveCluster.maxPeriod+0)
  waveCluster.prReport( tick)
  waveCluster.reset( tick)


def updateLongWaterLevel( tick):
  """update the long water level time series (once a minute)
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """
  #pylint: disable=global-statement
  global longWaterLevels
  global longWaterLevelAve
  global levelHourlyHighLow
  global levelDailyHighLow
  global levelWeeklyHighLow
  global levelMonthlyHighLow
  #pylint: enable=global-statement

  longAve = longWaterLevelAve.average
  print "{0:%Y-%m-%dT%H:%M:%S.%f-0400 updateLongWaterLevels {1}}"\
          .format( datetime.datetime.fromtimestamp(tick),
                   ifx.influxWrites)
  ifx.reset()
  longWaterLevels.append( longAve)
  levelHourlyHighLow.update( longAve)
  levelDailyHighLow.update( longAve)
  levelWeeklyHighLow.update( longAve)
  levelMonthlyHighLow.update( longAve)

  # calculate the water level change rates
  lenLevels = len( longWaterLevels)
  if lenLevels > 1+1:
    levelChange1Min = ( longAve - longWaterLevels[-(1+1)]) * 60
  else:
    levelChange1Min = 0

  if lenLevels > 1+5:
    levelChange5Min = ( longAve - longWaterLevels[-(1+5)]) * 12
  else:
    levelChange5Min = 0

  # trim list
  if lenLevels > 10:
    longWaterLevels = longWaterLevels[-5:]

  # send long term water levels to InfluxDB for graphing
  ifx.sendPoint( tick, "waterLevel", "longAve", longAve)
  ifx.sendPoint( tick, "waterLevel", "changeRate1Minute",
                 levelChange1Min)
  ifx.sendPoint( tick, "waterLevel", "changeRate5Minute",
                 levelChange5Min)


def hourlyReport( tick):
  """report on the variables being collected
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """
  outChan.prReport( tick, "Hourly wave height ave " + waveHeightAve)
  outChan.prReport( tick, "Hourly wave height high " +
                    waveHeightHourlyHighLow.high)
  outChan.prReport( tick, "Hourly wave height high " +
                    waveHeightHourlyHighLow.low)


def levelHourlyReport( tick):
  """report on the long term water level in the last hour
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  outChan.prReport( tick, "Hourly water Level " + longWaterLevel)
  outChan.prReport( tick, "Hourly water Level " + levelHourlyHighLow.high)
  outChan.prReport( tick, "Hourly water Level " + levelHourlyHighLow.low)
  levelHourlyHighLow.report( tick, outChan)
  levelHourlyHighLow.reset()


def levelDailyReport( currentTime):
  """report on the long term water level in the last day
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  levelDailyHighLow.report( currentTime, outChan)
  levelDailyHighLow.reset()


def levelWeeklyReport( currentTime):
  """report on the long term water level in the last week
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """
  if datetime.datetime.fromtimestamp(currentTick).weekday == 0:
    levelWeeklyHighLow.report( currentTime, outChan)
    levelWeeklyHighLow.reset()


def levelMonthlyReport( currentTime):
  """report on the long term water level in the past month
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  if datetime.datetime.fromtimestamp(currentTick).day == 1:
    levelMonthlyHighLow.report( currentTime, outChan)
    levelMonthlyHighLow.reset()


def doFFTs( currentTime):
  """do an FFT on each of the resampled data streams
  This is a scheduled routine, so limited arguments.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  waveLengthSamples.fft()
  periodSamples.fft()

  #sendAllFftSamples( currentTime)
  sendLimitedFftSamples( currentTime)

  waveLengthSamples.freshen()
  periodSamples.freshen()


def sendAllFftSamples( tick):
  """send FFT samples to the InfluxDB server

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  for sample in waveLengthSamples.resamples:
    if sample.response is not None:
      ifx.sendTaggedPoint( tick, "spectrum",
                           "waveLength", sample.waveLength,
                           "waveResponse", sample.response)
      if SEND_START_RESPONSES:
        ifx.sendTaggedPoint( tick - sample.cyclePeriod, "spectrum",
                             "waveLength", sample.waveLength, 
                             "startBoatResponse", sample.response)

  for sample in periodSamples.resamples:
    if sample.response is not None:
      ifx.sendTaggedPoint( tick, "spectrum", "period",
                           sample.period, "periodResponse", sample.response)
      if SEND_START_RESPONSES:
        ifx.sendTaggedPoint( tick - sample.cyclePeriod, "spectrum",
                             "period", sample.period,
                             "startPeriodResponse", sample.response)




def sendLimitedFftSamples(tick):
  """send limited FFT samples to the InfluxDB server

  Note: this is using a postfix time and not a prefix time

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  waveLengthResponse = 0
  waveLength = 0
  periodResponse = 0
  period = 0

  # find the dominant response by wavelength
  for sample in waveLengthSamples.resamples:
    if sample.response is not None:
      if sample.response > waveLengthResponse:
        waveLengthResponse = sample.response
      waveLength = sample.waveLength

  # find the dominant response by period
  for sample in periodSamples.resamples:
    if sample.response is not None:
      if sample.response > periodResponse:
        periodResponse = sample.response
      period = sample.cyclePeriod

  ifx.sendTaggedPoint( tick, "spectrum", "waveLength", waveLength,
                       "waveLengthResponse", waveLengthResponse)
  ifx.sendTaggedPoint( tick, "spectrum", "period", period,
                       "periodicResponse", periodResponse)
  dominantPeriod.update( period, waveLength)


def schedClusterEnd( currentTime, period):
  """schedule the end of a cluster function

  Args:
    None

  Returns:
    processID from mysched.schedule()

  Raises:
    None
  """
  return mainSched.schedule( reportCluster,
                             currentTime,
                             0,
                             period)


def unschedClusterEnd( taskID):
  """unschedule the end of a cluster function

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  mainSched.unschedule( taskID)


#### MAIN ####

#pylint: disable=too-many-locals
#pylint: disable=too-many-statements
#pylint: disable=global-statement
def main():
  """Initialize various data structures and orchestrate the measurement
  and recording activities.

  Args:
    None

  Returns:
    None

  Raises:
    None
  """

  global outChan
  global currentTick
  global ifx

  global dominantPeriod
  global waveLengthSamples
  global periodSamples

  global longWaterLevelAve
  global longWaterLevelStats
  global levelHourlyHighLow
  global levelDailyHighLow
  global levelWeeklyHighLow
  global levelMonthlyHighLow
  global longWaterLevels
  global medWaterLevelAve
  global waveHeightHourlyHighLow
  global waveHeightDailyHighLow
  global waveHeightWeeklyHighLow
  global waveHeightMonthlyHighLow
  global waveHeightLowPass
  global waveHeightStats
  global waveHeightAve

  global wavePowerStats
  global waveCluster


  # initialze the input and output streams
  inputFileName, outputFileBaseName = processCommandLineArguments()

  inChan = inputchan.InputChannel( inputFileName)
  if not inChan.success:
    print errorMessage
    sys.exit(1)
  openFileHandles = []
  openFileHandles.append( inChan)

  outChan = report.ReportChannel( outputFileBaseName)
  #outChan = report.ReportChannel( "")
  openFileHandles.append( outChan)
  ifx = influx.Influx(INFLUXDB_DATABASE)

  setupGracefulExit( openFileHandles)


  ## MAIN initialize data structures

  currentTick, currentLevel = inChan.getWaterLevel( currentTick)

  findWave = findwave.FindWave() # determine wave peaks and periods
  dominantPeriod = dominant.Dominant() # determine dominant Period and response

  instantWaveHeight = 0
  longWaterLevels = []
  longWaterLevelAve = average.Average( "Averaged Water Level", "in",
                                       LONG_AVE_SAMPLES)
  longWaterLevelStats =  stats.Stats( "Average Water Level", "in", 20)

  levelHourlyHighLow = highlow.HighLow( "Water Level Limits", "in")
  levelDailyHighLow = highlow.HighLow( "Water Level Limits", "in")
  levelWeeklyHighLow = highlow.HighLow( "Water Level Limits", "in")
  levelMonthlyHighLow = highlow.HighLow( "Water Level Limits", "in")
  medWaterLevelAve = average.Average( "Wave Baseline Water Level", "in",
                                      MEDIUM_AVE_SAMPLES)
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
  waveHeightStats = stats.Stats( "Wave Height", "in", 20)
  wavePowerStats = stats.Stats( "Wave Power", "nw/ft?", 20)
  waveCluster = cluster.Cluster( "Wave Clusters", outChan, CLUSTER_MULTIPLIER)
  clusterTaskID = None

  waveLengthSamples = resamples.Resamples()
  for waveLength in BOAT_LENGTHS:
    waveSpeed = math.sqrt (GRAVITY_CONSTANT * waveLength / 2 /math.pi)
        # ft/s
    cyclePeriod = waveLength / waveSpeed # s

    #pylint: disable=E1305
    print "Wave length {0:n} has period {1:.2f} and speed {2:.2f}".format(
      waveLength,
      cyclePeriod,
      waveSpeed)
    #pylint: enable=E1305

    waveLengthSamples.resamples.append(
      resamples.Resample( cyclePeriod, currentTick, instantWaveHeight))
    waveLengthSamples.resamples[-1].waveLength = waveLength # sort of a cheat...

  periodSamples = resamples.Resamples()
  for period in TARGET_PERIODS:
    periodSamples.resamples.append(
      resamples.Resample( period, currentTick, instantWaveHeight))


  ## MAIN schedule periodic tasks

  mainSched.schedule( updateLongWaterLevel, currentTick, EVERY_MINUTE, 0)
  mainSched.schedule( doFFTs, currentTick, EVERY_200_MSEC, 0)

  mainSched.schedule( hourlyReport, currentTick, EVERY_HOUR, 0)
  mainSched.schedule( levelHourlyReport, currentTick, EVERY_HOUR, 0)
  mainSched.schedule( levelDailyReport, currentTick, EVERY_DAY, 0)
  mainSched.schedule( levelWeeklyReport, currentTick, EVERY_WEEK, 0)
  mainSched.schedule( levelMonthlyReport, currentTick, EVERY_MONTH, 0)

  print "Initialization done"


  ###MAIN LOOP

  #for _ in range (0, 3*60*60*30): #200000000): # limited test run
  while True: # until stopped...
    lastTick = currentTick
    lastWaveHeight = instantWaveHeight
    currentTick, currentLevel = inChan.getWaterLevel( currentTick)
    #currentTick, currentLevel = inChan.readLevel( currentTick)
    if SEND_RAW_MEASUREMENTS:
      ifx.sendPoint( currentTick, "waterLevel", "waterLevel", currentLevel)

    longWaterLevelAve.update( currentLevel)
    waveBaseLine = medWaterLevelAve.update( currentLevel)
    if SEND_RAW_MEASUREMENTS:
      ifx.sendPoint( currentTick, "waterLevel",
                     "waveBaseLine", waveBaseLine)

    instantWaveHeight = currentLevel - waveBaseLine
    if SEND_RAW_WAVES:
      ifx.sendPoint( currentTick, "waterLevel",
                     "waveHeight", instantWaveHeight)

    instantWaveHeightAve = waveHeightAve.update( instantWaveHeight)
    if SEND_RAW_MEASUREMENTS:
      ifx.sendPoint( currentTick, "waterLevel",
                     "aveWaveHeight", instantWaveHeightAve)
    waveHeightTrap.update( currentTick, instantWaveHeight)
    waveHeightStats.update( instantWaveHeight)
    # this really doesn't do what you want:
    #   since this is instantaneous, the mean should be = 0.
    #   This makes the coefficientOfVariation get really big, since it is
    #   StdDev/mean.

    waveHeightAve2 = waveHeightLowPass.update( instantWaveHeight)
    if findWave.findWave( currentTick, waveHeightAve2):
      peak = findWave.wavePeakToPeak
      period = findWave.wavePeriod
      power = findWave.wavePower
      #pylint: disable=pointless-string-statement
      '''
      #if wave is also coherent  ... or is the coherent test only for clusters
      if dominantPeriod.firstPeriod == dominantPeriod.secondPeriod ==
          dominantPeriod.thirdPeriod:
        save power as part of the cluster
      else:
        save power as part of the background waves
      '''
      #pylint: enable=pointless-string-statement
      ifx.sendPoint( currentTick, "wave", "peak", peak)
      ifx.sendPoint( currentTick, "wave", "period", period)
      ifx.sendPoint( currentTick, "wave", "power", power)
      dominantPeriod.reset()

      waveHeightHourlyHighLow.update( peak)
      waveHeightDailyHighLow.update( peak)
      waveHeightWeeklyHighLow.update( peak)
      waveHeightMonthlyHighLow.update( peak)

      wavePowerStats.update( power)

      if waveCluster.isACluster( currentTick, peak, period, power): 
        ifx.sendPoint( currentTick, "cluster",
                       "threshold", waveCluster.threshold)
        if clusterTaskID is not None:
          unschedClusterEnd( clusterTaskID) # so it can be updated
          clusterTaskID = None
        else:
          waveCluster.reset( currentTick) # so it starts clean
        waveCluster.update( currentTick, peak, period, power) 
        clusterTaskID = schedClusterEnd( currentTick, CLUSTER_WINDOW)


    # resample raw wave for spectral analysis
    waveLengthSamples.evaluate ( currentTick, instantWaveHeight,
                                 lastTick, lastWaveHeight)
    periodSamples.evaluate ( currentTick, instantWaveHeight,
                             lastTick, lastWaveHeight)

# do the timed jobs that are due
    mainSched.execute(currentTick)

  #pylint: enable=too-many-statements
  #pylint: enable=global-statement
  #pylint: enable=too-many-locals

if __name__ == "__main__":
  # execute only if run as a script
  main()

#pylint: enable=too-many-lines
