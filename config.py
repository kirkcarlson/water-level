#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
config Module to hold and manage configurable parameters

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
import math


#### CONSTANTS ####

DEBUG = True # enable debug statements

FILE_GENERATION = 0 # measurements are played from a recorded file
LIVE_GENERATION = 1 # measurements are from real sensors
RANDOM_GENERATION = 2 # measurements are randomly generated
GENERATION = RANDOM_GENERATION # type of generation: file, random, real

MAX_LIST = 10 # maximum number of list items for pretty printing

# constants for random data generation
BASE_AIR_PRESSURE = 99600
SWING_AIR_PRESSURE = 100
BASE_WATER_COLUMN_PRESSURE = 110000
SWING_WATER_COLUMN_PRESSURE = 1000

PA_TO_INCH = 248.84 # Pa/inchH20 at 60?F
WATER_COLUMN_OFFSET = 12 # inches, resistance of tubing and height correction


SAMPLES_PER_SECOND = 30
NUMBER_OF_FFT_SAMPLES = 2**6 # should be a power of two
NUMBER_OF_FFT2_SAMPLES = 2**8 # should be a power of two
                       #  5 for   64 for   1.0 seconds
                       #  6 for   64 for   2.1 seconds
                       #  7 for  128 for   4.2 seconds
                       #  8 for  256 for   8.5 seconds
                       #  9 for  512 for  17   seconds
                       # 10 for 1028 for  34   seconds
## exploring the idea of doing overlapping FFTs... say 4sec window every .5
## second and a 17 second window every 2 seconds
## need to know if it reveals anything interesting
# look abut the same, but the freqs are about the same also and expect
# there to be lower freqs with longer periods
MINIMUM_NUMBER_OF_CYCLES = 3 # number of cycle periods in an FFT sample

DESIRED_PERIOD = 1./SAMPLES_PER_SECOND #second for measurement stream


# FFTtargetPeriods are the high level sample periods
#                  1    2    3    4    5    6    7    8    9   10   11   12
BOAT_LENGTHS =  [  6,   8,  10,  12,  14,  16,  18,  20,  22,  24,  26,  28,
                   30, 32,  34,  36,  38,  40]
TARGET_PERIODS =   [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8,\
                    3.0, 3.4, 3.6, 3.8, 4.0, 4.4, 4.8, 5.2, 5.6, 6.0, 6.4,\
                    6.8, 7.2, 7.6, 8.0, 8.8, 9.6, 10.4, 11.2, 12.0, 12.8,\
                    13.6, 14.4, 15.2, 16.0, 17.6, 19.2]

WAKE_START = 0
WAKE_END = len( BOAT_LENGTHS) -1
WAVE_START = WAKE_END + 1
WAVE_END = WAKE_END + len( TARGET_PERIODS)


SHORT_AVE_SAMPLES = 5
MEDIUM_AVE_SAMPLES = 4 * SAMPLES_PER_SECOND
LONG_AVE_SAMPLES = 1 * 60 * SAMPLES_PER_SECOND
PEAK_AVE_SAMPLES = 10
PERIOD_AVE_SAMPLES = 10
WAVE_HEIGHT_AVE_SAMPLES = 10

# sample: 2016-05-16 19:33:11.104, 99395, 110671
CSV_FORMAT = "{year:d}-{month:d}-{day:d} {hour:d}:{minute:d}:{second:f}, " +\
    "{airPressure:d}, {waterColumnPressure:d}\n"
# sample: 2016.05.16_19.33.11.104, 99395, 110671
#CSV_FORMAT = "{year:d}.{month:d}.{day:d}_{hour:d}.{minute:d}.{second:f},
#    {airPressure:d}, {waterColumnPressure:d}\n"
##CSV_FORMAT = "{date:S} {time:S}, {airPressure:S}, {waterColumnPressure:S}\n"


# raw wave print formats
RWFORMAT = "Raw Wave {0:<15} {1:6.2f} in {2:6.2f} s bal: {3:6.2f} {3:6.2f} uW"
RWCSVFORMAT = "{{ event: raw wave  tick:{0:.3f}, peak:{0:.2f}, period:{0:.2f},\
               power:{0:.3f} }}"




# debug message verbosity
VERB_IMPORTANT = 0
VERB_COMMON =    1
VERB_UNCOMMON =  2
VERB_RARELY =    3
VERB_DEBUG =     4
selectedVerbosity = VERB_DEBUG

PLOT_SUMMARY = 1
PLOT_MODE = PLOT_SUMMARY

PEAK_THRESHOLD = .25 # inches
WAVE_PERIOD_THRESHOLD = .3 # seconds
WAVE_PERIOD_CUTOFF = 3 # seconds

PEAK_THRESHOLD = 0. # inches
WAVE_PERIOD_THRESHOLD = 0 # seconds
WAVE_PERIOD_CUTOFF = 100 # seconds

#cluster configuration
CLUSTER_WINDOW = 5 # sec
CLUSTER_MULTIPLIER = 5 # anomalous trigger for start of cluster
MAX_DISTANCE_LIMIT = 5000 # feet

# constants for power conversion
# The power energy of a wave (kW/m) = (ro * g * g / 64 / math.pi) * H * H * Te
# where
#   ro is the density of water (999.97 kg/m/m/m)
#     (999.0 might be more reasonable 15c)
#   g is the gravitational constant (6.67385 * 10**-11 m m m/kg/s/s)
#   H is the wave height in meters (using inches instead of meters)
#   Te is the wave period in seconds
#     watts divide by 10**11
#     nanowatts divide by 10**2
#     .0254 m/in
#
# The power energy of a wave (kW/m) = POWER_CONSTANT * H * H * Te
POWER_CONSTANT = 999 * 6.67385 * 6.67385 / 16 / math.pi / 100 *.0254 * .0254
GRAVITY_CONSTANT =  32.174 # ft/s/s

# plot configuration
# LENGTH_COLORS define the colors for scatter plot colors of boats
#         boat length, color character
LENGTH_COLORS = [ (16, "r"),
                  (20, "m"),
                  (24, "c"),
                  (28, "b"),
                  (32, "g"),
                  (36,"k") ]
# ENERGY_SIZES define the size of scatter plot circles based on energy
# thresholds
#             energy, size
ENERGY_SIZES = [ (10, 32),
                 (15, 64),
                 (20, 128),
                 (25, 256),
                 (30, 384),
                 (35, 512) ]

# resample configuration
RESOLUTION = 7 # number of bits resolution for frequency samples
               # 4=>6% 5=>3% 6=>2% 7->1%
CLOSEST_METHOD = 1
INTERPOLATION_METHOD = 2
NORMALIZATION_METHOD = INTERPOLATION_METHOD 

# spectra configuration
MINIMUM_NUMBER_OF_CYCLES = 3 # minimum number of cycle periods in an FFT sample
BUFFER_SIZE =  2**10 # or about 30 seconds at 30 samples/second
'''
Notes

had:
BUFFER_SIZE =  2**10 # or about 30 seconds at 30 samples/second
MINIMUM_NUMBER_OF_CYCLES = 3

seemed a bit insensitive, so trying:
BUFFER_SIZE =  2**8 # or about 8.5 seconds at 30 samples/second
MINIMUM_NUMBER_OF_CYCLES = 1

this was very slow, changing back for now

this may even speed it up a tad, even though also trying to do these at
0.2 seconds instead of 1.0 seconds.
'''

# watch configuration
NEUTRAL = 0
RISING = 1
FALLING = 2
TREND = { NEUTRAL: "Neutral", RISING: "Rising" , FALLING: "Falling" }
