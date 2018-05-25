#!/usr/bin/python
# vim: set fileencoding=utf-8
# coding=utf8
"""
influx -- a module for communicating with an Influx Database

This module has functions to open a path to an InfluxDB and functions
to send data points to that database.
"""

#### IMPORTS ####
import datetime

from influxdb import InfluxDBClient
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_POLICY_NAME
from config import INFLUXDB_POLICY



#### CLASSES ####

# pylint: disable=too-many-arguments
class Influx ( object):
  """Communication with an InfluxDB."""

  def __init__( self, databaseName):
    """initialize communication with an InfluxDB
  
    Args:
      databaseName: name of the database within the particular server
  
    Returns:
      None
  
    Raises:
      None
    """

    # initialize influxdb channel
    self.client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT)
    if databaseName not in self.client.get_list_database():
      self.client.create_database( databaseName)
      self.client.create_retention_policy(INFLUXDB_POLICY_NAME, INFLUXDB_POLICY, 1,
                                          database=databaseName)
    self.client.switch_database( databaseName)
    self.influxWrites = 0


  def sendPoint( self, currentTick, measurement, fieldType, value):
    """send a measurement to an influxdb
  
    Args:
      currentTick: (s) epoch of time associated with measurement
      measurment: name of the measurement within the database
      fieldType: name of the field within the measurement
      value: value of the field
  
    Returns:
      None
  
    Raises:
      None
    """
    self.influxWrites = self.influxWrites + 1
    self.client.write_points (
      [ {
        "measurement" : measurement,
        #"time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
        "time": "{0:%Y-%m-%dT%H:%M:%S.%f-0400}".format(
          datetime.datetime.fromtimestamp(currentTick)),
        "fields" : {
          fieldType : value+0.
        }
      } ]
    )


  def sendTaggedPoint( self, currentTick, measurement, tagType, tag, fieldType, value):
    """send a tagged point to the influxDB
  
    Args:
      currentTick: (s) epoch of time associated with measurement
      measurment: name of the measurement within the database
      tagType: name of the type of tag used within the measurment
      tag: specific value for the tag
      fieldType: name of the field within the measurement
      value: value of the field
  
    Returns:
      None
  
    Raises:
      None
    """
    self.influxWrites = self.influxWrites + 1
    self.client.write_points (
      [ {
        "measurement" : measurement,
        "tags" : {
          tagType : tag
        },
        #"time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
        "time": "{0:%Y-%m-%dT%H:%M:%S.%f-0400}".format(
          datetime.datetime.fromtimestamp(currentTick)),
        "fields" : {
          fieldType : value+0.
        }
      } ]
    )


  def reset( self):
    """reset the influx write counter
  
    Args:
      None
  
    Returns:
      None
  
    Raises:
      None
    """
    self.influxWrites = 0
# pylint: enable=too-many-arguments
